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

    Why caching helps:
    - Avoids repeated LLM calls for common queries (major speedup).
    - Reduces cost and CPU load on Ollama.
    - Allows instant replays during debugging or UI reloads.
    """

    def __init__(self, ttl: int = CACHE_TTL_SECONDS):
        self.ttl = ttl
        self._store: Dict[str, Tuple[str, float]] = {}

    def _make_key(self, query: str, model: str, temp: float) -> str:
        norm = _normalize_query(query)
        return f"{model}:{temp:.3f}:{norm}"

    def get(self, query: str, model: str, temp: float) -> Optional[str]:
        if not self.ttl:
            logger.info("[Cache] Disabled (TTL=0)")
            return None

        key = self._make_key(query, model, temp)
        item = self._store.get(key)

        if not item:
            logger.info("[Cache] MISS for key='%s'", key)
            return None

        value, ts = item
        age = time.time() - ts
        if age > self.ttl:
            logger.info(
                "[Cache] EXPIRED entry for key='%s' (age=%.1fs > ttl=%ds), removing.",
                key, age, self.ttl
            )
            self._store.pop(key, None)
            return None

        logger.info("[Cache] HIT for key='%s' (age=%.1fs)", key, age)
        return value

    def set(self, query: str, model: str, temp: float, expanded: str) -> None:
        if not self.ttl:
            logger.info("[Cache] Skipped write (TTL=0)")
            return

        key = self._make_key(query, model, temp)
        self._store[key] = (expanded, time.time())
        logger.info("[Cache] STORED expansion for key='%s'", key)


query_cache = QueryCache()
