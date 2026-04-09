"""Interactive CLI loop helpers."""

from __future__ import annotations

from collections.abc import Callable


def run_repl(
    *,
    intro: str,
    input_prompt: str,
    exit_commands: set[str],
    clear_commands: set[str],
    on_message: Callable[[str], str],
    on_clear: Callable[[], None] | None = None,
) -> None:
    """Run a minimal REPL loop with optional clear command hook."""
    print(intro)
    while True:
        q = input(input_prompt).strip()
        if not q:
            continue
        q_lower = q.lower()
        if q_lower in exit_commands:
            break
        if q_lower in clear_commands:
            if on_clear is not None:
                on_clear()
            continue
        answer = on_message(q)
        print(answer)

