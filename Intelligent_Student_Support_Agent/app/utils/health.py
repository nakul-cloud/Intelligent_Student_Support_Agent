"""System health check and dependency connectivity verification.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively performs live probes across PostgreSQL, Redis, and Qdrant.
"""

import asyncio
from typing import Any, Dict
from sqlalchemy import text
from qdrant_client import QdrantClient

from app.config.database import engine
from app.config.redis import ping_redis
from app.config.settings import settings
from app.utils.logger import logger


async def check_system_health() -> Dict[str, Any]:
    """Execute live connectivity probes against all core backend dependencies.

    Returns:
        Dict detailing overall status ('healthy', 'degraded', 'unhealthy') and
        individual dependency status for PostgreSQL, Redis, and Qdrant.
    """
    dependencies: Dict[str, Any] = {}
    is_healthy = True

    # 1. Probe PostgreSQL
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        dependencies["database"] = {
            "status": "healthy",
            "type": "postgresql",
            "message": "Connected",
        }
    except Exception as exc:
        is_healthy = False
        logger.error(f"Health check: PostgreSQL probe failed: {exc}")
        dependencies["database"] = {
            "status": "unhealthy",
            "type": "postgresql",
            "error": str(exc),
        }

    # 2. Probe Redis
    try:
        redis_ok = await ping_redis()
        dependencies["cache"] = {
            "status": "healthy" if redis_ok else "degraded",
            "type": "redis",
            "message": "PONG" if redis_ok else "Redis unreachable (in-memory/Postgres fallback)",
        }
        if not redis_ok:
            # Degraded, but not hard blocker
            pass
    except Exception as exc:
        dependencies["cache"] = {
            "status": "degraded",
            "type": "redis",
            "error": str(exc),
        }

    # 3. Probe Qdrant Vector DB
    try:
        def _check_qdrant() -> bool:
            client = QdrantClient(url=settings.qdrant_url, timeout=1.5)
            client.get_collections()
            return True

        qdrant_ok = await asyncio.to_thread(_check_qdrant)
        dependencies["vector_db"] = {
            "status": "healthy" if qdrant_ok else "degraded",
            "type": "qdrant",
            "message": "Connected",
        }
    except Exception as exc:
        dependencies["vector_db"] = {
            "status": "degraded",
            "type": "qdrant",
            "message": f"Remote Qdrant unavailable: {exc}",
        }

    # Compute overall status
    if not dependencies.get("database", {}).get("status") == "healthy":
        overall_status = "unhealthy"
    elif any(d.get("status") == "degraded" for d in dependencies.values()):
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return {
        "status": overall_status,
        "app": "Intelligent Student Support Agent",
        "environment": settings.app_env,
        "dependencies": dependencies,
    }
