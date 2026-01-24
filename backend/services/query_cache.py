import os
import time
import logging
from typing import Optional, Dict, Tuple

CACHE_TTL_SECONDS = int(os.getenv("QUERY_CACHE_TTL", "3600"))  # default: 1 hour

logger = logging.getLogger(__name__)
if not logger.handlers:
    import sys

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


def _normalize_query(q: str) -> str:
    return " ".join((q or "").lower().split())


class QueryCache:
    """
    In-memory cache for semantic expansions.
    Cache keys are namespaced by user_id to prevent cross-account
    data leakage. Cache is cleared on logout.

    Why caching helps:
    - Avoids repeated LLM calls for common queries (major speedup).
    - Reduces cost and CPU load on Ollama.
    - Allows instant replays during debugging or UI reloads.
    """

    def __init__(self, ttl: int = CACHE_TTL_SECONDS):
        self.ttl = ttl
        self._store: Dict[str, Tuple[str, float]] = {}

    def _make_key(
            self,
            user_id: str,
            query: str,
            model: str,
            temp: float,
            semantic_mode: str,
            verbosity: str,
            profile_rev: int = 0,
    ) -> str:
        norm_query = _normalize_query(query)
        sem_mode = (semantic_mode or "clarify_only").lower()
        verb = (verbosity or "medium").lower()

        return (
            f"{user_id}:"
            f"{model}:"
            f"{temp:.3f}:"
            f"{sem_mode}:"
            f"{verb}:"
            f"rev{profile_rev}:"
            f"{norm_query}"
        )

    def clear(self) -> None:
        size = len(self._store)
        logger.info("[Cache] CleARED %d entries", size)
        self._store.clear()

    def get(
            self,
            user_id: str,
            query: str,
            model: str,
            temp: float,
            semantic_mode: str,
            verbosity: str,
            profile_rev: int = 0,
    ) -> Optional[str]:
        if not self.ttl:
            logger.info("[Cache] Disabled (TTL=0)")
            return None

        key = self._make_key(
            user_id, query, model, temp, semantic_mode, verbosity, profile_rev
        )

        item = self._store.get(key)
        if not item:
            logger.info("[Cache] MISS for key='%s'", key)
            return None

        value, ts = item
        age = time.time() - ts

        if age > self.ttl:
            logger.info(
                "[Cache] EXPIRED key='%s' (age=%.1fs > ttl=%ds)",
                key, age, self.ttl
            )
            self._store.pop(key, None)
            return None

        logger.info("[Cache] HIT key='%s' (age=%.1fs)", key, age)
        return value
    def set(
            self,
            user_id: str,
            query: str,
            model: str,
            temp: float,
            semantic_mode: str,
            verbosity: str,
            expanded: str,
            profile_rev: int = 0,
    ) -> None:
        if not self.ttl:
            logger.info("[Cache] Skipped write (TTL=0)")
            return

        self.key = self._make_key(user_id, query, model, temp, semantic_mode, verbosity, profile_rev)
        key = self.key

        self._store[key] = (expanded, time.time())
        logger.info("[Cache] STORED key='%s'", key)

def on_user_logout(user_id: str):
    logger.info("User '%s' logging out — clearing query cache", user_id)
    query_cache.clear()

query_cache = QueryCache()
