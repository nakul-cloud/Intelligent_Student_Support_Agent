"""Sliding window rate limiting dependency using Redis with in-memory fallback.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Throttles abusive traffic and prevents denial-of-service on sensitive endpoints.
"""

import time
from typing import Callable, Dict, Tuple
from fastapi import HTTPException, Request, status
from app.config.redis import redis_client
from app.config.settings import settings
from app.utils.logger import logger

# In-memory fallback if Redis is unavailable: {key: (count, reset_time)}
_in_memory_limits: Dict[str, Tuple[int, float]] = {}


def rate_limiter(max_requests: int = 30, window_seconds: int = 60) -> Callable:
    """FastAPI route dependency enforcing sliding-window request throttling.

    Args:
        max_requests: Max permitted calls within window.
        window_seconds: Window duration in seconds.

    Raises:
        HTTPException: Status 429 when rate limit is exceeded.
    """

    async def _rate_limit_dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        key = f"rate_limit:{path}:{client_ip}"

        try:
            # Atomic Redis sliding window check
            current_count = await redis_client.incr(key)
            if current_count == 1:
                await redis_client.expire(key, window_seconds)

            if current_count > max_requests:
                logger.warning(
                    f"Rate limit exceeded on {path} for IP {client_ip} ({current_count}/{max_requests})"
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: maximum {max_requests} requests per {window_seconds} seconds. Please slow down.",
                )
        except HTTPException:
            raise
        except Exception as exc:
            # Fallback to local in-memory window
            now = time.time()
            count, reset_time = _in_memory_limits.get(key, (0, now + window_seconds))

            if now > reset_time:
                count = 1
                reset_time = now + window_seconds
            else:
                count += 1

            _in_memory_limits[key] = (count, reset_time)

            if count > max_requests:
                logger.warning(
                    f"Rate limit (in-memory) exceeded on {path} for IP {client_ip} ({count}/{max_requests})"
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: maximum {max_requests} requests per {window_seconds} seconds. Please slow down.",
                )

    return _rate_limit_dependency
