"""Centralized client factory for model/API initialization."""

from __future__ import annotations

from ai_agent.config.settings import settings
from ai_agent.core.llm.clients import DeepSeekClient, MinimaxImageClient


def _service_cfg(service_name: str) -> dict[str, object]:
    cfg = settings.services.get(service_name, {})
    return cfg if isinstance(cfg, dict) else {}


def build_deepseek_client(model: str = "deepseek-chat", timeout: int = 60) -> DeepSeekClient:
    """Build DeepSeek client from centralized config."""
    cfg = _service_cfg("deepseek")
    base_url = str(cfg.get("base_url", "")).strip()
    api_key = str(cfg.get("api_key", "")).strip()
    if not base_url or not api_key:
        raise RuntimeError("Missing deepseek.base_url/api_key in configs/public.yaml + configs/private.local.yaml")
    return DeepSeekClient(base_url=base_url, api_key=api_key, model=model, timeout=timeout)


def build_minimax_image_client(timeout: int = 120) -> MinimaxImageClient:
    """Build Minimax image client from centralized config.

    Note:
    - Class definition lives in `core/llm/clients.py` for unified management.
    """
    cfg = _service_cfg("minimax")
    image_base_url = str(cfg.get("image_base_url", "")).strip()
    api_key = str(cfg.get("api_key", "")).strip()
    if not image_base_url or not api_key:
        raise RuntimeError("Missing minimax.image_base_url/api_key in configs/public.yaml + configs/private.local.yaml")

    return MinimaxImageClient(image_base_url=image_base_url, api_key=api_key, timeout=timeout)

