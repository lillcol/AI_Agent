"""Stage 00 tutorial example: minimal runnable LLM call (DeepSeek).

This file demonstrates the smallest complete model-calling path:
1) read config (base_url / api_key)
2) build chat-completions payload (system + user)
3) send HTTP POST request
4) parse and print model text output

The example intentionally stays single-turn (no tools, no memory).
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import request

if __package__ is None or __package__ == "":
    # Support direct file execution:
    # python src/ai_agent/learning/stage_00_foundation/react_hello_world.py
    #
    # Module execution is usually preferred (`PYTHONPATH=src python -m ...`),
    # but many learners run files directly. Add `src` to sys.path so
    # `import ai_agent...` works and avoids ModuleNotFoundError.
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from ai_agent.config.settings import settings


@dataclass
class DeepSeekClient:
    """Minimal DeepSeek client for tutorial use."""

    # Model service base URL, e.g. https://api.deepseek.com
    base_url: str
    # API key (loaded from private.local.yaml, should never be committed)
    api_key: str
    # Default model name (replace as needed)
    model: str = "deepseek-chat"
    # Request timeout (seconds)
    timeout: int = 60
    # Usage returned by the latest API call, for token-cost visibility.
    last_usage: dict[str, Any] | None = None

    def chat(self, user_query: str) -> str:
        """Send one user query and return model text answer."""
        # system_prompt controls output style:
        # - concise
        # - direct answer
        # - no reasoning trace
        system_prompt = (
            "你是一个简洁助手。"
            "请直接给出结果，语言尽量简洁。"
            "不要输出思考过程、推理步骤或中间分析。"
        )

        # Minimal Chat Completions payload:
        # - model: target model
        # - temperature=0: stable/reproducible output
        # - messages: conversation context (system + user)
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query},
            ],
        }

        # DeepSeek Chat Completions endpoint.
        endpoint = f"{self.base_url.rstrip('/')}/chat/completions"

        # Build a standard HTTP POST request with urllib.
        # data must be bytes: json.dumps(...) then encode("utf-8").
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        # Execute request and parse JSON response.
        with request.urlopen(req, timeout=self.timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        # Keep latest usage metadata so upper layers can log token costs.
        usage = body.get("usage")
        self.last_usage = usage if isinstance(usage, dict) else None

        # Final text is located at:
        # choices[0].message.content
        return body["choices"][0]["message"]["content"].strip()


def main() -> None:
    # 1) Read DeepSeek config from centralized merged settings
    # (public.yaml + private.local.yaml).
    deepseek_cfg = settings.services.get("deepseek", {})
    base_url = deepseek_cfg.get("base_url")
    api_key = deepseek_cfg.get("api_key")

    # 2) Read user input
    # Prefer CLI argument for script-friendly usage:
    # python .../react_hello_world.py "What is 3 to the 5th power?"
    # If no argument is given, fallback to interactive input.
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        query = input("请输入问题（例如：3的5次方等于多少？）: ").strip()

    # 3) Build client, execute a single call, print result
    client = DeepSeekClient(base_url=base_url, api_key=api_key)
    answer = client.chat(query)
    print(answer)


if __name__ == "__main__":
    # Script entrypoint.
    main()
