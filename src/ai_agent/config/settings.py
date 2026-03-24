"""Centralized settings loaded from environment variables and YAML config files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field

from dotenv import load_dotenv
import yaml

load_dotenv()


def _read_yaml(path: Path) -> dict[str, Any]:
    """Read YAML file into dict; return empty dict when file missing."""
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        return {}
    return data


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge two dictionaries and return merged result."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_service_config() -> dict[str, Any]:
    """Load and merge public + private service configuration files."""
    root = Path(__file__).resolve().parents[3]
    public_cfg = _read_yaml(root / "configs" / "public.yaml")
    private_cfg = _read_yaml(root / "configs" / "private.yaml")
    private_local_cfg = _read_yaml(root / "configs" / "private.local.yaml")
    merged_private = _deep_merge(private_cfg, private_local_cfg)
    merged = _deep_merge(public_cfg, merged_private)
    return merged.get("services", {})


@dataclass(frozen=True)
class Settings:
    """Application-level settings container."""

    app_name: str = os.getenv("APP_NAME", "ai-agent-learning")
    app_env: str = os.getenv("APP_ENV", "dev")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    services: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "services", _load_service_config())


settings = Settings()

