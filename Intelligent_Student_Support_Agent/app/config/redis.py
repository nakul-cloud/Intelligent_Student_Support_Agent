import asyncio
from redis.asyncio import Redis
from app.config.settings import settings
from app.utils.logger import logger

# Singleton async Redis client instance
redis_client = Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    decode_responses=True,
    socket_connect_timeout=1,
)


async def get_redis() -> Redis:
    """FastAPI dependency for accessing the Redis client."""
    return redis_client


async def ping_redis() -> bool:
    """Verify that Redis is healthy and responding to ping."""
    try:
        response = await asyncio.wait_for(redis_client.ping(), timeout=1.0)
        logger.info(f"Redis ping response: {response}")
        return bool(response)
    except Exception as exc:
        logger.warning(f"Redis not available ({exc}). Falling back to primary DB.")
        return False
