"""Stage 00 tutorial example: minimal runnable LLM call (DeepSeek).

This file demonstrates the smallest complete model-calling path:
1) read config (base_url / api_key)
2) build chat-completions payload (system + user)
3) send HTTP POST request
4) parse and print model text output

The example intentionally stays single-turn (no tools, no memory).
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    # Support direct file execution:
    # python src/ai_agent/learning/stage_00_foundation/react_hello_world.py
    #
    # Module execution is usually preferred (`PYTHONPATH=src python -m ...`),
    # but many learners run files directly. Add `src` to sys.path so
    # `import ai_agent...` works and avoids ModuleNotFoundError.
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from ai_agent.core.llm.clients import DeepSeekClient


def main() -> None:
    # 1) Read user input
    # Prefer CLI argument for script-friendly usage:
    # python .../react_hello_world.py "What is 3 to the 5th power?"
    # If no argument is given, fallback to interactive input.
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        query = input("请输入问题（例如：3的5次方等于多少？）: ").strip()

    # 2) Build client from centralized factory and execute one call.
    # Import locally to avoid circular import during module loading.
    from ai_agent.core.llm.factory import build_deepseek_client

    client = build_deepseek_client()
    answer = client.chat(query)
    print(answer)


if __name__ == "__main__":
    # Script entrypoint.
    main()
