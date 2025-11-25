# backend/services/semantic_expansion.py
import os
import sys
import httpx
import logging
import re

from typing import Dict, List, Tuple
from services.query_cache import query_cache  # singleton cache
from services.db import user_profiles_col    

# ---------------------------------------------------
# Logging Setup
# ---------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

logger.propagate = False

MAX_LOG_ITEMS = 10  #adjust as needed for logging

def _log_truncated_dict(label: str, data: dict, max_items: int = 10):
    """
    Logs only the first max_items of a dict to avoid giant logs.
    Shows how many items were omitted.
    """
    items = list(data.items())
    shown = dict(items[:max_items])

    if len(items) > max_items:
        logger.info(f"{label}: {shown} ... (+{len(items) - max_items} more)")
    else:
        logger.info(f"{label}: {shown}")


# ---------------------------------------------------
# Config
# ---------------------------------------------------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_TEMP = float(os.getenv("OLLAMA_TEMP", "0.4"))

SYSTEM_PROMPT_BASE = (
    "You expand short user queries into a single, more detailed search query. "
    "Keep it one line, human-readable, and include helpful specifics (entities, "
    "synonyms/aliases in parentheses, dates/regions/formats, intent keywords). "
    "Return ONLY the expanded query—no extra commentary."
)


# ---------------------------------------------------
# Simple tokenization
# ---------------------------------------------------

# Use a basic regex to identify "words" (letters/numbers/underscore)
_TOKEN_WORD_REGEX = re.compile(r"\w+")

#regex useful for extracting words
def _simple_tokenize(text: str) -> List[str]:
    """
    Tokenize text into lowercase words for lightweight overlap checks.

    This tokenizer intentionally avoids complexity (no NLP libraries).
    It is sufficient to detect whether a query and a user interest
    have meaningful word overlap.
    """
    if not text:
        return []
    return [token.lower() for token in _TOKEN_WORD_REGEX.findall(text)]


# ---------------------------------------------------
# Interest extraction helpers
# ---------------------------------------------------

def _get_explicit_interest_keywords(profile: dict) -> List[str]:
    """
    Extract explicit interests from the user profile.
    """
    explicit_raw = profile.get("explicit_interests", []) or []
    out: List[str] = []

    for item in explicit_raw:
        if isinstance(item, dict):
            keyword = item.get("keyword")
            if keyword:
                out.append(str(keyword))

    logger.info(f"[explicit] Extracted explicit interests: {out}")
    return out


def _get_implicit_interest_scores(profile: dict) -> Dict[str, float]:
    """
    Extract implicit interests as {keyword: numeric_score}.
    """
    raw = profile.get("implicit_interests", {}) or {}

    #must be a dict, makes sure it is
    if isinstance(raw, dict):
        out: Dict[str, float] = {}
        for key, value in raw.items():
            if isinstance(value, (int, float)):
                out[str(key)] = float(value)
            else:
                out[str(key)] = 1.0
        
        _log_truncated_dict("[implicit] Extracted implicit interests (with scores)", out, MAX_LOG_ITEMS)
        return out

    return {}


# Interest scoring
def _compute_interest_scores(profile: dict) -> Dict[str, float]:
    """
    Combine explicit + implicit interests into a unified scored dictionary.

    Scoring heuristics:
        - Explicit interests: +3.0 (strong manual signal)
        - Implicit interests: +1.0 base + stored numeric weight
        - Query history match: +0.5 for each time an interest appears
          in a previous query (simple relevance reinforcement)
    """
    scores: Dict[str, float] = {}

    # Explicit interests get strong weight
    for kw in _get_explicit_interest_keywords(profile):
        key = kw.lower()
        scores[key] = scores.get(key, 0.0) + 3.0

    # Implicit interests get smaller—but meaningful—weight
    for kw, implicit_score in _get_implicit_interest_scores(profile).items():
        key = kw.lower()
        scores[key] = scores.get(key, 0.0) + 1.0 + float(implicit_score)

    # Light reinforcement from query history
    history = profile.get("query_history", []) or []
    for entry in history:
        raw_text = entry.get("query") if isinstance(entry, dict) else str(entry)
        tokens = _simple_tokenize(raw_text)

        for kw in list(scores.keys()):
            if kw in tokens:
                scores[kw] += 0.5

    _log_truncated_dict(
        "[scores] Combined explicit + implicit + history-based interest scores",
        scores,
        MAX_LOG_ITEMS
    )
    return scores


# Interest relevance selection for current query
def _select_interests_for_query(
    seed_query: str,
    scored_interests: Dict[str, float],
    max_primary: int = 3,
    max_secondary: int = 3,
) -> Tuple[List[str], List[str]]:
    """
    Select which interests matter for this query.

    Returns:
        primary_interests   [] Top-scoring interests with token overlap to query
        secondary_interests [] Next best interests (high score, but no overlap)
    """
    if not scored_interests:
        return [], []

    seed_tokens = set(_simple_tokenize(seed_query))

    # Sort by descending score
    sorted_items = sorted(scored_interests.items(), key=lambda kv: kv[1], reverse=True)
    sorted_keywords = [kw for kw, _ in sorted_items]

    primary: List[str] = []
    secondary: List[str] = []

    # Primary = interests that share tokens with the query
    for kw, score in sorted_items:
        if len(primary) >= max_primary:
            break
        if seed_tokens.intersection(set(_simple_tokenize(kw))):
            primary.append(kw)

    # Secondary = top remaining interests
    for kw in sorted_keywords:
        if kw not in primary and len(secondary) < max_secondary:
            secondary.append(kw)

    # If nothing overlaps, everything goes to secondary
    if not primary:
        secondary = sorted_keywords[:max_secondary]

    logger.info(
    f"[select] For seed='{seed_query}', primary interests={primary}, "
    f"secondary interests={secondary}"
    )
    return primary, secondary


# Structured prompt generation
def _format_personalization_for_llm(
    primary_interests: List[str],
    secondary_interests: List[str],
) -> str:
    """
    Build a concise, structured personalization snippet for the LLM.

    Format example:
      "User primary interests: kubernetes, cloud; secondary interests: devops, linux."

    This structure is far more interpretable for LLMs than
    dumping raw comma-separated interests.
    """
    if not primary_interests and not secondary_interests:
        return ""

    parts: List[str] = []

    if primary_interests:
        parts.append("primary interests: " + ", ".join(primary_interests))
    if secondary_interests:
        parts.append("secondary interests: " + ", ".join(secondary_interests))

    return "User " + "; ".join(parts)


async def expand_query(seed: str, user_id: str = None) -> str:
    """
    Expand a short query using the LLM, with optional personalized biasing
    based on user interests (primary/secondary relevance ranking).
    """
    seed = (seed or "").strip()
    if not seed:
        logger.warning("Empty seed query provided")
        return seed

    # Query cache lookup
    cached = query_cache.get(seed, OLLAMA_MODEL, OLLAMA_TEMP)
    if cached:
        logger.info("Query is in cache")
        return cached
    else:
        logger.info("Query not in cache")

    logger.info(f"Expanding query: '{seed}' for user_id={user_id}")

    # Personalized interest relevance selection
    personalization_snippet = ""

    if user_id:
        profile = user_profiles_col.find_one({"user_id": user_id})
        if profile:
            # Compute interest scores
            scores = _compute_interest_scores(profile)

            # Select relevant interests for THIS query
            primary, secondary = _select_interests_for_query(seed, scores)

            # Turn them into a structured prompt snippet
            personalization_snippet = _format_personalization_for_llm(primary, secondary)

            logger.info(
                f"Personalization for user {user_id}: "
                f"primary={primary}, secondary={secondary}"
            )

    # Build system prompt
    system_prompt = SYSTEM_PROMPT_BASE

    if personalization_snippet:
        system_prompt += (
            " When expanding the query, gently bias toward these user preferences "
            "only if they are relevant: "
            f"{personalization_snippet}."
        )

    logger.debug(f"System prompt: {system_prompt}")

    # LLM request payload
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "options": {"temperature": OLLAMA_TEMP},
        "system": system_prompt,
        "prompt": seed,
    }

    # Call Ollama
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{OLLAMA_URL.rstrip('/')}/api/generate",
                json=payload,
            )

        response.raise_for_status()

        data = response.json()
        raw_text = (data.get("response") or "").strip()

        expanded = " ".join(raw_text.split()) or seed
        logger.info(f"Query enhanced: '{seed}' → '{expanded}'")

    except Exception as e:
        logger.error(f"Query expansion failed: {e}. Using original seed.")
        expanded = seed

    # Cache result
    query_cache.set(seed, OLLAMA_MODEL, OLLAMA_TEMP, expanded)

    return expanded