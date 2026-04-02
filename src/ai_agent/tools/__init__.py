"""Tooling layer.

This package provides:
- Tool protocol base class
- JSON Schema helpers
- Tool registry (singleton)
- LLM function-calling orchestration utilities
"""

from ai_agent.tools.base import Tool
from ai_agent.tools.function_calling import FunctionCallingOrchestrator
from ai_agent.tools.registry import ToolExecutionResult, ToolRegistry, registry

__all__ = [
    "Tool",
    "FunctionCallingOrchestrator",
    "ToolExecutionResult",
    "ToolRegistry",
    "registry",
]

