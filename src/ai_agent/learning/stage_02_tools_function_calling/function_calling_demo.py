"""Stage 02 example: LLM Function Calling -> tool registration -> execution.

This runnable demo shows the full function-calling path:
1) register tools (calculator / time / weather)
2) ask the LLM for strict planner JSON (tool + arguments)
3) parse planner JSON and execute the selected tool
4) ask the LLM to produce a concise final answer from tool output

The implementation is intentionally classic and explicit, without
framework-specific integrations.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    # Allow direct script execution (not using `python -m`).
    # Example:
    # python src/ai_agent/learning/stage_02_tools_function_calling/function_calling_demo.py "What is 3 to the 5th power?"
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

# Imports are now safe for both:
# - module execution: `PYTHONPATH=src python -m ...`
# - direct script execution: `python path/to/file.py ...`
from ai_agent.config.settings import settings
from ai_agent.tools import FunctionCallingOrchestrator, registry
from ai_agent.tools.examples.amap_weather import AMapWeatherTool
from ai_agent.tools.examples.calculator import CalculatorTool
from ai_agent.tools.examples.get_time import GetTimeTool


# Import the existing native LLM client without changing it.
# DeepSeekClient.chat(user_query: str) -> str matches orchestrator expectations.
from ai_agent.learning.stage_00_foundation.react_hello_world import DeepSeekClient  # noqa: E402


def main() -> None:
    # 1) Load DeepSeek config (URL + key) from merged settings.
    # Reuse the existing native LLM client; do not add provider logic here.
    deepseek_cfg = settings.services.get("deepseek", {})
    base_url = deepseek_cfg.get("base_url", "")
    api_key = deepseek_cfg.get("api_key", "")

    # This demo assumes `configs/private.local.yaml` already contains `api_key`.
    llm_client = DeepSeekClient(base_url=base_url, api_key=api_key)

    # 2) Register tools into the singleton `ToolRegistry`.
    # If there is a name conflict, `register()` overwrites (safe for re-runs).
    registry.register(CalculatorTool())
    registry.register(GetTimeTool())
    registry.register(AMapWeatherTool())

    # 3) Build orchestrator:
    # planner JSON -> execute tool -> LLM generates final answer
    orchestrator = FunctionCallingOrchestrator(llm_client=llm_client, tool_registry=registry)

    # 4) Read user query from CLI args; if none, read from stdin.
    user_query = " ".join(sys.argv[1:]).strip()
    if not user_query:
        user_query = input("Please enter a question (calculator/time/weather): ").strip()
    if not user_query:
        raise RuntimeError("Empty input.")

    # 5) Run full function-calling flow and print the final answer.
    final_text = orchestrator.run(user_query=user_query)
    print(final_text)


if __name__ == "__main__":
    main()

