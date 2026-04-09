"""Small JSON extraction helpers for LLM outputs."""

from __future__ import annotations


def extract_first_json_object(text: str) -> str:
    """Extract the first balanced JSON object substring from free text."""
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

