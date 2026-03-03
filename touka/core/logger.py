import sys
from loguru import logger

logger.remove()

logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <white>{message}</white>",
    colorize=True,
    level="INFO",
)

logger.add(
    "logs/{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} - {message}",
    rotation="00:00",
    retention="30 days",
    level="DEBUG",
    enqueue=True,
)

__all__ = ["logger"]