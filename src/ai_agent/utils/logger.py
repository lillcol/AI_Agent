"""Shared logging configuration helper."""

from __future__ import annotations

import logging
from pathlib import Path

from ai_agent.config.settings import settings


def setup_logger(name: str = "ai_agent") -> logging.Logger:
    """Create and return a project logger with console and file handlers."""
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(settings.log_level.upper())

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(logs_dir / "app.log")
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger

