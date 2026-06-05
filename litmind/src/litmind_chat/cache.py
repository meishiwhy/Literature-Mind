"""LRU 查询缓存"""

import time
from collections import OrderedDict
from typing import Any, Optional


class QueryCache:
    """LRU 缓存，基于 OrderedDict"""

    def __init__(self, max_size: int = 100, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()

    def _make_key(self, question: str) -> str:
        return question.lower().strip()

    def get(self, question: str) -> Optional[Any]:
        key = self._make_key(question)
        if key not in self._cache:
            return None
        value, timestamp = self._cache[key]
        if time.time() - timestamp > self.ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return value

    def put(self, question: str, value: Any) -> None:
        key = self._make_key(question)
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (value, time.time())
        if len(self._cache) > self.max_size:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        self._cache.clear()
