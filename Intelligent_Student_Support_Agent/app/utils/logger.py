"""Structured application logging utility using Loguru."""

import os
import sys
from loguru import logger
from app.config.settings import settings

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Remove default Loguru handler
logger.remove()

# Console handler with clean, colored format
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level.upper(),
)

# File handler with rotation and retention
logger.add(
    "logs/application.log",
    rotation="10 MB",
    retention="10 days",
    compression="zip",
    encoding="utf-8",
    level=settings.log_level.upper(),
    enqueue=True,
    backtrace=True,
    diagnose=True,
)

__all__ = ["logger"]
