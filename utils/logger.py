from loguru import logger

from .config import settings

logger.add(
    "./logs/app_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="7 days",
    level=settings.LOG_LEVEL.upper(),
    format="{time} - {level} - {message}",
    enqueue=True,
)
