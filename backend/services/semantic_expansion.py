"""
backend/services/semantic_expansion.py

Purpose
-------
LLM-backed query expansion with optional personalization.

Overview
--------
This module expands short user queries using an LLM (via Ollama) and can
optionally bias expansions using a user's explicit and implicit interests.

Design principles
-----------------
- Keep explicit and implicit interests independent (no scaling/transforms)
- Select top-K explicit interests (ranked by the DB weight, which is 0..1)
- Select top-K implicit interests (ranked by the DB numeric score)
- Provide both lists directly to the LLM in a short, structured snippet
- Keep behavior conservative: do not force personalization
- Keep logging consistent and helpful for debugging
- Fall back to returning the original seed query if anything fails
"""

from __future__ import annotations
import os
import re
from typing import Dict, List, Optional, Tuple

import httpx
import unicodedata

from services.query_cache import query_cache
from services.db import user_profiles_col
from services.logger import AppLogger

logger = AppLogger.get_logger(__name__)

# -----------------------
# Configuration
# -----------------------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_TEMP = float(os.getenv("OLLAMA_TEMP", "0.4"))

TOP_K_EXPLICIT = int(os.getenv("SE_EXP_TOP_K_EXPLICIT", "5"))
TOP_K_IMPLICIT = int(os.getenv("SE_EXP_TOP_K_IMPLICIT", "5"))

# Max allowed length for the personalization snippet (user interest context)
MAX_SNIPPET_CHARS = int(os.getenv("SE_MAX_SNIPPET_CHARS", "600"))
# Max allowed length for the full system prompt sent to the LLM
MAX_SYSTEM_PROMPT_CHARS = int(os.getenv("SE_MAX_SYSTEM_PROMPT_CHARS", "1200"))
# Max allowed length for the user prompt (raw seed query)
MAX_USER_PROMPT_CHARS = int(os.getenv("SE_MAX_USER_PROMPT_CHARS", "600"))

# NOTE/TODO:
# User interests are provided as a soft bias signal only.
# The system prompt explicitly instructs the LLM not to infer or invent
# query topics based solely on interests, to reduce semantic drift.
# This is a prompt-level mitigation; LLMs can't completely ignore words given to them
# Stronger relevance gating may be added later at the application layer.
SYSTEM_PROMPT_BASE = (
    "Expand short user queries into a single detailed search query. "
    "Keep it one line, clear, and specific (entities, synonyms/aliases in parentheses, dates/regions, helpful keywords). "
    "Return ONLY the expanded query. "
    "Interpret the user's query first and preserve its original topic and intent. "
    "Do NOT infer or invent topics based solely on user interests. "
    "Treat user interests as a soft bias only: "
    "- Strong interests: may guide wording strongly, only if they clearly overlap the query topic. "
    "- Medium interests: background context; do not let them shift the main query focus. "
    "- Weak interests: generally ignore unless directly relevant to the query. ")

# -----------------------
# Normalize and Truncate
# -----------------------

def _normalize_single_line(text: str) -> str:
    """
    Collapse all whitespace (including newlines) to single spaces so prompts
    stay on one line. Also strips leading/trailing spaces.
    """
    if not text:
        return ""
    return " ".join(str(text).split())


def _truncate_text(text: str, max_len: int, context: str) -> str:
    """
    Truncate `text` to at most `max_len` characters, preserving readability. Simple truncation.
    - Prefer cutting at the last whitespace before the limit (if it's not too early).
    - Always return a single-line string.
    - Log the truncation event at INFO level.
    """
    if max_len <= 0:
        # Treat <=0 as a no limit choice to avoid surprising behavior
        return _normalize_single_line(text)

    original = _normalize_single_line(text)
    if len(original) <= max_len:
        return original

    truncated = original[:max_len]
    last_space = truncated.rfind(" ")

    # Avoid chopping to something tiny if the only spaces are very early
    if last_space > int(max_len * 0.6):
        truncated = truncated[:last_space]

    truncated = truncated.rstrip() + " ..."
    logger.info(
        "%s truncated to %d characters (original=%d).",
        context,
        len(truncated),
        len(original),
    )
    return truncated


# -----------------------
# Simple tokenizer
# -----------------------
_TOKEN_WORD_REGEX = re.compile(r"\w+")


def _simple_tokenize(text: str) -> List[str]:
    """
    Tokenize text into lowercase word tokens.

    This is intentionally lightweight — it's only used for normalization or
    lightweight overlap checks if needed in future changes.
    """
    if not text:
        return []
    return [t.lower() for t in _TOKEN_WORD_REGEX.findall(text)]


# -----------------------
# Interest strength labelling for explicit interests
# -----------------------
def _classify_explicit(explicit: Dict[str, float]) -> Dict[str, List[str]]:
    buckets = {"strong": [], "medium": [], "weak": []}
    for kw, w in explicit.items():
        if w >= 0.70:
            buckets["strong"].append(kw)
        elif w >= 0.40:
            buckets["medium"].append(kw)
        else:
            buckets["weak"].append(kw)
    return buckets


# -----------------------
# Interest strength labelling for implicit interests
# -----------------------
def _classify_implicit(implicit: Dict[str, float]) -> Dict[str, List[str]]:
    """
    Classify top-K implicit interests into strong/medium/weak using relative dominance.
    Heuristic:
      - Strong: top1 >= 1.5x top2 AND top1 >= 10
      - Medium: top1 >= 2x median(top5) or score >= 6
      - Weak: everything else
    """
    buckets = {"strong": [], "medium": [], "weak": []}
    if not implicit:
        return buckets

    sorted_items = sorted(implicit.items(), key=lambda kv: kv[1], reverse=True)
    top_scores = [v for _, v in sorted_items[:5]]  # consider top 5
    top1 = top_scores[0]
    top2 = top_scores[1] if len(top_scores) > 1 else 0
    median_top5 = sorted(top_scores)[len(top_scores) // 2]

    for kw, score in sorted_items:
        if 1.5 * top2 <= top1 == score and top1 >= 10:
            buckets["strong"].append(kw)
        elif score >= max(6, 2 * median_top5):
            buckets["medium"].append(kw)
        else:
            buckets["weak"].append(kw)

    return buckets


# -----------------------
# Verbosity filtering
# -----------------------
def _filter_tiers_by_verbosity(tiers: Dict[str, List[str]], verbosity: str) -> Dict[str, List[str]]:
    """
    Filters strong/medium/weak tiers based on verbosity:
      - off    → none
      - low    → strong only
      - medium → strong + medium
      - high   → all tiers
    """
    if verbosity == "off":
        return {"strong": [], "medium": [], "weak": []}
    if verbosity == "low":
        return {"strong": tiers.get("strong", []), "medium": [], "weak": []}
    if verbosity == "medium":
        return {
            "strong": tiers.get("strong", []),
            "medium": tiers.get("medium", []),
            "weak": [],
        }
    return tiers  # high


# -----------------------
# Interest extraction
# -----------------------
def _extract_explicit(profile: dict) -> Dict[str, float]:
    """
    Extract explicit interests from the user profile.

    The profile expects `explicit_interests` to be a list of objects:
      { "keyword": <str>, "weight": <float 0..1> }

    Returns:
      dict mapping lowercase keyword -> weight (0..1)
    """
    out: Dict[str, float] = {}
    raw = profile.get("explicit_interests") or []

    if not isinstance(raw, list):
        logger.debug("Profile explicit_interests not a list; skipping explicit extraction.")
        return out

    for item in raw:
        if not isinstance(item, dict):
            continue
        kw = item.get("keyword")
        w = item.get("weight")
        if not kw:
            continue
        try:
            w = float(w)
        except Exception:
            w = 1.0
        # clamp to [0, 1]
        w = max(0.0, min(1.0, w))
        key = str(kw).lower()
        # keep the raw weight (0..1) for ranking within explicit interests
        out[key] = out.get(key, 0.0) + w

    # logger.info("[Personalization] Extracted explicit interests (raw weights): %s", out)
    return out


def _extract_implicit(profile: dict) -> Dict[str, float]:
    """
    Extract implicit interests from the user profile.

    The profile expects `implicit_interests` to be a dict:
      { "<keyword>": <numeric_score>, ... }

    Returns:
      dict mapping lowercase keyword -> numeric_score (as stored)
    """
    out: Dict[str, float] = {}
    raw = profile.get("implicit_interests") or {}

    if not isinstance(raw, dict):
        logger.debug("Profile implicit_interests not a dict; skipping implicit extraction.")
        return out

    for kw, val in raw.items():
        try:
            v = float(val)
        except Exception:
            # fallback to a modest score if DB value is malformed
            v = 1.0
        key = str(kw).lower()
        out[key] = out.get(key, 0.0) + v

    # logger.info("[Personalization] Extracted implicit interests (raw scores): %s", out)
    return out


# -----------------------
# Top-K selection
# -----------------------
def _select_top_k(explicit: Dict[str, float], implicit: Dict[str, float]) -> Tuple[List[str], List[str]]:
    """
    Independently select top-K explicit and top-K implicit interests.

    Returns:
      (top_explicit_keywords, top_implicit_keywords) — each list ordered by
      descending score (highest first). If there are fewer than K items, returns
      whatever is available.
    """
    explicit_sorted = sorted(explicit.items(), key=lambda kv: kv[1], reverse=True)
    implicit_sorted = sorted(implicit.items(), key=lambda kv: kv[1], reverse=True)

    top_explicit = [kw for kw, _ in explicit_sorted[:TOP_K_EXPLICIT]]
    top_implicit = [kw for kw, _ in implicit_sorted[:TOP_K_IMPLICIT]]

    logger.info("[Personalization] Top explicit (ordered): %s", top_explicit)
    logger.info("[Personalization] Top implicit (ordered): %s", top_implicit)

    return top_explicit, top_implicit


# -----------------------
# Format personalization snippet
# -----------------------
def _format_personalization_snippet(explicit: Dict[str, List[str]], implicit: Dict[str, List[str]]) -> str:
    """
    Build a tiered personalization snippet. Explicit and implicit interests
    are passed as { "strong": [...], "medium": [...], "weak": [...] }.
    Weak signals are considered background only.
    """
    parts = []

    for tier in ["strong", "medium", "weak"]:
        if explicit.get(tier):
            parts.append(f"{tier.capitalize()} explicit interests: {', '.join(explicit[tier])}")
        if implicit.get(tier):
            parts.append(f"{tier.capitalize()} implicit interests: {', '.join(implicit[tier])}")

    if not parts:
        return ""

    snippet = "User interests provided for context: " + "; ".join(parts) + "."
    snippet = _normalize_single_line(snippet)

    if MAX_SNIPPET_CHARS > 0:
        snippet = _truncate_text(
            snippet,
            MAX_SNIPPET_CHARS,
            context="Personalization snippet",
        )
    return snippet


def _strip_wrapping_quotes(text: str) -> str:
    """
    Remove leading/trailing straight or curly quotes ONLY if the entire
    string is wrapped by them. Internal quotes are preserved.
    """
    if not text or len(text) < 2:
        return text

    pairs = [
        ('"', '"'),
        ('“', '”'),
        ('‘', '’'),
    ]

    for left, right in pairs:
        if text.startswith(left) and text.endswith(right):
            return text[1:-1].strip()

    return text


# -----------------------
# Main expansion entrypoint
# -----------------------
async def expand_query(
        seed: str,
        user_id: Optional[str] = None,
        verbosity: str = "medium",
) -> str:
    """
    Expand the user's `seed` query using the configured LLM, optionally biasing
    the expansion using the user's profile interests and verbosity level.

    Verbosity controls which interests are included in the personalization snippet:
      - off    → no interest-based personalization
      - low    → strong explicit interests only
      - medium → strong explicit + top implicit
      - high   → all explicit + all implicit

    Steps:
      1. Normalize and truncate seed query.
      2. Return cached expansion (if present).
      3. If user_id provided and profile exists:
           - extract explicit + implicit interests
           - take top-K lists
           - filter interests according to verbosity
           - create personalization snippet
      4. Build system prompt and call LLM
      5. Cache result and return

    Returns:
      Expanded query string (single-line, whitespace-normalized)
    """
    seed = (seed or "").strip()
    seed = _normalize_single_line(seed)

    # Enforce max length on user prompt BEFORE cache/personalization
    if 0 < MAX_USER_PROMPT_CHARS < len(seed):
        seed = _truncate_text(seed, MAX_USER_PROMPT_CHARS, context="User prompt")

    if not seed:
        logger.warning("expand_query called with empty seed.")
        return seed

    # 1) Cache check
    cached = query_cache.get(seed, OLLAMA_MODEL, OLLAMA_TEMP)
    if cached:
        logger.debug("Query expansion cache hit", extra={"original": seed, "expanded": cached})
        return cached
    else:
        logger.debug("Query expansion cache miss", extra={"original": seed})

    # 2) Build system prompt
    system_prompt = SYSTEM_PROMPT_BASE
    try:
        if user_id:
            profile = user_profiles_col.find_one({"user_id": user_id})
            if profile:
                explicit_map = _extract_explicit(profile)
                implicit_map = _extract_implicit(profile)

                top_explicit, top_implicit = _select_top_k(explicit_map, implicit_map)

                # Verbosity-based filtering
                verbosity = (verbosity or "medium").lower()
                if verbosity not in {"off", "low", "medium", "high"}:
                    verbosity = "medium"

                # classify tiers
                explicit_tiers = _classify_explicit(explicit_map)
                implicit_tiers = _classify_implicit(implicit_map)

                # filter tiers based on verbosity
                explicit_tiers = _filter_tiers_by_verbosity(explicit_tiers, verbosity)
                implicit_tiers = _filter_tiers_by_verbosity(implicit_tiers, verbosity)

                # build snippet
                snippet = _format_personalization_snippet(explicit_tiers, implicit_tiers)
                if snippet:
                    system_prompt = (
                        f"{SYSTEM_PROMPT_BASE} When expanding the query, consider "
                        f"the following user interest context (apply only when relevant): {snippet}"
                    )
                    logger.info(
                        "[Personalization] Applied for user_id=%s (verbosity=%s): %s",
                        user_id, verbosity, snippet
                    )
                logger.info(
                    "[Personalization] Full system prompt before truncation (len=%d): %s",
                    len(system_prompt),
                    system_prompt
                )
            else:
                logger.info("No profile found for user_id=%s", user_id)
    except Exception as e:
        logger.exception("Error during personalization extraction/selection: %s", e)
        system_prompt = SYSTEM_PROMPT_BASE

    # Normalize & truncate system prompt
    system_prompt = _normalize_single_line(system_prompt)

    if 0 < MAX_SYSTEM_PROMPT_CHARS < len(system_prompt):
        system_prompt = _truncate_text(system_prompt, MAX_SYSTEM_PROMPT_CHARS, context="System prompt")

    # 3) Prepare LLM payload and call
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "options": {"temperature": OLLAMA_TEMP},
        "system": system_prompt,
        "prompt": seed,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{OLLAMA_URL.rstrip('/')}/api/generate", json=payload)
        resp.raise_for_status()

        raw = (resp.json().get("response") or "").strip()

        # collapse whitespace first
        collapsed = " ".join(raw.split()) or seed

        # normalize to NFC for characters like é
        normalized = unicodedata.normalize("NFC", collapsed)

        # remove wrapping quotes if present
        stripped = _strip_wrapping_quotes(normalized)

        logger.info(
            "Expanded query for seed='%s' -> '%s' (repr=%s)",
            seed, stripped, repr(stripped)
        )

        expanded = stripped

    except Exception as e:
        logger.warning(
            "Query expansion failed, using original seed='%s', error=%s",
            seed, e
        )
        expanded = seed

    # 4) Cache result (even if identical to seed)
    try:
        query_cache.set(seed, OLLAMA_MODEL, OLLAMA_TEMP, expanded)
        logger.debug(
            "Query expansion complete",
            extra={"original": seed, "expanded": expanded, "same": seed == expanded},
        )
    except Exception:
        logger.exception("Failed to write expansion result to cache.")

    return expanded
