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

    CN: Tool 用于让 LLM 以“请求工具”的方式获得能力（如计算、查询等）。
    你需要关注的关键点：
    - name / description：供 planner 选择工具使用
    - input_schema / output_schema：约束 planner 如何组织 arguments，以及工具返回应该是什么结构
    - run(args)：执行工具；args 已经是 JSON 解析后的 dict
    - 真实系统里通常会校验 args 与 input_schema，并校验输出结构是否符合 output_schema
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

        CN:
        - args 是已经被 JSON 解析后的参数 dict，不是用户原始文本
        - 返回值必须能被 JSON 序列化，才能继续被后续步骤（提示/日志/最终回答）使用
        """

    def invoke(self, args: dict[str, Any]) -> Any:
        """Invoke tool (a small wrapper around `run`).

        We keep this method so future orchestration layers can hook in
        cross-cutting concerns (logging, metrics, retries) without touching Tool implementations.

        CN:
        - invoke() 是 run() 的薄封装
        - 后续如果你要加日志/重试/指标，只需要在这里动，不要改工具本身
        """
        return self.run(args)

    @classmethod
    def as_function_definition(cls) -> dict[str, Any]:
        """Return a tool definition payload suitable for prompting an LLM.

        The demo uses an LLM planner that reads this definition and chooses:
        - tool_name
        - arguments (must match the schema descriptions)

        CN:
        这个方法把工具的元信息和 schemas 组合成 planner 可读的结构。
        规划器会根据它生成 arguments，然后调用 run(args)。
        """
        return {
            "name": cls.name,
            "description": cls.description,
            "input_schema": cls.input_schema,
            "output_schema": cls.output_schema,
        }

