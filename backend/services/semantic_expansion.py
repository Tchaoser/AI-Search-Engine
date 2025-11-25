# backend/services/semantic_expansion.py
import os
import sys
import httpx
import logging

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


def _get_personalization_context(user_id: str, max_items: int = 5):
    """
    Fetch top implicit + explicit interests; return short string describing them.
    """
    if not user_id:
        logger.debug(f"No user_id provided for personalization context")
        return ""

    profile = user_profiles_col.find_one({"user_id": user_id})
    if not profile:
        logger.debug(f"No profile found for user_id: {user_id}")
        return ""

    implicit = profile.get("implicit_interests", {}) or {}
    explicit_raw = profile.get("explicit_interests", []) or []
    explicit = [e["keyword"] for e in explicit_raw if "keyword" in e]

    # take top N implicit tokens
    top_implicit = list(implicit.keys())[:max_items]

    interests = explicit + top_implicit
    if not interests:
        logger.debug(f"No interests found for user_id: {user_id}")
        return ""

    # Log the interests found
    logger.info(f"Found interests for user {user_id}: explicit={explicit}, top_implicit={top_implicit}")

    # Example:
    # "User interests: photography, machine-learning, python, wildlife"
    return "User interests: " + ", ".join(interests)


async def expand_query(seed: str, user_id: str = None) -> str:
    seed = (seed or "").strip()
    if not seed:
        logger.warning("Empty seed query provided")
        return seed
    
    in_cache = query_cache.get(seed, OLLAMA_MODEL, OLLAMA_TEMP)
    if in_cache:
        # Cached expanded query returned
        print("Query is in cache")
        return in_cache
    else:
        print("Query not in cache")
    

    logger.info(f"Expanding query: '{seed}' for user_id: {user_id}")

    personalization = _get_personalization_context(user_id)

    # Log the personalization context that will be used
    if personalization:
        logger.info(f"Using personalization context: {personalization}")
    else:
        logger.info("No personalization context available")

    system_prompt = SYSTEM_PROMPT_BASE
    if personalization:
        system_prompt += f" Use these interests to bias expansions when relevant: {personalization}."

    # Log the full system prompt being sent (optional - might be verbose)
    logger.debug(f"System prompt: {system_prompt}")

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "options": {"temperature": OLLAMA_TEMP},
        "system": system_prompt,
        "prompt": seed,
    }

    try:
        logger.debug(f"Sending request to Ollama with model: {OLLAMA_MODEL}, temperature: {OLLAMA_TEMP}")

        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(f"{OLLAMA_URL.rstrip('/')}/api/generate", json=payload)

        r.raise_for_status()
        data = r.json()
        text = (data.get("response") or "").strip()
        expanded = " ".join(text.split()) or seed
    except Exception:
        # fail-safe so search remains functional need this because of shitty gpu
        expanded = seed

    #expanded query stored even if idential to seed
    query_cache.set(seed, OLLAMA_MODEL, OLLAMA_TEMP, expanded)

    return expanded
