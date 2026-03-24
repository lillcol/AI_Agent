"""Minimal DeepSeek Hello World demo."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib import request

if __package__ is None or __package__ == "":
    # Allow running this file directly: python src/.../react_hello_world.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from ai_agent.config.settings import settings


@dataclass
class DeepSeekClient:
    base_url: str
    api_key: str
    model: str = "deepseek-chat"
    timeout: int = 60

    def chat(self, user_query: str) -> str:
        """Send one user query to DeepSeek and return plain text answer."""
        # Keep the response concise and hide reasoning steps.
        system_prompt = (
            "你是一个简洁助手。"
            "请直接给出结果，语言尽量简洁。"
            "不要输出思考过程、推理步骤或中间分析。"
        )
        # Minimal payload for chat completion.
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
        return body["choices"][0]["message"]["content"].strip()


def main() -> None:
    # Read DeepSeek config from merged settings.
    deepseek_cfg = settings.services.get("deepseek", {})
    base_url = deepseek_cfg.get("base_url")
    api_key = deepseek_cfg.get("api_key")

    # Prefer command line question; fallback to interactive input.
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        query = input("请输入问题（例如：3的5次方等于多少？）: ").strip()

    # Single call, single answer.
    client = DeepSeekClient(base_url=base_url, api_key=api_key)
    answer = client.chat(query)
    print(answer)


if __name__ == "__main__":
    main()
