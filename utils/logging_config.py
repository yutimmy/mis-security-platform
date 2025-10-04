"""Centralized logging configuration for the application."""
from __future__ import annotations

import logging
from logging.config import dictConfig
from typing import Optional

_DEFAULT_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s %(levelname)s %(name)s - %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}


def configure_logging(app: Optional["Flask"] = None, level: int = logging.INFO) -> None:
    """Configure root logging and align the Flask app logger if provided."""
    dictConfig(_DEFAULT_LOGGING)
    if app is not None:
        app.logger.setLevel(level)
        app.logger.propagate = False
        # Replace existing handlers with the standardized console handler.
        app.logger.handlers.clear()
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(_DEFAULT_LOGGING["formatters"]["standard"]["format"]))
        app.logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Helper for retrieving module loggers with the configured defaults."""
    return logging.getLogger(name)
