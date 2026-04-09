"""ReAct Agent beginner example (minimal Thought-Action-Observation loop).

This file demonstrates the classic ReAct control loop:
1) Thought: ask the LLM what to do next
2) Action: if needed, call a tool (calculator in this demo)
3) Observation: feed tool output back to the LLM
4) Repeat until the model returns a final answer

Constraints:
- Minimal dependencies: reuse existing LLM client + calculator tool + registry
- Focus on three learning points:
  - state management (store each step)
  - loop control (max steps + terminal conditions)
  - observable logs (step-by-step trace in logs/app.log)
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    # Allow running this file directly:
    # python src/ai_agent/learning/stage_03_react_agent/react_loop_demo.py "What is 3 to the 5th power plus 10 divided by 2 minus 8?"
    #
    # Add ".../AI_Agent/src" to sys.path so `import ai_agent...` works.
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


from ai_agent.core.llm.factory import build_deepseek_client
from ai_agent.core.llm.clients import DeepSeekClient
from ai_agent.tools import registry
from ai_agent.tools.examples.calculator import CalculatorTool
from ai_agent.utils.logger import setup_logger


@dataclass
class StepState:
    """One ReAct step snapshot (what the model decided + what we observed).
    """

    step_index: int
    thought: str = ""
    action_tool: str = ""
    action_arguments: dict[str, Any] = field(default_factory=dict)
    observation: str = ""


@dataclass
class AgentState:
    """ReAct agent overall state across multiple steps.
    """

    question: str
    steps: list[StepState] = field(default_factory=list)
    final_answer: str | None = None
    llm_call_count: int = 0
    prompt_tokens_total: int = 0
    completion_tokens_total: int = 0
    total_tokens_total: int = 0


def _extract_first_json_object(text: str) -> str:
    """Extract the first JSON object from a string.

    Why:
    LLM outputs may contain leading text. For this educational scaffold,
    we tolerate minor formatting and extract the first {...} block.

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

    """

    raw_json = _extract_first_json_object(content)
    return json.loads(raw_json)


class CalculatorReActAgent:
    """A minimal ReAct agent that can solve arithmetic via calculator tool.
    """

    def __init__(self, llm_client: DeepSeekClient, max_steps: int = 6) -> None:
        self.llm = llm_client
        self.max_steps = max_steps
        self.logger = setup_logger("react_agent")

    def run(self, question: str) -> AgentState:
        # State keeps the step trace for learning/debugging.
        state = AgentState(question=question)

        # Prepare tool registry once (calculator only in this stage).
        # Keep registration here so the demo is standalone.
        registry.register(CalculatorTool())

        # DeepSeekClient is configured for concise answers in earlier stages.
        # Here we keep "thought" as a short label, not full chain-of-thought.
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
            "- Do not repeat an action that was already executed successfully.\n"
            "- Continue from the latest computed result whenever possible.\n"
            "- If a previous step already included a sub-expression, do not recalculate it separately.\n"
            "- Do not output any additional text.\n"
        )

        # Scratchpad: feed accumulated execution history back after each tool call.
        observations: list[str] = []
        self.logger.info("=== ReAct Run Start ===")
        self.logger.info("Question: %s", question)
        self.logger.info("Max steps: %s", self.max_steps)

        for i in range(1, self.max_steps + 1):
            self.logger.info("--- Step %s/%s ---", i, self.max_steps)
            step_prompt = self._build_prompt(
                system_instructions=system_instructions,
                question=question,
                observations=observations,
            )

            # Call the LLM once per step.
            model_text = self.llm.chat(step_prompt)
            self.logger.info("Step %s | LLM raw (truncated): %s", i, model_text[:400])
            state.llm_call_count += 1

            usage = self.llm.last_usage or {}
            prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
            completion_tokens = int(usage.get("completion_tokens", 0) or 0)
            total_tokens = int(usage.get("total_tokens", prompt_tokens + completion_tokens) or 0)
            state.prompt_tokens_total += prompt_tokens
            state.completion_tokens_total += completion_tokens
            state.total_tokens_total += total_tokens
            self.logger.info(
                "Step %s | Token usage: prompt=%s completion=%s total=%s",
                i,
                prompt_tokens,
                completion_tokens,
                total_tokens,
            )
            self.logger.info(
                "Step %s | Token running total: prompt=%s completion=%s total=%s",
                i,
                state.prompt_tokens_total,
                state.completion_tokens_total,
                state.total_tokens_total,
            )

            parsed = parse_react_output(model_text)
            step = StepState(step_index=i, thought=str(parsed.get("thought", "")).strip())
            state.steps.append(step)
            step_type = str(parsed.get("type", "")).strip()
            self.logger.info(
                "Step %s | THOUGHT: %s",
                i,
                step.thought or "(empty)",
            )
            self.logger.info("Step %s | Parsed type: %s", i, step_type or "(missing)")

            if step_type == "final":
                step.observation = "(final)"
                state.final_answer = str(parsed.get("answer", "")).strip()
                self.logger.info("Step %s | FINAL ANSWER: %s", i, state.final_answer or "(empty)")
                self.logger.info(
                    "Token summary | calls=%s prompt=%s completion=%s total=%s",
                    state.llm_call_count,
                    state.prompt_tokens_total,
                    state.completion_tokens_total,
                    state.total_tokens_total,
                )
                self.logger.info("=== ReAct Run End ===")
                return state

            # Otherwise: action path.
            tool_name = str(parsed.get("tool", "")).strip()
            arguments = parsed.get("arguments", {}) or {}
            if not isinstance(arguments, dict):
                arguments = {}

            step.action_tool = tool_name
            step.action_arguments = arguments

            self.logger.info(
                "Step %s | ACTION: tool=%s args=%s",
                i,
                tool_name,
                json.dumps(arguments, ensure_ascii=False),
            )

            # Execute tool from registry.
            tool_result = registry.execute(tool_name, arguments)
            step.observation = json.dumps(tool_result.output, ensure_ascii=False)

            self.logger.info(
                "Step %s | OBSERVATION: %s",
                i,
                step.observation,
            )

            history_entry = json.dumps(
                {
                    "tool": tool_name,
                    "arguments": arguments,
                    "observation": tool_result.output,
                },
                ensure_ascii=False,
            )
            observations.append(history_entry)
            observations_total_chars = sum(len(item) for item in observations)
            latest_observation_chars = len(step.observation)
            self.logger.info(
                "Step %s | Observations stats: count=%s total_chars=%s latest_chars=%s",
                i,
                len(observations),
                observations_total_chars,
                latest_observation_chars,
            )
            self.logger.info(
                "Step %s | Observations full content: %s",
                i,
                json.dumps(observations, ensure_ascii=False),
            )

        # If we exit the loop, no final answer was reached in max_steps.
        state.final_answer = "Unable to solve within max_steps."
        self.logger.warning("Stopped after max_steps=%s.", self.max_steps)
        self.logger.info(
            "Token summary | calls=%s prompt=%s completion=%s total=%s",
            state.llm_call_count,
            state.prompt_tokens_total,
            state.completion_tokens_total,
            state.total_tokens_total,
        )
        self.logger.info("=== ReAct Run End ===")
        return state

    @staticmethod
    def _build_prompt(
        system_instructions: str,
        question: str,
        observations: list[str],
    ) -> str:
        """Build the single-string prompt passed into DeepSeekClient.chat().
        """

        history = ""
        if observations:
            history = "Execution history so far:\n" + "\n".join(f"- {obs}" for obs in observations) + "\n\n"

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
    # Get user question:
    # - CLI arg preferred
    # - fallback to stdin
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        question = input("Enter a math question: ").strip()
    if not question:
        raise RuntimeError("Empty question.")

    llm_client = build_deepseek_client()
    agent = CalculatorReActAgent(llm_client=llm_client, max_steps=6)

    state = agent.run(question)
    # Print only the final answer for user-facing output.
    print(state.final_answer or "")
    print(
        "[Token Usage] "
        f"calls={state.llm_call_count}, "
        f"prompt={state.prompt_tokens_total}, "
        f"completion={state.completion_tokens_total}, "
        f"total={state.total_tokens_total}"
    )

    # For learning: inspect the full trace in logs/app.log.


if __name__ == "__main__":
    main()

