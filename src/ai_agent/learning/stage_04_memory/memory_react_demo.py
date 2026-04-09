"""Stage 04 demo: memory-enabled multi-turn ReAct agent.

What this demo adds on top of Stage 03:
- short-term memory (conversation + tool traces)
- long-term memory (file persistence for reusable knowledge)
- memory-aware prompt building (recall before each turn)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    # Allow direct execution:
    # python src/ai_agent/learning/stage_04_memory/memory_react_demo.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from ai_agent.core.memory import LongTermMemoryFile, MemoryManager, ShortTermMemory
from ai_agent.core.llm.factory import build_deepseek_client
from ai_agent.core.llm.clients import DeepSeekClient
from ai_agent.tools import registry
from ai_agent.tools.examples.calculator import CalculatorTool
from ai_agent.utils.logger import setup_logger


def _extract_first_json_object(text: str) -> str:
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
    return json.loads(_extract_first_json_object(content))


@dataclass
class TurnResult:
    user_query: str
    answer: str


class MemoryReActAgent:
    """Minimal memory-enabled ReAct agent for Stage 04."""

    def __init__(self, llm_client: DeepSeekClient, memory: MemoryManager, max_steps: int = 5) -> None:
        self.llm = llm_client
        self.memory = memory
        self.max_steps = max_steps
        self.logger = setup_logger("memory_react_agent")
        registry.register(CalculatorTool())

    def ask(self, user_query: str) -> TurnResult:
        self.memory.add_short_message("user", user_query)
        short_context = self.memory.format_short_context(query=user_query, limit=12)
        long_context = self.memory.format_long_context(query=user_query, limit=3)
        self.logger.info("Memory recall | short:\n%s", short_context)
        self.logger.info("Memory recall | long:\n%s", long_context)

        system_instructions = (
            "You are a memory-enabled ReAct agent.\n"
            "Output STRICT JSON ONLY.\n\n"
            "Available tool: calculator.\n\n"
            "Return one of:\n"
            '1) {"type":"action","thought":"<short note>","tool":"calculator","arguments":{"expression":"<expr>"}}\n'
            '2) {"type":"final","thought":"<short note>","answer":"<answer>"}\n\n'
            "Rules:\n"
            "- Prefer using recalled memory when sufficient.\n"
            "- Avoid recomputing already solved sub-parts from memory.\n"
            "- Keep thought short.\n"
            "- No additional text outside JSON.\n"
        )

        observations: list[str] = []
        final_answer = ""
        for step in range(1, self.max_steps + 1):
            prompt = self._build_prompt(
                system_instructions=system_instructions,
                user_query=user_query,
                short_context=short_context,
                long_context=long_context,
                observations=observations,
            )
            model_text = self.llm.chat(prompt)
            parsed = parse_react_output(model_text)
            step_type = str(parsed.get("type", "")).strip()
            thought = str(parsed.get("thought", "")).strip()
            self.logger.info("Turn step %s | THOUGHT: %s", step, thought or "(empty)")

            if step_type == "final":
                final_answer = str(parsed.get("answer", "")).strip()
                self.logger.info("Turn step %s | FINAL: %s", step, final_answer)
                break

            tool_name = str(parsed.get("tool", "")).strip()
            arguments = parsed.get("arguments", {}) or {}
            if not isinstance(arguments, dict):
                arguments = {}
            self.logger.info(
                "Turn step %s | ACTION: tool=%s args=%s",
                step,
                tool_name,
                json.dumps(arguments, ensure_ascii=False),
            )
            tool_result = registry.execute(tool_name, arguments).output
            self.memory.add_tool_result(tool_name, arguments, tool_result)
            observation = json.dumps(
                {"tool": tool_name, "arguments": arguments, "observation": tool_result},
                ensure_ascii=False,
            )
            observations.append(observation)
            self.logger.info("Turn step %s | OBSERVATION: %s", step, json.dumps(tool_result, ensure_ascii=False))

        if not final_answer:
            final_answer = "Unable to answer within max_steps."

        self.memory.add_short_message("assistant", final_answer)
        self._maybe_store_long_term_knowledge(user_query=user_query, answer=final_answer)
        return TurnResult(user_query=user_query, answer=final_answer)

    def _maybe_store_long_term_knowledge(self, user_query: str, answer: str) -> None:
        q = user_query.lower()
        should_store = any(keyword in q for keyword in ["方法", "叫什么", "how", "method", "偏好", "preference"])
        if should_store:
            topic = "method_explanation"
            content = f"Q: {user_query} | A: {answer}"
            self.memory.remember_knowledge(topic=topic, content=content, tags=["stage_04", "react", "memory"])
            self.logger.info("Long-term memory write | topic=%s", topic)

    @staticmethod
    def _build_prompt(
        system_instructions: str,
        user_query: str,
        short_context: str,
        long_context: str,
        observations: list[str],
    ) -> str:
        obs_block = ""
        if observations:
            obs_block = "Tool observations in this turn:\n" + "\n".join(f"- {item}" for item in observations) + "\n\n"
        return (
            system_instructions
            + "\n"
            + "Short-term memory context:\n"
            + short_context
            + "\n\n"
            + "Long-term memory recall:\n"
            + long_context
            + "\n\n"
            + obs_block
            + "User question:\n"
            + user_query
            + "\n\n"
            + "Decide next step."
        )


def build_default_agent() -> MemoryReActAgent:
    llm = build_deepseek_client()
    memory = MemoryManager(
        # Keep both record count and character budget to avoid prompt explosion.
        short_term=ShortTermMemory(max_records=40, max_chars=6000),
        long_term=LongTermMemoryFile(),
    )
    return MemoryReActAgent(llm_client=llm, memory=memory, max_steps=5)


def run_scripted_demo(agent: MemoryReActAgent) -> None:
    scripted_questions = [
        "3的5次方是多少？",
        "刚才的结果加10是多少？",
        "这个计算方法叫什么？",
    ]
    print("Running scripted Stage 04 memory demo...\n")
    for idx, question in enumerate(scripted_questions, start=1):
        result = agent.ask(question)
        print(f"[Turn {idx}] Q: {result.user_query}")
        print(f"[Turn {idx}] A: {result.answer}\n")


def run_interactive(agent: MemoryReActAgent) -> None:
    print("Interactive mode. Type 'exit' to stop, '/clear' to reset short-term memory.")
    while True:
        q = input("You: ").strip()
        if not q:
            continue
        if q.lower() in {"exit", "quit"}:
            break
        if q.lower() in {"/clear", ":clear"}:
            agent.memory.clear_short()
            print("Agent: short-term memory cleared.")
            continue
        result = agent.ask(q)
        print("Agent:", result.answer)


def show_long_memory_snapshot(agent: MemoryReActAgent, limit: int = 20) -> None:
    """Print current long-term memory records for quick verification."""
    records = agent.memory.long_term.list_recent(limit=limit)
    print(f"Long-term memory snapshot (latest {limit}):")
    if not records:
        print("- (empty)")
        return
    for idx, record in enumerate(records, start=1):
        topic = str(record.metadata.get("topic", "general"))
        print(f"- [{idx}] topic={topic} | content={record.content}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 04 memory-enabled ReAct demo.")
    parser.add_argument("--interactive", action="store_true", help="Run interactive multi-turn chat.")
    parser.add_argument(
        "--show-long-memory",
        action="store_true",
        help="Print long-term memory snapshot before and after the demo.",
    )
    parser.add_argument(
        "--memory-limit",
        type=int,
        default=20,
        help="How many long-term memory records to print with --show-long-memory.",
    )
    args = parser.parse_args()

    agent = build_default_agent()

    if args.show_long_memory:
        show_long_memory_snapshot(agent, limit=args.memory_limit)
        print("")

    if args.interactive:
        run_interactive(agent)
    else:
        run_scripted_demo(agent)

    if args.show_long_memory:
        print("")
        show_long_memory_snapshot(agent, limit=args.memory_limit)


if __name__ == "__main__":
    main()
