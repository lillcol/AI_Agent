"""LLM Function Calling parsing and tool execution orchestration.

This module is intentionally framework-agnostic:
- it does NOT depend on how a provider implements function calling
- it only expects a plain text chat API from your existing LLM client

The demo uses a strict JSON protocol:

First step (planner):
  - tool_call:
    {"type":"tool_call","tool_name":"calculator","arguments":{"expression":"3**5"}}
  - final:
    {"type":"final","answer":"..."}

Second step (answerer):
  - plain text, concise answer (no JSON requirement).
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    # Allow direct execution/import when running this file as a script:
    # python src/ai_agent/tools/function_calling.py
    # This makes `from ai_agent...` work by adding ".../AI_Agent/src" to sys.path.
    # For this file: .../AI_Agent/src/ai_agent/tools/function_calling.py
    # parents[0]=tools, parents[1]=ai_agent, parents[2]=src
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ai_agent.tools.registry import ToolRegistry, registry
from ai_agent.utils.logger import setup_logger


@dataclass(frozen=True)
class ParsedToolCall:
    """Parsed planner result from the LLM."""

    type: str  # "tool_call" | "final"
    tool_name: str | None
    arguments: dict[str, Any] | None
    answer: str | None


def _extract_first_json_object(text: str) -> str:
    """Extract the first JSON object from a string.

    We assume the output is mostly JSON (strict or near-strict),
    but we tolerate leading/trailing whitespace.

    Learning note:
    Many real LLM outputs include small formatting artifacts.
    For this educational scaffold we keep parsing minimal:
    - find the first "{" character
    - scan forward while tracking brace depth
    - return that object substring
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


def parse_planner_output(content: str) -> ParsedToolCall:
    """Parse planner JSON and normalize it into a ParsedToolCall."""
    # Step A: extract the first JSON object substring.
    # Step B: json.loads into a Python dict.
    # Step C: normalize into our strongly-typed ParsedToolCall.
    raw_json = _extract_first_json_object(content)
    obj = json.loads(raw_json)

    call_type = str(obj.get("type", "")).strip()
    if call_type == "tool_call":
        tool_name = str(obj.get("tool_name", "")).strip()
        arguments = obj.get("arguments", {})
        # arguments is expected to be a JSON object that matches the tool's input_schema.
        if not isinstance(arguments, dict):
            raise ValueError("tool_call.arguments must be an object.")
        return ParsedToolCall(type="tool_call", tool_name=tool_name, arguments=arguments, answer=None)

    if call_type == "final":
        answer = str(obj.get("answer", "")).strip()
        return ParsedToolCall(type="final", tool_name=None, arguments=None, answer=answer)

    raise ValueError(f"Invalid planner output type: {call_type}")


class FunctionCallingOrchestrator:
    """A minimal two-step flow: plan -> execute tool -> answer."""

    def __init__(self, llm_client: Any, tool_registry: ToolRegistry = registry) -> None:
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.logger = setup_logger("function_calling_orchestrator")

    @staticmethod
    def _truncate_text(text: str, max_chars: int = 2000) -> str:
        """Truncate long strings for readable logs."""
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "...(truncated)"

    def run(self, user_query: str) -> str:
        """Run planner/exec/answer with the provided LLM client."""
        tool_defs = self.tool_registry.list_tools()

        # Step 1: planning.
        # The LLM must output a strict JSON object so we can reliably parse it.
        # We avoid provider-specific "tool_calls" formats here and instead
        # implement a small, classic demo protocol.
        #
        # Important learning detail:
        # - The planner prompt includes tool definitions (name/description/schemas).
        # - For function calling education, the planner output is constrained to:
        #     { "type": "tool_call", "tool_name": "...", "arguments": {...} }
        #   or
        #     { "type": "final", "answer": "..." }
        #
        # This keeps the rest of the code extremely deterministic and easy to debug.
        planner_prompt = (
            "You are a tool planner.\n"
            "You must choose one tool call OR return a final answer.\n"
            "Return STRICT JSON ONLY (no markdown, no extra text).\n\n"
            "Allowed return formats:\n"
            "1) Tool call:\n"
            '{"type":"tool_call","tool_name":"<tool>","arguments":{...}}\n'
            "2) Final:\n"
            '{"type":"final","answer":"<final text>"}\n\n'
            "Argument rules:\n"
            "- For tool arguments, follow the JSON schema descriptions from Tools.\n"
            '- For calculator, arguments.expression should be a Python-like arithmetic '
            'expression using numbers and operators: + - * / % ** and parentheses.\n'
            "- For get_time, timezone should be an IANA timezone like Asia/Shanghai.\n"
            "- For amap_weather, arguments.city should be the city name.\n\n"
            "Tools:\n"
            f"{json.dumps(tool_defs, ensure_ascii=False)}\n\n"
            f"User question:\n{user_query}\n"
        )

        # Ask the planner step.
        planner_text = self.llm_client.chat(planner_prompt)
        self.logger.info("Planner raw response (truncated): %s", self._truncate_text(planner_text))

        # Parse into our normalized representation so the orchestrator can switch on type.
        parsed = parse_planner_output(planner_text)

        # Step 1b: if model decided "final", return immediately.
        if parsed.type == "final":
            self.logger.info("Planner decided to return final answer directly.")
            return parsed.answer or ""

        # Otherwise we expect a tool call.
        assert parsed.type == "tool_call"

        # Step 2: execute the selected tool from the registry.
        self.logger.info(
            "Planner decided to call tool: %s | arguments=%s",
            parsed.tool_name,
            json.dumps(parsed.arguments or {}, ensure_ascii=False),
        )
        tool_result = self.tool_registry.execute(parsed.tool_name or "", parsed.arguments or {})
        self.logger.info(
            "Tool execution finished: %s | output(truncated)=%s",
            tool_result.tool_name,
            self._truncate_text(json.dumps(tool_result.output, ensure_ascii=False)),
        )

        # Step 3: ask a second LLM call to convert tool output into the final user-facing text.
        # We keep this prompt simple and explicitly ask for no internal reasoning.
        #
        # In a more advanced system, you might:
        # - feed tool output back along with the original question in a structured format
        # - enforce answer length / formatting
        # - validate the answer schema
        answer_prompt = (
            "You are a concise assistant.\n"
            "Using the tool result below, provide a concise final answer.\n"
            "Do NOT output any internal reasoning.\n\n"
            f"Tool result (JSON): {json.dumps(tool_result.output, ensure_ascii=False)}\n\n"
            f"User question: {user_query}\n"
        )

        # Final answer text returned by the LLM.
        return self.llm_client.chat(answer_prompt).strip()

