"""JSON Schema helpers used by tools and function-calling demos."""

from __future__ import annotations

from typing import Any


def object_schema(properties: dict[str, dict[str, Any]], required: list[str]) -> dict[str, Any]:
    """Build a minimal JSON schema for a JSON object.

    Learning design:
    - We intentionally keep the schema small.
    - Tools use `input_schema`/`output_schema` to help the planner
      generate correct argument shapes.
    - `additionalProperties=False` discourages unknown fields.
    """
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def string_property(description: str) -> dict[str, Any]:
    return {"type": "string", "description": description}


def number_property(description: str) -> dict[str, Any]:
    # Use "number" so both int and float are accepted.
    return {"type": "number", "description": description}


def boolean_property(description: str) -> dict[str, Any]:
    return {"type": "boolean", "description": description}

