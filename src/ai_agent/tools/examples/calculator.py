"""Calculator tool (safe arithmetic evaluation)."""

from __future__ import annotations

import ast
import operator
from typing import Any

from ai_agent.tools.base import Tool
from ai_agent.tools.schemas import number_property, object_schema, string_property


def _normalize_expression(expr: str) -> str:
    """Normalize an expression into a Python-like arithmetic string.

    Learning rationale:
    LLM outputs can vary in symbols:
    - "×" or "x" -> "*"
    - "^" -> "**" (Python exponent)
    This function reduces that variance before AST parsing.
    """
    expr = expr.strip()
    expr = expr.replace("×", "*").replace("x", "*")
    # Some LLMs may output '^' for power; convert it to Python '**'.
    if "^" in expr:
        expr = expr.replace("^", "**")
    return expr


def _safe_eval_arithmetic(expr: str) -> float:
    """Safely evaluate arithmetic using Python AST (no eval()).

    Why AST:
    - It parses the expression into a syntax tree.
    - We only allow a small set of operators.
    - Any unsupported node type raises an error.
    """
    allowed_bin_ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv,
    }
    allowed_unary_ops = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    def eval_node(node: ast.AST) -> float:
        # Recursively evaluate only supported AST node types.
        if isinstance(node, ast.Expression):
            return eval_node(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in allowed_bin_ops:
            fn = allowed_bin_ops[type(node.op)]
            return fn(eval_node(node.left), eval_node(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in allowed_unary_ops:
            fn = allowed_unary_ops[type(node.op)]
            return fn(eval_node(node.operand))
        # Reject everything else (names, attributes, function calls, etc.).
        raise ValueError("Unsupported expression")

    expr = _normalize_expression(expr)
    tree = ast.parse(expr, mode="eval")
    return eval_node(tree)


class CalculatorTool(Tool):
    name = "calculator"
    description = "Evaluate a simple arithmetic expression and return its numeric result."

    input_schema = object_schema(
        properties={
            "expression": string_property(
                'Arithmetic expression using operators like +, -, *, /, %, **, parentheses. Example: "3**5".'
            )
        },
        required=["expression"],
    )

    output_schema = object_schema(
        properties={"result": number_property("Computed numeric result.")},
        required=["result"],
    )

    def run(self, args: dict[str, Any]) -> dict[str, Any]:
        """Tool entrypoint.

        Args schema expects:
            { "expression": "<arithmetic expression>" }

        Returns:
            { "result": <number> }
        """
        expression = str(args.get("expression", "")).strip()
        result = _safe_eval_arithmetic(expression)
        # Convert near-integers to int for nicer outputs.
        if abs(result - round(result)) < 1e-9:
            result = float(round(result))
        return {"result": result}

