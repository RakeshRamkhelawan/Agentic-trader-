import sys
import logging
from backend.core.config.settings import settings


def setup_logging(name: str) -> logging.Logger:
    """
    Configure and return a logger instance.
    """
    logger = logging.getLogger(name)

    # Als logger al handlers heeft, niets doen (voorkom dubbele logs)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)

    # Formatter kiezen
    if settings.ENV == "production":
        # JSON Formatter zou hier komen (voor nu even simpel)
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}'
        )
    else:
        # Human readable
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
