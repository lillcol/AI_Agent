"""Shared API client implementations for LLM and image generation."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any
from urllib import request


@dataclass
class DeepSeekClient:
    """Minimal DeepSeek chat-completions client."""

    base_url: str
    api_key: str
    model: str = "deepseek-chat"
    timeout: int = 60
    last_usage: dict[str, Any] | None = None

    def chat(self, user_query: str) -> str:
        system_prompt = (
            "你是一个简洁助手。"
            "请直接给出结果，语言尽量简洁。"
            "不要输出思考过程、推理步骤或中间分析。"
        )
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query},
            ],
        }
        endpoint = f"{self.base_url.rstrip('/')}/chat/completions"
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=self.timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        usage = body.get("usage")
        self.last_usage = usage if isinstance(usage, dict) else None
        return body["choices"][0]["message"]["content"].strip()


@dataclass
class MinimaxImageClient:
    """POST to ``{image_base_url}/image_generation`` with Bearer auth."""

    image_base_url: str
    api_key: str
    timeout: int = 120

    def generate(
        self,
        *,
        prompt: str,
        model: str = "image-01",
        aspect_ratio: str = "16:9",
        response_format: str = "url",
        n: int = 1,
        prompt_optimizer: bool = True,
        extra: dict[str, Any] | None = None,
        verbose: bool = True,
    ) -> dict[str, Any]:
        endpoint = f"{self.image_base_url.rstrip('/')}/image_generation"
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "response_format": response_format,
            "n": n,
            "prompt_optimizer": prompt_optimizer,
        }
        if extra:
            payload.update(extra)

        if verbose:
            print(
                f"[progress] (1/2) POST image_generation "
                f"(model={model}, n={n}, aspect_ratio={aspect_ratio}, format={response_format})...",
                file=sys.stderr,
                flush=True,
            )

        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=self.timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        if not isinstance(body, dict):
            raise TypeError("Expected JSON object in response.")
        if verbose:
            print("[progress] (2/2) API response received and JSON parsed.", file=sys.stderr, flush=True)
        return body

