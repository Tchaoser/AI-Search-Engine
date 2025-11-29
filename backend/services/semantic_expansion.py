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

SYSTEM_PROMPT_BASE = (
    "You expand short user queries into a single detailed search query. "
    "Keep it one line, clear, and specific (entities, synonyms/aliases in "
    "parentheses, dates/regions, helpful keywords). Return ONLY the expanded query."
)

# -----------------------
# Simple tokenizer
# -----------------------
_TOKEN_WORD_REGEX = re.compile(r"\w+")


def _simple_tokenize(text: str) -> List[str]:
    if not text:
        return []
    return [t.lower() for t in _TOKEN_WORD_REGEX.findall(text)]


# -----------------------
# Interest extraction
# -----------------------
def _extract_explicit(profile: dict) -> Dict[str, float]:
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
        w = max(0.0, min(1.0, w))
        key = str(kw).lower()
        out[key] = out.get(key, 0.0) + w

    return out


def _extract_implicit(profile: dict) -> Dict[str, float]:
    out: Dict[str, float] = {}
    raw = profile.get("implicit_interests") or {}

    if not isinstance(raw, dict):
        logger.debug("Profile implicit_interests not a dict; skipping implicit extraction.")
        return out

    for kw, val in raw.items():
        try:
            v = float(val)
        except Exception:
            v = 1.0
        key = str(kw).lower()
        out[key] = out.get(key, 0.0) + v

    return out


# -----------------------
# Top-K selection
# -----------------------
def _select_top_k(explicit: Dict[str, float], implicit: Dict[str, float]) -> Tuple[List[str], List[str]]:
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
    if not explicit and not implicit:
        return ""

    explicit_str = ", ".join(explicit) if explicit else "none"
    implicit_str = ", ".join(implicit) if implicit else "none"

    return f"User interests provided for context: Explicit = {explicit_str}; Implicit = {implicit_str}."


# -----------------------
# Main expansion entrypoint
# -----------------------
async def expand_query(seed: str, user_id: Optional[str] = None) -> str:
    seed = (seed or "").strip()
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
                snippet = _format_personalization_snippet(top_explicit, top_implicit)
                if snippet:
                    system_prompt = (
                        f"{SYSTEM_PROMPT_BASE} When expanding the query, consider "
                        f"the following user interest context (apply only when relevant): {snippet}"
                    )
                    logger.info("[Personalization] Applied for user_id=%s: %s", user_id, snippet)
            else:
                logger.info("No profile found for user_id=%s", user_id)
    except Exception as e:
        logger.exception("Error during personalization extraction/selection: %s", e)
        system_prompt = SYSTEM_PROMPT_BASE

    # 3) Prepare LLM payload and call
    expanded = seed
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
        expanded = " ".join(raw.split()) or seed
        logger.info("Expanded query for seed='%s' -> '%s'", seed, expanded)
    except Exception as e:
        logger.warning("Query expansion failed, using original seed='%s', error=%s", seed, e)
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
