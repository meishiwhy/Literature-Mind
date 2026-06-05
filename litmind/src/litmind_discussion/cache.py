"""Simple dict-based cache for discussion results"""

from __future__ import annotations

import time
from threading import Lock
from typing import Any, Optional

from .config import CACHE_MAX_SIZE, CACHE_TTL_SECONDS


class DiscussionCache:
    def __init__(self, ttl: int = CACHE_TTL_SECONDS, max_size: int = CACHE_MAX_SIZE):
        self._ttl = ttl
        self._max_size = max_size
        self._cache: dict[str, tuple[float, Any]] = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None
            ts, val = self._cache[key]
            if time.time() - ts > self._ttl:
                del self._cache[key]
                return None
            return val

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._cache[key] = (time.time(), value)
            if len(self._cache) > self._max_size:
                oldest = min(self._cache.keys(), key=lambda k: self._cache[k][0])
                del self._cache[oldest]

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
