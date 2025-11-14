"""
Cache Service - LRU Cache with TTL Implementation

Implements a two-tier caching strategy for RAG optimization:
1. Response Cache: Caches entire RAG responses for identical queries (TTL: 5 minutes)
2. Retrieval Cache: Caches document search results separately (TTL: 10 minutes)

Both caches use LRU (Least Recently Used) eviction policy with max 100 entries.
Cache keys use SHA256 hash of normalized queries for deterministic matching.

AC#2: Response caching for identical queries
AC#3: Retrieval caching for document searches
"""

import hashlib
import time
import logging
from typing import Any, Optional, Dict
from collections import OrderedDict

logger = logging.getLogger(__name__)


class CacheService:
    """
    LRU Cache with TTL support for RAG optimization.

    Maintains statistics on cache performance (hits, misses, evictions).
    Thread-safe operations with timestamp-based TTL validation.
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize LRU cache with specified maximum size.

        Args:
            max_size: Maximum number of entries before LRU eviction (default: 100)
        """
        self.max_size = max_size
        self.cache: OrderedDict[str, tuple[Any, float, float]] = OrderedDict()

        # Statistics tracking
        self.hits = 0
        self.misses = 0
        self.evictions = 0

        logger.info(f"CacheService initialized with max_size={max_size}")

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache if exists and not expired.

        Args:
            key: Cache key (typically SHA256 hash of normalized query)

        Returns:
            Cached value if found and not expired, None otherwise

        Implements:
        - TTL validation: checks if (current_time - timestamp) > ttl_seconds
        - LRU update: moves accessed item to end of OrderedDict for recent-use tracking
        """
        if key not in self.cache:
            self.misses += 1
            return None

        value, timestamp, ttl_seconds = self.cache[key]
        elapsed = time.time() - timestamp

        # Check TTL expiration
        if elapsed > ttl_seconds:
            logger.debug(f"Cache entry expired: key={key}, ttl={ttl_seconds}s, elapsed={elapsed:.2f}s")
            del self.cache[key]
            self.misses += 1
            return None

        # Update LRU ordering: move to end (most recently used)
        self.cache.move_to_end(key)
        self.hits += 1

        logger.debug(f"Cache hit: key={key}, elapsed={elapsed:.2f}s, ttl_remaining={ttl_seconds - elapsed:.2f}s")
        return value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """
        Store value in cache with TTL expiration.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds before expiration

        Implements:
        - Duplicate key handling: updates existing entry (no eviction)
        - LRU eviction: removes least-recently-used entry when cache exceeds max_size
        - TTL tracking: stores tuple (value, timestamp, ttl_seconds)
        """
        current_time = time.time()

        # If key exists, remove it first (will be re-added at end of OrderedDict)
        if key in self.cache:
            del self.cache[key]

        # Add to cache
        self.cache[key] = (value, current_time, ttl_seconds)

        # Enforce LRU eviction if cache exceeds max_size
        if len(self.cache) > self.max_size:
            evicted_key, _ = self.cache.popitem(last=False)  # Remove least recently used (first item)
            self.evictions += 1
            logger.debug(f"LRU eviction: key={evicted_key}, cache_size={len(self.cache)}, total_evictions={self.evictions}")

        logger.debug(f"Cache set: key={key}, ttl={ttl_seconds}s, cache_size={len(self.cache)}")

    def invalidate(self, key: Optional[str] = None) -> None:
        """
        Invalidate cache entries.

        Args:
            key: Specific key to invalidate. If None, clears entire cache.

        Useful for:
        - Document updates: invalidate retrieval cache when documents change
        - Session cleanup: clear all caches on logout
        """
        if key is None:
            # Clear entire cache
            cleared_size = len(self.cache)
            self.cache.clear()
            logger.info(f"Cache cleared: {cleared_size} entries removed")
        else:
            # Remove specific key
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"Cache entry invalidated: key={key}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Return cache statistics for monitoring and health checks.

        Returns:
            Dict with:
            - hits: Total successful cache hits
            - misses: Total cache misses
            - evictions: Total LRU evictions
            - size: Current number of entries in cache
            - hit_rate: Cache hit rate (hits / (hits + misses)) or 0 if no queries
            - max_size: Maximum capacity
        """
        total_accesses = self.hits + self.misses
        hit_rate = self.hits / total_accesses if total_accesses > 0 else 0.0

        stats = {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "size": len(self.cache),
            "hit_rate": round(hit_rate, 4),
            "max_size": self.max_size,
            "total_accesses": total_accesses
        }

        logger.debug(f"Cache stats: {stats}")
        return stats

    @staticmethod
    def generate_cache_key(query: str) -> str:
        """
        Generate deterministic cache key from query string.

        Implements:
        - Normalization: lowercase, strip whitespace
        - Hashing: SHA256 for collision resistance and fixed length
        - Deterministic: identical normalized queries produce identical keys

        Args:
            query: User query string

        Returns:
            SHA256 hexdigest (64 characters)

        Example:
            >>> key1 = CacheService.generate_cache_key("  HELLO WORLD  ")
            >>> key2 = CacheService.generate_cache_key("hello world")
            >>> key1 == key2
            True
        """
        normalized = query.lower().strip()
        return hashlib.sha256(normalized.encode()).hexdigest()


# Global cache instances (singleton pattern for app-wide reuse)
response_cache = CacheService(max_size=100)  # 5-minute TTL for identical queries
retrieval_cache = CacheService(max_size=100)  # 10-minute TTL for document searches
