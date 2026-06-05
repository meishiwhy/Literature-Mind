"""Evidence Finder 查询缓存"""

from __future__ import annotations

import time
from collections import OrderedDict
from threading import Lock
from typing import Any, Optional

from .config import CACHE_MAX_SIZE, CACHE_TTL_SECONDS


class QueryCache:
    """线程安全的 LRU 查询缓存"""

    def __init__(self, ttl: int = CACHE_TTL_SECONDS, max_size: int = CACHE_MAX_SIZE):
        self._ttl = ttl
        self._max_size = max_size
        self._cache: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = Lock()

    def _key(self, query: str) -> str:
        return query.lower().strip()

    def get(self, query: str) -> Optional[Any]:
        key = self._key(query)
        with self._lock:
            if key not in self._cache:
                return None
            timestamp, value = self._cache[key]
            if time.time() - timestamp > self._ttl:
                del self._cache[key]
                return None
            self._cache.move_to_end(key)
            return value

    def set(self, query: str, value: Any) -> None:
        key = self._key(query)
        with self._lock:
            self._cache[key] = (time.time(), value)
            self._cache.move_to_end(key)
            while len(self._cache) > self._max_size:
                self._cache.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def invalidate(self, query: str) -> None:
        key = self._key(query)
        with self._lock:
            self._cache.pop(key, None)
