"""ReAct Agent 入门示例（极简思考-行动-观察闭环）。

这个文件演示 ReAct 的经典控制循环：
1) Thought：向大模型询问下一步做什么
2) Action：如需要则调用工具（本例使用 calculator）
3) Observation：把工具结果回填给大模型
4) Repeat：直到大模型返回最终答案（final）

This demo shows the *classic* ReAct control loop:
1) Thought: ask the LLM what to do next
2) Action: if needed, call a tool (here: calculator)
3) Observation: feed the tool result back to the LLM
4) Repeat until the LLM returns a final answer

Constraints / 学习重点：
- Minimal dependencies / 最少依赖：复用你现有的 LLM client + calculator tool + registry
- Three learning points / 三个学习点：
  - state management / 状态管理：记录每一步（thought/action/observation）
  - loop control / 循环控制：最大步数 + 终止条件
  - observable logs / 可观测日志：逐步打印并写入 `logs/app.log`
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    # Allow running this file directly:
    # python src/ai_agent/learning/stage_03_react_agent/react_loop_demo.py "3的5次方加10除2再减8"
    #
    # CN: 直接运行文件时，需要把 `src` 加到 sys.path，保证能 import ai_agent。
    # EN: We add ".../AI_Agent/src" to sys.path so `import ai_agent...` works.
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


from ai_agent.config.settings import settings
from ai_agent.tools import registry
from ai_agent.tools.examples.calculator import CalculatorTool
from ai_agent.utils.logger import setup_logger

# Reuse your existing native LLM client without modifying it.
from ai_agent.learning.stage_00_foundation.react_hello_world import DeepSeekClient


@dataclass
class StepState:
    """One ReAct step snapshot (what the model decided + what we observed).

    CN: 单步快照：模型决定的内容 + 我们观察到的工具结果（observation）。
    """

    step_index: int
    thought: str = ""
    action_tool: str = ""
    action_arguments: dict[str, Any] = field(default_factory=dict)
    observation: str = ""


@dataclass
class AgentState:
    """ReAct agent overall state across multiple steps.

    CN: 多步执行期间的整体状态（question/steps/final_answer）。
    """

    question: str
    steps: list[StepState] = field(default_factory=list)
    final_answer: str | None = None


def _extract_first_json_object(text: str) -> str:
    """Extract the first JSON object from a string.

    Why:
    LLM outputs may contain leading text. For this educational scaffold,
    we tolerate minor formatting and extract the first {...} block.

    CN:
    LLM 有时会在 JSON 前后夹杂少量文字，所以我们只取“第一个 {...} JSON 块”。
    """

    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in model output.")

    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    raise ValueError("Unterminated JSON object in model output.")


def parse_react_output(content: str) -> dict[str, Any]:
    """Parse LLM output for ReAct demo.

    Expected strict formats (planner-like):
    - Action:
      {
        "type": "action",
        "thought": "...",
        "tool": "calculator",
        "arguments": { "expression": "3**5" }
      }
    - Final:
      {
        "type": "final",
        "thought": "...",
        "answer": "..."
      }

    CN:
    模型输出需要是严格 JSON（或接近 JSON）。这里解析：
    - type=action：提取 tool/arguments，进入工具执行
    - type=final：提取 answer，结束循环
    """

    raw_json = _extract_first_json_object(content)
    return json.loads(raw_json)


class CalculatorReActAgent:
    """A minimal ReAct agent that can solve arithmetic via calculator tool.

    CN: 这是一个“极简 ReAct 计算器代理”：只用 calculator 工具解数学题。
    """

    def __init__(self, llm_client: DeepSeekClient, max_steps: int = 6) -> None:
        self.llm = llm_client
        self.max_steps = max_steps
        self.logger = setup_logger("react_agent")

    def run(self, question: str) -> AgentState:
        # CN: 状态 state 用于学习/调试：记录每一步。
        # EN: State keeps the step trace for learning/debugging.
        state = AgentState(question=question)

        # CN: 这里给当前 stage 准备工具：本阶段只用 calculator。
        # EN: Prepare tool registry once (calculator only in this stage).
        # EN: We still register here to make the demo standalone.
        registry.register(CalculatorTool())

        # CN: DeepSeekClient 在前面阶段的实现中已经倾向“简洁且不输出思考过程”。
        # EN: ReAct system prompt is enforced by DeepSeekClient itself (concise/no reasoning).
        # CN: 因此这里把 thought 设计成短标签，而不是完整推理链。
        # EN: We request "thought" as a *short* description, not detailed chain-of-thought.
        system_instructions = (
            "You are a ReAct-style agent.\n"
            "You must output STRICT JSON ONLY.\n\n"
            "Decide one step at a time:\n"
            "1) If you need calculation, return:\n"
            '{ "type":"action","thought":"<short note>","tool":"calculator",'
            '"arguments":{"expression":"<arithmetic expression>"} }\n\n'
            "2) If you can answer, return:\n"
            '{ "type":"final","thought":"<short note>","answer":"<final answer text>" }\n\n'
            "Rules:\n"
            "- calculator.expression must be a simple arithmetic expression.\n"
            "- Do not output any additional text.\n"
        )

        # CN: scratchpad = observation 列表；每次调用工具后把结果喂回给 LLM。
        # EN: A small "scratchpad" we feed back after each tool call.
        observations: list[str] = []

        for i in range(1, self.max_steps + 1):
            step_prompt = self._build_prompt(
                system_instructions=system_instructions,
                question=question,
                observations=observations,
            )

            # CN: 每一步只调用一次 LLM，得到下一步的 action/final。
            # EN: Call the LLM once per step.
            model_text = self.llm.chat(step_prompt)
            self.logger.info("Step %s | LLM raw (truncated): %s", i, model_text[:400])

            parsed = parse_react_output(model_text)
            step = StepState(step_index=i, thought=str(parsed.get("thought", "")).strip())
            state.steps.append(step)

            if str(parsed.get("type", "")).strip() == "final":
                step.observation = "(final)"
                state.final_answer = str(parsed.get("answer", "")).strip()
                self.logger.info("Step %s | Reached final answer.", i)
                return state

            # CN: 否则进入 action 路径（工具调用）。
            # EN: Otherwise: action path.
            tool_name = str(parsed.get("tool", "")).strip()
            arguments = parsed.get("arguments", {}) or {}
            if not isinstance(arguments, dict):
                arguments = {}

            step.action_tool = tool_name
            step.action_arguments = arguments

            self.logger.info(
                "Step %s | Action: tool=%s args=%s",
                i,
                tool_name,
                json.dumps(arguments, ensure_ascii=False),
            )

            # Execute tool from registry.
            tool_result = registry.execute(tool_name, arguments)
            step.observation = json.dumps(tool_result.output, ensure_ascii=False)

            self.logger.info(
                "Step %s | Observation (truncated): %s",
                i,
                step.observation[:400],
            )

            observations.append(step.observation)

        # CN: 如果走完最大步数仍没 final，认为无法在限制内解决。
        # EN: If we exit loop, we failed to reach a final answer.
        state.final_answer = "Unable to solve within max_steps."
        self.logger.warning("Stopped after max_steps=%s.", self.max_steps)
        return state

    @staticmethod
    def _build_prompt(
        system_instructions: str,
        question: str,
        observations: list[str],
    ) -> str:
        """Build the single-string prompt passed into DeepSeekClient.chat().

        CN: 把 system 指令 + Question + 历史 Observation 拼成一次 step 的 prompt。
        EN: Concatenate system instructions + question + observation history into one step prompt.
        """

        history = ""
        if observations:
            history = "Observations so far:\n" + "\n".join(f"- {obs}" for obs in observations) + "\n\n"

        return (
            system_instructions
            + "\n"
            + "Question:\n"
            + question
            + "\n\n"
            + history
            + "Decide the next step."
        )


def main() -> None:
    # CN: 读取 DeepSeek 配置（public.yaml + private.local.yaml 合并）。
    # EN: Read DeepSeek config from merged settings.
    deepseek_cfg = settings.services.get("deepseek", {})
    base_url = deepseek_cfg.get("base_url", "")
    api_key = deepseek_cfg.get("api_key", "")

    if not base_url or not api_key:
        raise RuntimeError("Missing deepseek.base_url/api_key in configs/public.yaml + configs/private.local.yaml")

    # CN: 获取用户问题：
    # - 优先命令行参数
    # - 没传则进入交互输入
    # EN: Get user question:
    # - CLI arg preferred
    # - fallback to stdin
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        question = input("Enter a math question: ").strip()
    if not question:
        raise RuntimeError("Empty question.")

    llm_client = DeepSeekClient(base_url=base_url, api_key=api_key)
    agent = CalculatorReActAgent(llm_client=llm_client, max_steps=6)

    state = agent.run(question)
    # CN: 用户输出只打印 final_answer，便于公众号读者直接看结果。
    # EN: Print only the final answer for user-facing output.
    print(state.final_answer or "")

    # CN: 学习用途：完整轨迹可在 logs/app.log 查看。
    # EN: For learning: inspect the full trace in logs/app.log.


if __name__ == "__main__":
    main()

