"""Centralized settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Application-level settings container."""

    app_name: str = os.getenv("APP_NAME", "ai-agent-learning")
    app_env: str = os.getenv("APP_ENV", "dev")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()

