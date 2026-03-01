"""backend/services/interest_selection.py

Purpose
-------
Centralize user-interest *selection* algorithms used by semantic expansion.

This module provides a simple environment-variable switch between:
  - "top_k"  : deterministic K-matching (legacy behavior)
  - "hybrid" : deterministic core + sampled tail (recommended in Issue #98)

Env vars
--------
SE_INTEREST_SELECTION_ALGO
    "top_k" (default) or "hybrid".

SE_HYBRID_CORE_N
    How many of the strongest interests are always included (default: 2).

SE_HYBRID_POOL_SIZE
    How far into the ranked list we sample from for the tail (default: 10).
    The pool always starts *after* the core.

SE_HYBRID_DETERMINISTIC
    "1" to make sampling deterministic per (user_id, seed, kind), by seeding
    the RNG with a stable hash. Default: "1".

Notes
-----
This module is intentionally lightweight and dependency-free so it can be used
in hot paths.
"""
from __future__ import annotations

import hashlib
import os
import random
from typing import Dict, List, Tuple

from backend.services.logger import AppLogger

logger = AppLogger.get_logger(__name__)


# -----------------------
# Legacy Top-K (faithful extraction of your _select_top_k)
# -----------------------
def select_top_k(explicit: Dict[str, float], implicit: Dict[str, float], k_explicit: int, k_implicit: int) -> Tuple[List[str], List[str]]:
    """
    Independently select top-K explicit and top-K implicit interests.

    Returns:
      (top_explicit_keywords, top_implicit_keywords) — each list ordered by
      descending score (highest first). If there are fewer than K items, returns
      whatever is available.
    """
    explicit_sorted = sorted(explicit.items(), key=lambda kv: kv[1], reverse=True)
    implicit_sorted = sorted(implicit.items(), key=lambda kv: kv[1], reverse=True)

    top_explicit = [kw for kw, _ in explicit_sorted[:k_explicit]]
    top_implicit = [kw for kw, _ in implicit_sorted[:k_implicit]]

    logger.info("[Personalization] Top explicit (ordered): %s", top_explicit)
    logger.info("[Personalization] Top implicit (ordered): %s", top_implicit)

    return top_explicit, top_implicit


# -----------------------
# Hybrid: deterministic core + sampled tail
# -----------------------
def _stable_seed(user_id: str, seed: str, kind: str) -> int:
    raw = f"{user_id}\x1f{seed}\x1f{kind}".encode("utf-8", errors="ignore")
    digest = hashlib.sha256(raw).digest()
    return int.from_bytes(digest[:4], byteorder="big", signed=False)


def _hybrid_one(scores: Dict[str, float], k: int, core_n: int, pool_size: int, rng: random.Random) -> List[str]:
    if not scores or k <= 0:
        return []

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    k = min(k, len(ranked))

    core_n = max(0, min(core_n, k))
    pool_size = max(core_n, min(pool_size, len(ranked)))

    core = ranked[:core_n]
    tail_pool = ranked[core_n:pool_size]

    remaining = k - core_n
    if remaining <= 0 or not tail_pool:
        return [kw for kw, _ in core][:k]

    # Weighted sampling without replacement (iterative re-normalization)
    pool = list(tail_pool)
    picked: List[str] = []
    for _ in range(min(remaining, len(pool))):
        weights = [max(0.0, s) for _, s in pool]
        total = sum(weights)

        if total <= 0.0:
            choice = rng.choice(pool)
        else:
            r = rng.random() * total
            acc = 0.0
            choice = pool[-1]
            for (kw, s), w in zip(pool, weights):
                acc += w
                if acc >= r:
                    choice = (kw, s)
                    break

        picked.append(choice[0])
        pool.remove(choice)

    return [kw for kw, _ in core] + picked


def select_hybrid(explicit: Dict[str, float], implicit: Dict[str, float], k_explicit: int, k_implicit: int, user_id: str = "", seed: str = "") -> Tuple[List[str], List[str]]:
    core_n = int(os.getenv("SE_HYBRID_CORE_N", "2"))
    pool_size = int(os.getenv("SE_HYBRID_POOL_SIZE", "10"))
    deterministic = (os.getenv("SE_HYBRID_DETERMINISTIC", "1") or "1").strip() == "1"

    rng = random.Random(_stable_seed(user_id, seed, "hybrid")) if deterministic else random.Random()

    selected_explicit = _hybrid_one(explicit, k_explicit, core_n, pool_size, rng)
    selected_implicit = _hybrid_one(implicit, k_implicit, core_n, pool_size, rng)

    logger.info("[Personalization] Hybrid explicit: %s", selected_explicit)
    logger.info("[Personalization] Hybrid implicit: %s", selected_implicit)

    return selected_explicit, selected_implicit


# -----------------------
# Switcher (env-controlled)
# -----------------------
def select_interests(explicit: Dict[str, float], implicit: Dict[str, float], k_explicit: int, k_implicit: int, user_id: str = "", seed: str = "") -> Tuple[List[str], List[str]]:
    algo = (os.getenv("SE_INTEREST_SELECTION_ALGO", "top_k") or "top_k").strip().lower()

    # accept a few aliases
    if algo in {"k", "k_matching", "kmatching", "topk"}:
        algo = "top_k"

    if algo == "hybrid":
        return select_hybrid(explicit, implicit, k_explicit, k_implicit, user_id, seed)

    # default: legacy exact behavior
    return select_top_k(explicit, implicit, k_explicit, k_implicit)
