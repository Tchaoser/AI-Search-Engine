import os
import time
from typing import Optional, Dict, Tuple

#time to keep a cached expansion 
CACHE_TTL_SECONDS = int(os.getenv("QUERY_CACHE_TTL", "3600"))  # default: 1 hour

#this is a singleton class so it called in class file and then the declaration here is imported to other files
def _normalize_query(q: str) -> str:
    """
    Normalize user query for caching so it matches:
    - lowercase
    - collapse internal whitespace
    """
    return " ".join((q or "").lower().split())


class QueryCache:
    """
    in-memory cache for query expansions.
    """

    def __init__(self, ttl: int = CACHE_TTL_SECONDS):
        self.ttl = ttl
        # key is (value, timestamp) tuple
        self._store: Dict[str, Tuple[str, float]] = {}

    def _make_key(self, query: str, model: str, temp: float) -> str:
        norm = _normalize_query(query)
        return f"{model}:{temp:.3f}:{norm}"

    def get(self, query: str, model: str, temp: float) -> Optional[str]:
        if not self.ttl:
            return None  # caching disabled if ttl == 0

        key = self._make_key(query, model, temp)
        item = self._store.get(key)
        if not item:
            return None

        value, ts = item
        #expire entries older than TTL
        if time.time() - ts > self.ttl:
            self._store.pop(key, None)
            return None

        return value

    def set(self, query: str, model: str, temp: float, expanded: str) -> None:
        if not self.ttl:
            return  # caching disabled
        key = self._make_key(query, model, temp)
        self._store[key] = (expanded, time.time())


query_cache = QueryCache()
