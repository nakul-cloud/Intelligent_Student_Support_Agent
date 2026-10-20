"""Uvicorn server runner ."""

import uvicorn
from app.config.settings import settings
from app.utils.logger import logger

if __name__ == "__main__":
    logger.info(f"Starting server on {settings.host}:{settings.port}...")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.app_env == "development",
        log_level="info",
    )
