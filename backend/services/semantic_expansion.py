# backend/services/semantic_expansion.py
import os
import httpx
import logging
from services.db import user_profiles_col

import sys

# Configure logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create handler if none exists
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

# Set up logger
logger = logging.getLogger(__name__)

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
        response_data = r.json()
        text = (response_data.get("response") or "").strip()
        expanded_query = " ".join(text.split()) or seed

        # Log the enhancement result
        if expanded_query != seed:
            logger.info(f"Query enhanced: '{seed}' -> '{expanded_query}'")
        else:
            logger.info(f"Query unchanged: '{seed}'")

        return expanded_query

    except Exception as e:
        # Log the error and fallback
        logger.error(f"Error expanding query '{seed}': {str(e)}. Falling back to original query.")
        return seed