"""
Unit Tests for CacheService

Tests cache operations (get, set, invalidate), TTL expiration,
LRU eviction, and statistics tracking.

AC#2: Response caching tests
AC#3: Retrieval caching tests
"""

import pytest
import time
from app.services.cache_service import CacheService


class TestCacheServiceBasicOperations:
    """Test basic cache operations: set, get, invalidate."""

    def test_cache_set_and_get(self):
        """Test setting and retrieving values from cache."""
        cache = CacheService(max_size=10)
        key = "test_key"
        value = {"answer": "Test answer", "sources": []}
        ttl = 300

        cache.set(key, value, ttl)
        retrieved = cache.get(key)

        assert retrieved == value
        assert cache.hits == 1
        assert cache.misses == 0

    def test_cache_get_missing_key(self):
        """Test retrieving non-existent key returns None."""
        cache = CacheService(max_size=10)

        result = cache.get("nonexistent_key")

        assert result is None
        assert cache.misses == 1

    def test_cache_invalidate_single_key(self):
        """Test invalidating a single cache entry."""
        cache = CacheService(max_size=10)
        key = "test_key"
        cache.set(key, "value", 300)

        cache.invalidate(key)
        result = cache.get(key)

        assert result is None

    def test_cache_invalidate_all_keys(self):
        """Test clearing entire cache (invalidate with no key)."""
        cache = CacheService(max_size=10)
        cache.set("key1", "value1", 300)
        cache.set("key2", "value2", 300)

        cache.invalidate()  # Clear all
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert len(cache.cache) == 0


class TestCacheServiceTTL:
    """Test TTL (Time-To-Live) expiration logic."""

    def test_cache_ttl_expiration(self):
        """Test that expired entries return None and count as misses."""
        cache = CacheService(max_size=10)
        key = "expiring_key"
        value = "test_value"
        ttl = 1  # 1 second TTL

        cache.set(key, value, ttl)
        assert cache.get(key) == value  # Should hit immediately

        # Wait for expiration
        time.sleep(1.1)
        result = cache.get(key)

        assert result is None
        assert cache.misses >= 1  # At least one miss after expiration

    def test_cache_ttl_not_expired(self):
        """Test that non-expired entries are still accessible."""
        cache = CacheService(max_size=10)
        key = "persist_key"
        value = "test_value"
        ttl = 5  # 5 second TTL

        cache.set(key, value, ttl)
        time.sleep(0.5)  # Wait less than TTL
        result = cache.get(key)

        assert result == value
        assert cache.hits == 1


class TestCacheServiceLRUEviction:
    """Test LRU (Least Recently Used) eviction policy."""

    def test_lru_eviction_on_overflow(self):
        """Test that least-recently-used item is evicted when max_size exceeded."""
        cache = CacheService(max_size=3)

        # Fill cache to max_size
        cache.set("key1", "value1", 300)
        cache.set("key2", "value2", 300)
        cache.set("key3", "value3", 300)

        assert len(cache.cache) == 3
        assert cache.evictions == 0

        # Add one more item (should evict least-recently-used "key1")
        cache.set("key4", "value4", 300)

        assert len(cache.cache) == 3
        assert cache.evictions == 1
        assert cache.get("key1") is None  # key1 was evicted
        assert cache.get("key4") == "value4"  # key4 is present

    def test_lru_eviction_order(self):
        """Test that LRU correctly tracks access order."""
        cache = CacheService(max_size=3)

        cache.set("key1", "value1", 300)
        cache.set("key2", "value2", 300)
        cache.set("key3", "value3", 300)

        # Access key1 (makes it recently used)
        _ = cache.get("key1")

        # Add new item (should evict key2, not key1 which was just accessed)
        cache.set("key4", "value4", 300)

        assert cache.get("key1") == "value1"  # key1 still in cache
        assert cache.get("key2") is None  # key2 was evicted
        assert cache.get("key4") == "value4"

    def test_lru_eviction_with_duplicate_key(self):
        """Test that updating existing key doesn't trigger eviction."""
        cache = CacheService(max_size=2)

        cache.set("key1", "value1", 300)
        cache.set("key2", "value2", 300)
        assert cache.evictions == 0

        # Update key1 (should not evict, just update)
        cache.set("key1", "new_value1", 300)

        assert len(cache.cache) == 2
        assert cache.evictions == 0
        assert cache.get("key1") == "new_value1"


class TestCacheServiceStatistics:
    """Test cache statistics tracking."""

    def test_cache_stats_structure(self):
        """Test that stats() returns all required fields."""
        cache = CacheService(max_size=100)

        stats = cache.get_stats()

        assert "hits" in stats
        assert "misses" in stats
        assert "evictions" in stats
        assert "size" in stats
        assert "hit_rate" in stats
        assert "max_size" in stats

    def test_cache_hit_rate_calculation(self):
        """Test accurate hit rate calculation."""
        cache = CacheService(max_size=10)
        cache.set("key1", "value1", 300)

        # 1 hit
        cache.get("key1")
        # 1 miss
        cache.get("nonexistent")

        stats = cache.get_stats()
        # hit_rate = hits / (hits + misses) = 1 / 2 = 0.5
        assert stats["hit_rate"] == 0.5
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    def test_cache_hit_rate_zero_accesses(self):
        """Test hit rate when no accesses have occurred."""
        cache = CacheService(max_size=10)

        stats = cache.get_stats()

        assert stats["hit_rate"] == 0.0
        assert stats["total_accesses"] == 0

    def test_cache_eviction_tracking(self):
        """Test that eviction count is accurately tracked."""
        cache = CacheService(max_size=2)

        cache.set("key1", "value1", 300)
        cache.set("key2", "value2", 300)
        cache.set("key3", "value3", 300)  # Causes eviction
        cache.set("key4", "value4", 300)  # Causes eviction

        stats = cache.get_stats()
        assert stats["evictions"] == 2


class TestCacheServiceKeyGeneration:
    """Test cache key generation."""

    def test_key_generation_normalization(self):
        """Test that key generation normalizes input (lowercase, strip)."""
        key1 = CacheService.generate_cache_key("  HELLO WORLD  ")
        key2 = CacheService.generate_cache_key("hello world")
        key3 = CacheService.generate_cache_key("Hello World")

        assert key1 == key2 == key3

    def test_key_generation_deterministic(self):
        """Test that same input always generates same key."""
        query = "¿Cómo solicito vacaciones?"
        key1 = CacheService.generate_cache_key(query)
        key2 = CacheService.generate_cache_key(query)

        assert key1 == key2

    def test_key_generation_different_queries(self):
        """Test that different queries generate different keys."""
        key1 = CacheService.generate_cache_key("query1")
        key2 = CacheService.generate_cache_key("query2")

        assert key1 != key2

    def test_key_generation_sha256_length(self):
        """Test that generated keys are SHA256 hexdigests (64 chars)."""
        key = CacheService.generate_cache_key("test")

        assert len(key) == 64  # SHA256 hexdigest is 64 characters


class TestCacheServiceIntegration:
    """Integration tests with realistic scenarios."""

    def test_response_cache_scenario(self):
        """
        Test response cache scenario:
        - User submits query
        - Response cached
        - Same query within TTL returns cached response
        """
        cache = CacheService(max_size=100)  # Response cache

        query = "¿Cómo solicito vacaciones?"
        key = CacheService.generate_cache_key(query)
        response = {"answer": "Puedes solicitar vacaciones...", "sources": []}

        # First query (cache miss)
        cache.set(key, response, ttl_seconds=300)
        retrieved = cache.get(key)

        assert retrieved == response
        assert cache.hits == 1
        assert cache.misses == 0

        # Second identical query (cache hit)
        retrieved2 = cache.get(key)
        assert retrieved2 == response
        assert cache.hits == 2

    def test_retrieval_cache_scenario(self):
        """
        Test retrieval cache scenario:
        - User submits search query
        - Documents retrieved and cached
        - Same search within 10min TTL returns cached documents
        """
        cache = CacheService(max_size=100)  # Retrieval cache

        search_query = "vacaciones"
        key = CacheService.generate_cache_key(search_query)
        documents = [
            {"id": 1, "title": "Política de Vacaciones", "relevance_score": 0.95},
            {"id": 2, "title": "Calendario de Días Feriados", "relevance_score": 0.85}
        ]

        cache.set(key, documents, ttl_seconds=600)
        retrieved = cache.get(key)

        assert retrieved == documents
        assert len(retrieved) == 2

    def test_multiple_independent_caches(self):
        """Test that multiple cache instances operate independently."""
        response_cache = CacheService(max_size=100)
        retrieval_cache = CacheService(max_size=100)

        key = "shared_key"
        response_data = {"answer": "test"}
        retrieval_data = [{"doc": 1}]

        response_cache.set(key, response_data, 300)
        retrieval_cache.set(key, retrieval_data, 600)

        assert response_cache.get(key) == response_data
        assert retrieval_cache.get(key) == retrieval_data
        assert response_cache.get_stats()["size"] == 1
        assert retrieval_cache.get_stats()["size"] == 1
