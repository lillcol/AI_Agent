"""Stage 02 example: LLM Function Calling -> tool registration -> execution.


这是 Stage 02 的可运行 Demo，展示“Function Calling 全流程”：
1. 注册工具（calculator / time / weather）
2. 让 LLM 输出严格 planner JSON（选择工具 + 参数）
3. 解析 planner JSON -> 执行对应工具
4. 再让 LLM 基于工具结果生成简洁最终答案

This is a deliberately "classic and explicit" demo, so you can follow the
end-to-end control flow without any framework-specific integrations.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    # CN: 允许直接运行脚本（而不是用 -m 模块方式）
    # EN: Allow direct script execution (not using `python -m`).
    # CN: 示例：python ... "3的5次方等于多少？"
    # EN: Example: python ... "3의 5 power - how much?" (Chinese input is fine).
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

# CN: 现在这些导入对两种运行方式都安全：
# EN: Imports are safe for both:
# CN: - 模块方式：`PYTHONPATH=src python -m ...`
# EN: - Module execution: `PYTHONPATH=src python -m ...`
# CN: - 直接运行脚本：`python path/to/file.py ...`
# EN: - Direct script execution: `python path/to/file.py ...`
from ai_agent.config.settings import settings
from ai_agent.tools import FunctionCallingOrchestrator, registry
from ai_agent.tools.examples.amap_weather import AMapWeatherTool
from ai_agent.tools.examples.calculator import CalculatorTool
from ai_agent.tools.examples.get_time import GetTimeTool


# CN: Import the existing native LLM client without changing it.
# EN: DeepSeekClient.chat(user_query: str) -> str matches our orchestrator expectations.
from ai_agent.learning.stage_00_foundation.react_hello_world import DeepSeekClient  # noqa: E402


def main() -> None:
    # CN: 1) Load DeepSeek config (URL + key) from merged settings.
    # EN: This demo reuses your existing native LLM client, so we do not implement
    # EN: any new provider logic here.
    deepseek_cfg = settings.services.get("deepseek", {})
    base_url = deepseek_cfg.get("base_url", "")
    api_key = deepseek_cfg.get("api_key", "")

    # CN: 本 demo 假设你已经在 `configs/private.local.yaml` 填好了 `api_key`。
    # EN: This demo assumes you already set `api_key` in `configs/private.local.yaml`.
    llm_client = DeepSeekClient(base_url=base_url, api_key=api_key)

    # CN: 2) 将工具注册到单例 `ToolRegistry`。
    # EN: 2) Register tools into the singleton `ToolRegistry`.
    # CN: 若发生同名冲突，`register()` 会覆盖，因此重复运行不会积累旧状态。
    # EN: If there is a name conflict, `register()` overwrites, so re-running is safe.
    registry.register(CalculatorTool())
    registry.register(GetTimeTool())
    registry.register(AMapWeatherTool())

    # CN: 3) 构建 orchestrator：
    # EN: 3) Build the orchestrator:
    # CN: 它的流程是 planner JSON -> 执行工具 -> 让 LLM 输出最终答案。
    # EN: planner JSON -> execute tool -> LLM generates the final answer.
    orchestrator = FunctionCallingOrchestrator(llm_client=llm_client, tool_registry=registry)

    # CN: 4) 从命令行参数读取用户问题；如果没传则从 stdin 读取。
    # EN: 4) Read the user query from CLI args; if none, read from stdin.
    user_query = " ".join(sys.argv[1:]).strip()
    if not user_query:
        user_query = input("Please enter a question (calculator/time/weather): ").strip()
    if not user_query:
        raise RuntimeError("Empty input.")

    # CN: 5) 运行完整的 function calling 流程，并打印最终答案。
    # EN: 5) Run the full function-calling flow and print the final answer.
    final_text = orchestrator.run(user_query=user_query)
    print(final_text)


if __name__ == "__main__":
    main()

