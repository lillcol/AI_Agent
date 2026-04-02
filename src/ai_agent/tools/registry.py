"""Tool registry (singleton) for register/get/execute operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai_agent.tools.base import Tool


@dataclass(frozen=True)
class ToolExecutionResult:
    """Execution result wrapper (useful for observability)."""

    tool_name: str
    output: Any


class ToolRegistry:
    """A singleton registry for tools.

    Features:
    - register tool
    - get tool by name
    - execute tool by name + args

    Learning note:
    Why a singleton?
    - For a learning scaffold, it avoids passing a registry object
      through many layers.
    - The orchestrator can simply import `registry` and use it.

    Where you would extend it later:
    - Validate `args` against `tool.input_schema` (JSON schema validation)
    - Keep tool versions / namespaces
    - Add async execution and timeouts for I/O heavy tools
    """

    _instance: "ToolRegistry | None" = None

    def __new__(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
        return cls._instance

    def register(self, tool: Tool) -> None:
        """Register (or overwrite) a tool by its `name`.

        Learning note:
        - The planner only knows `tool_name`.
        - `tool_name` must be stable and unique.
        - In this scaffold, we allow overwriting so you can re-run demos
          without clearing state manually.
        """
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        """Get tool instance by name.

        Raises:
            KeyError: if the tool was not registered.
        """
        if name not in self._tools:
            raise KeyError(f"Tool not registered: {name}")
        return self._tools[name]

    def list_tools(self) -> list[dict[str, Any]]:
        """Return tool definitions for prompting an LLM.

        The returned structure is embedded into the planner prompt so the LLM
        can follow each tool's JSON input/output conventions.
        """
        return [tool.as_function_definition() for tool in self._tools.values()]

    def execute(self, name: str, args: dict[str, Any]) -> ToolExecutionResult:
        """Execute a registered tool and return a structured wrapper.

        Why wrap?
        - It keeps tool output paired with tool_name.
        - The answerer step can log or format results consistently.
        """
        tool = self.get(name)
        output = tool.invoke(args)
        return ToolExecutionResult(tool_name=name, output=output)


# Global singleton accessor (import-friendly).
registry = ToolRegistry()

