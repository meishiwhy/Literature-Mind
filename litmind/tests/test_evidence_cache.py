"""Tests for QueryCache"""

import time
import pytest
from litmind_evidence.cache import QueryCache


class TestQueryCache:
    def setup_method(self):
        self.cache = QueryCache(ttl=60, max_size=10)

    def test_set_get(self):
        self.cache.set("test query", {"result": 42})
        assert self.cache.get("test query") == {"result": 42}

    def test_case_insensitive_key(self):
        self.cache.set("Test Query", "value")
        assert self.cache.get("test query") == "value"

    def test_cache_miss(self):
        assert self.cache.get("nonexistent") is None

    def test_invalidate(self):
        self.cache.set("test", "value")
        self.cache.invalidate("test")
        assert self.cache.get("test") is None

    def test_clear(self):
        self.cache.set("a", 1)
        self.cache.set("b", 2)
        self.cache.clear()
        assert self.cache.get("a") is None
        assert self.cache.get("b") is None

    def test_ttl_expiry(self):
        cache = QueryCache(ttl=0)  # 0 TTL = immediate expiry
        cache.set("test", "value")
        time.sleep(0.01)
        assert cache.get("test") is None

    def test_max_size_eviction(self):
        cache = QueryCache(ttl=60, max_size=2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)  # should evict 'a'
        assert cache.get("a") is None
        assert cache.get("c") == 3
