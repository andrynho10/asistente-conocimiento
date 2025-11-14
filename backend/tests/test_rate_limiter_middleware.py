"""
Unit tests for Rate Limiting Middleware.

Tests the token bucket algorithm and rate limiting enforcement.
AC#6: Rate Limiting Enforcement - 10 queries per 60 seconds per user.
"""

import pytest
import time
from app.middleware.rate_limiter import RateLimitStore, check_rate_limit


class TestRateLimitStore:
    """Test rate limit store using token bucket algorithm."""

    def test_initial_bucket_creation(self):
        """Test bucket is created with correct initial state."""
        store = RateLimitStore()
        allowed, remaining = store.get_bucket("test_key", capacity=10, refill_rate=10/60)

        assert allowed is True
        assert remaining == 9.0  # Started with 10, used 1

    def test_token_consumption(self):
        """Test tokens are consumed correctly."""
        store = RateLimitStore()

        # Consume all 10 tokens
        for i in range(10):
            allowed, _ = store.get_bucket("test_key", capacity=10, refill_rate=0)
            assert allowed is True

        # 11th request should be denied
        allowed, _ = store.get_bucket("test_key", capacity=10, refill_rate=0)
        assert allowed is False

    def test_token_refill(self):
        """Test tokens refill over time."""
        store = RateLimitStore()

        # Consume all tokens
        for i in range(10):
            store.get_bucket("test_key", capacity=10, refill_rate=0)

        # Wait a bit and refill at 1 token per second
        time.sleep(0.1)
        allowed, remaining = store.get_bucket("test_key", capacity=10, refill_rate=1.0)

        # Should have ~1 more token available (plus the one we consume)
        assert remaining > 0

    def test_capacity_limit(self):
        """Test bucket cannot exceed capacity."""
        store = RateLimitStore()

        # Consume nothing, wait for refill
        time.sleep(0.2)
        allowed, remaining = store.get_bucket("test_key", capacity=10, refill_rate=100.0)

        # Should not exceed 9 (capacity - consumed token)
        assert remaining <= 9.0

    def test_multiple_keys(self):
        """Test different keys have independent limits."""
        store = RateLimitStore()

        # Consume tokens for key1
        for i in range(10):
            store.get_bucket("key1", capacity=10, refill_rate=0)

        # key2 should still have tokens
        allowed, remaining = store.get_bucket("key2", capacity=10, refill_rate=0)
        assert allowed is True
        assert remaining == 9.0

    def test_cleanup_old_buckets(self):
        """Test old buckets are cleaned up."""
        store = RateLimitStore()

        # Create some buckets
        store.get_bucket("old_key", capacity=10, refill_rate=0)
        store.get_bucket("new_key", capacity=10, refill_rate=0)

        # Manually set old_key's last_refill to past
        import time as time_module
        store._buckets["old_key"]["last_refill"] = time_module.time() - 4000

        # Cleanup with 1 hour threshold
        store.cleanup_old_buckets(max_age_seconds=3600)

        # old_key should be removed
        assert "old_key" not in store._buckets
        assert "new_key" in store._buckets

    def test_zero_refill_rate(self):
        """Test with zero refill rate (bucket doesn't refill)."""
        store = RateLimitStore()

        for i in range(5):
            allowed, _ = store.get_bucket("test", capacity=5, refill_rate=0)
            assert allowed is True

        # 6th should fail with no refill
        allowed, _ = store.get_bucket("test", capacity=5, refill_rate=0)
        assert allowed is False

        # Wait and try again (no refill at rate=0)
        time.sleep(0.1)
        allowed, _ = store.get_bucket("test", capacity=5, refill_rate=0)
        assert allowed is False


class TestCheckRateLimitFunction:
    """Test check_rate_limit helper function."""

    def test_check_rate_limit_allowed(self):
        """Test check_rate_limit returns True when allowed."""
        result = check_rate_limit("test_key", limit=10, window=60)
        assert result is True

    def test_check_rate_limit_denied_after_limit(self):
        """Test check_rate_limit denies after limit reached."""
        # Use distinct key to avoid interference
        key = f"test_{int(time.time() * 1000)}"

        # Consume limit
        for i in range(10):
            result = check_rate_limit(key, limit=10, window=60)
            assert result is True

        # Should be denied
        result = check_rate_limit(key, limit=10, window=60)
        assert result is False

    def test_check_rate_limit_custom_limits(self):
        """Test check_rate_limit with different limits."""
        key1 = f"limit5_{int(time.time() * 1000)}"
        key2 = f"limit20_{int(time.time() * 1000)}"

        # Key1 with limit=5
        for i in range(5):
            assert check_rate_limit(key1, limit=5, window=60) is True
        assert check_rate_limit(key1, limit=5, window=60) is False

        # Key2 with limit=20
        for i in range(20):
            assert check_rate_limit(key2, limit=20, window=60) is True
        assert check_rate_limit(key2, limit=20, window=60) is False


class TestRateLimitingAC6:
    """Test AC#6: Rate Limiting Enforcement (10 queries per 60s per user)."""

    def test_ac6_10_per_60_seconds(self):
        """AC#6: Enforce 10 queries per 60 seconds per user."""
        user_key = f"user:test_{int(time.time() * 1000)}"

        # Should allow 10 requests
        for i in range(10):
            result = check_rate_limit(user_key, limit=10, window=60)
            assert result is True, f"Request {i+1} should be allowed"

        # 11th request should be denied
        result = check_rate_limit(user_key, limit=10, window=60)
        assert result is False, "11th request should be denied (rate limit exceeded)"

    def test_ac6_per_user_isolation(self):
        """AC#6: Rate limits are per-user, not global."""
        user1_key = f"user:user1_{int(time.time() * 1000)}"
        user2_key = f"user:user2_{int(time.time() * 1000)}"

        # User1 uses 5 requests
        for i in range(5):
            assert check_rate_limit(user1_key, limit=10, window=60) is True

        # User2 should still have all 10 available
        for i in range(10):
            result = check_rate_limit(user2_key, limit=10, window=60)
            assert result is True, f"User2 request {i+1} should be allowed"

        # User2's 11th should fail, User1's 6th should succeed
        assert check_rate_limit(user2_key, limit=10, window=60) is False
        assert check_rate_limit(user1_key, limit=10, window=60) is True

    def test_ac6_window_reset(self):
        """AC#6: Rate limit window resets after time period."""
        import threading

        user_key = f"user:window_test_{int(time.time() * 1000)}"

        # Consume 10 tokens in 1-second window
        for i in range(10):
            check_rate_limit(user_key, limit=10, window=1)

        # Should be rate limited now
        assert check_rate_limit(user_key, limit=10, window=1) is False

        # Wait for window to reset (with some tolerance for timing)
        time.sleep(1.2)

        # Should allow requests again
        assert check_rate_limit(user_key, limit=10, window=1) is True
