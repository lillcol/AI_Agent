"""Tool protocol base classes.

This repo is a learning scaffold, so the goal here is:
- define a small, explicit Tool interface
- standardize tool metadata (name/description) and JSON Schema for inputs/outputs
- make tool invocation consistent across demos
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

ToolInputSchema = dict[str, Any]
ToolOutputSchema = dict[str, Any]


class Tool(ABC):
    """Abstract base class for all tools.

    A Tool is a small, self-contained capability that the LLM can request.

    Learning-oriented contract (keep it simple and explicit):
    - Tools expose metadata: `name`, `description`
    - Tools expose JSON Schemas for:
      - `input_schema`: how the planner should structure arguments
      - `output_schema`: what shape the tool returns
    - Tools implement `run(args)`:
      - `args` is already a parsed dict (produced by our JSON parser)
      - return value must be JSON-serializable so it can be embedded in LLM prompts

    Learning note:
    This scaffold keeps the demo intentionally small and focuses on the control flow:
    planner JSON -> registry execute -> tool result -> final answer.

    In production, you would typically validate inputs against `input_schema`
    and enforce/validate the returned structure against `output_schema`.

    """

    name: ClassVar[str]
    description: ClassVar[str]
    input_schema: ClassVar[ToolInputSchema]
    output_schema: ClassVar[ToolOutputSchema]

    @abstractmethod
    def run(self, args: dict[str, Any]) -> Any:
        """Execute the tool.

        Args:
            args: JSON-parsed arguments. This is NOT raw text.

        Returns:
            Any JSON-serializable object (dict/list/str/number/bool).
        """

    def invoke(self, args: dict[str, Any]) -> Any:
        """Invoke tool (a small wrapper around `run`).

        We keep this method so future orchestration layers can hook in
        cross-cutting concerns (logging, metrics, retries) without touching Tool implementations.
        """
        return self.run(args)

    @classmethod
    def as_function_definition(cls) -> dict[str, Any]:
        """Return a tool definition payload suitable for prompting an LLM.

        The demo uses an LLM planner that reads this definition and chooses:
        - tool_name
        - arguments (must match the schema descriptions)
        """
        return {
            "name": cls.name,
            "description": cls.description,
            "input_schema": cls.input_schema,
            "output_schema": cls.output_schema,
        }

