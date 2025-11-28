"""
backend/services/semantic_expansion.py

Purpose
-------
LLM-backed query expansion with optional personalization.

Overview
--------
This module expands short user queries using an LLM (via Ollama) and can
optionally bias expansions using a user's explicit and implicit interests.

Design principles for this variant
 - Keep explicit and implicit interests independent (no scaling/transforms).
 - Select top-K explicit interests (ranked by the DB weight, which is 0..1).
 - Select top-K implicit interests (ranked by the DB numeric score).
 - Provide both lists directly to the LLM in a short, structured snippet.
 - Keep behavior conservative: do not force personalization; let the model
   apply interests only when relevant.
 - Keep logging consistent and helpful for debugging.
 - If anything fails, fall back to returning the original seed query.
 - No history boosting or thresholds in this module.

Refactor notes (future TODO):
 - Consider moving prompt-building to its own class for easier testing.
 - Consider injecting `user_profiles_col` for easier unit testing/mocking.
 - Consider adding a small diagnostics mode (ENV flag) for verbose logs.
"""

from __future__ import annotations

import os
import sys
import logging
import re
from typing import Dict, List, Optional, Tuple

import httpx

from services.query_cache import query_cache
from services.db import user_profiles_col

# -----------------------
# Configuration
# -----------------------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_TEMP = float(os.getenv("OLLAMA_TEMP", "0.4"))

# How many explicit + implicit interests to expose to the LLM
TOP_K_EXPLICIT = int(os.getenv("SE_EXP_TOP_K_EXPLICIT", "5"))
TOP_K_IMPLICIT = int(os.getenv("SE_EXP_TOP_K_IMPLICIT", "5"))

SYSTEM_PROMPT_BASE = (
    "You expand short user queries into a single detailed search query. "
    "Keep it one line, clear, and specific (entities, synonyms/aliases in "
    "parentheses, dates/regions, helpful keywords). Return ONLY the expanded query."
)

# -----------------------
# Logging
# -----------------------
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False

# -----------------------
# Simple tokenizer (used only for normalization, not for matching logic)
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
    # sort descending by value
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
def _format_personalization_snippet(explicit: List[str], implicit: List[str]) -> str:
    """
    Build a short, structured personalization snippet to include in the system prompt.

    Example output:
      "User interests provided for context: Explicit = jobs, pokemon; Implicit = marvel, spiderman"

    The LLM should treat these as contextual signals and apply them only when relevant.
    """
    if not explicit and not implicit:
        return ""

    explicit_str = ", ".join(explicit) if explicit else "none"
    implicit_str = ", ".join(implicit) if implicit else "none"

    return f"User interests provided for context: Explicit = {explicit_str}; Implicit = {implicit_str}."


# -----------------------
# Main expansion entrypoint
# -----------------------
async def expand_query(seed: str, user_id: Optional[str] = None) -> str:
    """
    Expand the user's `seed` query using the configured LLM, optionally biasing
    the expansion using the user's profile interests.

    Steps:
      1. Return cached expansion (if present).
      2. If user_id provided and profile exists:
           - extract explicit + implicit interests (no transforms)
           - take top-K from each independently
           - create a short personalization snippet and attach it to the system prompt
      3. Call the LLM and return the expanded query (or the seed on failure).
      4. Cache the result.

    Returns:
      The expanded query string (single-line, whitespace-normalized).
    """
    seed = (seed or "").strip()
    if not seed:
        logger.warning("expand_query called with empty seed.")
        return seed

    # 1) Cache check
    cached = query_cache.get(seed, OLLAMA_MODEL, OLLAMA_TEMP)
    if cached:
        logger.info("[Semantic] Using cached expansion for seed='%s'", seed)
        return cached

    # 2) Build system prompt
    system_prompt = SYSTEM_PROMPT_BASE
    try:
        if user_id:
            profile = user_profiles_col.find_one({"user_id": user_id})
            if profile:
                explicit_map = _extract_explicit(profile)
                implicit_map = _extract_implicit(profile)

                top_explicit, top_implicit = _select_top_k(explicit_map, implicit_map)

                snippet = _format_personalization_snippet(top_explicit, top_implicit)
                if snippet:
                    # keep snippet concise and instructive
                    system_prompt = (
                        f"{SYSTEM_PROMPT_BASE} When expanding the query, consider "
                        f"the following user interest context (apply only when relevant): {snippet}"
                    )
                    logger.info("[Personalization] Applied for user_id=%s: %s", user_id, snippet)
            else:
                logger.info("No profile found for user_id=%s", user_id)
    except Exception as e:
        # never fail the whole expansion pipeline due to personalization errors
        logger.exception("Error during personalization extraction/selection: %s", e)
        system_prompt = SYSTEM_PROMPT_BASE

    # 3) Prepare LLM payload and call
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "options": {"temperature": OLLAMA_TEMP},
        "system": system_prompt,
        "prompt": seed,
    }

    expanded = seed
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{OLLAMA_URL.rstrip('/')}/api/generate", json=payload)
        resp.raise_for_status()
        data = resp.json()
        raw = (data.get("response") or "").strip()
        expanded = " ".join(raw.split()) or seed
        logger.info("Expanded prompt for seed='%s'", system_prompt)
        logger.info("Expanded query for seed='%s' -> '%s'", seed, expanded)
    except Exception as e:
        logger.exception("LLM expansion failed: %s. Falling back to seed.", e)
        expanded = seed

    # 4) Cache the result
    try:
        query_cache.set(seed, OLLAMA_MODEL, OLLAMA_TEMP, expanded)
    except Exception:
        logger.exception("Failed to write expansion result to cache.")

    return expanded
