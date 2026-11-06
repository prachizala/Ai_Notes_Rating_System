"""
Rate limiting module using Redis with local fallback.
"""

import time
from typing import Dict, Tuple
from fastapi import HTTPException, Request, status
from app.core.config import settings
from app.core.logging import logger

try:
    import redis
    redis_client = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_timeout=0.5,
        socket_connect_timeout=0.5,
    )
except Exception as e:
    logger.warning(f"Failed to connect to Redis for rate limiting: {e}. Fallback enabled.")
    redis_client = None

# In-memory fallback: key -> (count, reset_timestamp)
_memory_limits: Dict[str, Tuple[int, float]] = {}


def check_rate_limit(key: str, limit: int, window_seconds: int = 3600) -> bool:
    """
    Returns True if allowed, False if limit exceeded.
    """
    global redis_client
    if redis_client:
        try:
            current = redis_client.incr(key)
            if current == 1:
                redis_client.expire(key, window_seconds)
            return current <= limit
        except Exception as e:
            logger.debug(f"Redis rate limit fallback due to error: {e}")

    # Fallback in-memory
    now = time.time()
    count, reset_at = _memory_limits.get(key, (0, now + window_seconds))
    if now > reset_at:
        count = 0
        reset_at = now + window_seconds
    count += 1
    _memory_limits[key] = (count, reset_at)
    return count <= limit


def rate_limit_auth(request: Request, limit: int = 15, window_seconds: int = 300):
    """
    Rate limit dependency for login/register by client IP.
    Default: 15 attempts per 5 minutes per IP.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    endpoint = request.url.path
    key = f"rl:auth:{client_ip}:{endpoint}"
    if not check_rate_limit(key, limit=limit, window_seconds=window_seconds):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please wait a few minutes before trying again."
        )
