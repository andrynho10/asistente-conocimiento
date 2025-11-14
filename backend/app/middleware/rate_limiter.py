"""
Rate Limiting Middleware for API endpoints.

Implements token bucket algorithm for rate limiting with configurable limits per endpoint.
AC#6: Rate Limiting Enforcement - Enforces 10 queries per 60 seconds per user.

Usage:
    app.add_middleware(RateLimitMiddleware)
"""

import time
import logging
from typing import Dict, Tuple
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitStore:
    """
    In-memory rate limit store using token bucket algorithm.

    Thread-safe storage for rate limit buckets per user/endpoint combination.
    """

    def __init__(self):
        """Initialize rate limit storage."""
        # Format: {key: {"tokens": float, "last_refill": float}}
        self._buckets: Dict[str, Dict[str, float]] = {}
        self._lock = __import__('threading').Lock()

    def get_bucket(self, key: str, capacity: int, refill_rate: float) -> Tuple[bool, float]:
        """
        Check and update token bucket for rate limiting.

        Args:
            key: Unique identifier (user_id, endpoint, etc)
            capacity: Maximum tokens in bucket
            refill_rate: Tokens per second to add

        Returns:
            Tuple of (allowed: bool, remaining_tokens: float)
        """
        with self._lock:
            now = time.time()

            # Initialize bucket if not exists
            if key not in self._buckets:
                self._buckets[key] = {
                    "tokens": float(capacity),
                    "last_refill": now
                }

            bucket = self._buckets[key]

            # Calculate tokens to add based on time elapsed
            time_elapsed = now - bucket["last_refill"]
            tokens_to_add = time_elapsed * refill_rate
            bucket["tokens"] = min(capacity, bucket["tokens"] + tokens_to_add)
            bucket["last_refill"] = now

            # Check if request allowed
            if bucket["tokens"] >= 1:
                bucket["tokens"] -= 1
                return True, bucket["tokens"]
            else:
                return False, bucket["tokens"]

    def cleanup_old_buckets(self, max_age_seconds: int = 3600):
        """
        Remove old buckets that haven't been used recently.

        Args:
            max_age_seconds: Remove buckets older than this (default 1 hour)
        """
        with self._lock:
            now = time.time()
            to_remove = []

            for key, bucket in self._buckets.items():
                if now - bucket["last_refill"] > max_age_seconds:
                    to_remove.append(key)

            for key in to_remove:
                del self._buckets[key]

            if to_remove:
                logger.debug(f"Cleaned up {len(to_remove)} old rate limit buckets")


# Global rate limit store
_rate_limit_store = RateLimitStore()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for FastAPI applications.

    Implements AC#6: Rate Limiting Enforcement.

    Default limits:
    - IA endpoints: 10 requests per 60 seconds per user
    - Health check: 20 requests per 60 seconds per IP
    - Retrieve endpoint: 15 requests per 60 seconds per user
    """

    # Endpoint-specific rate limits (requests per 60 seconds)
    ENDPOINT_LIMITS = {
        "/api/ia/query": (10, "user"),      # 10 per user per 60s
        "/api/ia/health": (20, "ip"),       # 20 per IP per 60s
        "/api/ia/retrieve": (15, "user"),   # 15 per user per 60s
        "/api/documents/upload": (5, "user"), # 5 per user per 60s
    }

    # Default rate limit window (seconds)
    RATE_LIMIT_WINDOW = 60

    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limiting.

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response with rate limit headers
        """
        # Check if endpoint has rate limiting enabled
        endpoint_path = request.url.path
        limit_found = None
        key_type = None

        # Match endpoint pattern
        for pattern, (limit, key_type_val) in self.ENDPOINT_LIMITS.items():
            if endpoint_path.startswith(pattern):
                limit_found = limit
                key_type = key_type_val
                break

        # If no limit configured, allow request
        if limit_found is None:
            response = await call_next(request)
            return response

        # Build rate limit key
        if key_type == "user":
            # Extract user ID from token or session
            # For now, use a simple approach
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                # In real implementation, decode JWT to get user_id
                user_id = auth_header.split()[-1][:10]  # Simplified
                key = f"rate_limit:user:{user_id}:{endpoint_path}"
            else:
                # Unauthenticated request - use IP
                key = f"rate_limit:ip:{request.client.host}:{endpoint_path}"
        else:  # ip-based
            key = f"rate_limit:ip:{request.client.host}:{endpoint_path}"

        # Convert limit per 60s to tokens per second
        refill_rate = limit_found / self.RATE_LIMIT_WINDOW

        # Check rate limit
        allowed, remaining = _rate_limit_store.get_bucket(
            key=key,
            capacity=limit_found,
            refill_rate=refill_rate
        )

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {key}: "
                f"limit={limit_found}/{self.RATE_LIMIT_WINDOW}s"
            )

            response = JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded: "
                              f"{limit_found} requests per {self.RATE_LIMIT_WINDOW} seconds",
                    "retry_after": self.RATE_LIMIT_WINDOW
                }
            )
            response.headers["Retry-After"] = str(self.RATE_LIMIT_WINDOW)
            response.headers["X-RateLimit-Limit"] = str(limit_found)
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.RATE_LIMIT_WINDOW)
            return response

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(limit_found)
        response.headers["X-RateLimit-Remaining"] = str(int(remaining))
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.RATE_LIMIT_WINDOW)

        return response


def get_rate_limit_key(request: Request, endpoint: str = None) -> str:
    """
    Get rate limit key for request.

    Args:
        request: HTTP request
        endpoint: Optional endpoint identifier

    Returns:
        Rate limit key string
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        user_id = auth_header.split()[-1][:10]
        return f"user:{user_id}"
    else:
        return f"ip:{request.client.host}"


def check_rate_limit(
    key: str,
    limit: int = 10,
    window: int = 60
) -> bool:
    """
    Check if request is within rate limit.

    Args:
        key: Rate limit key
        limit: Number of requests allowed
        window: Time window in seconds

    Returns:
        True if request allowed, False otherwise
    """
    refill_rate = limit / window
    allowed, _ = _rate_limit_store.get_bucket(
        key=key,
        capacity=limit,
        refill_rate=refill_rate
    )
    return allowed
