"""Memory manager that orchestrates short-term and long-term memories."""

from __future__ import annotations

from typing import Any

from ai_agent.core.memory.base import MemoryRecord
from ai_agent.core.memory.long_term_file import LongTermMemoryFile
from ai_agent.core.memory.short_term import ShortTermMemory


class MemoryManager:
    """One-stop API for writing and recalling memory."""

    def __init__(
        self,
        short_term: ShortTermMemory | None = None,
        long_term: LongTermMemoryFile | None = None,
    ) -> None:
        self.short_term = short_term or ShortTermMemory()
        self.long_term = long_term or LongTermMemoryFile()

    def add_short_message(self, role: str, content: str, metadata: dict[str, Any] | None = None) -> None:
        record = MemoryRecord(
            record_type="conversation",
            content=content,
            metadata={"role": role, **(metadata or {})},
        )
        self.short_term.add(record)

    def add_tool_result(self, tool_name: str, arguments: dict[str, Any], output: dict[str, Any]) -> None:
        self.short_term.add(
            MemoryRecord(
                record_type="tool_result",
                content=f"{tool_name} -> {output}",
                metadata={"tool_name": tool_name, "arguments": arguments, "output": output},
            )
        )

    def remember_knowledge(self, topic: str, content: str, tags: list[str] | None = None) -> None:
        # Long-term backend performs dedup (topic + content normalized hash).
        self.long_term.add(
            MemoryRecord(
                record_type="knowledge",
                content=content,
                metadata={"topic": topic, "tags": tags or []},
            )
        )

    def recall_short(self, limit: int = 8) -> list[MemoryRecord]:
        return self.short_term.list_recent(limit=limit)

    def recall_short_hybrid(self, query: str, recent_limit: int = 6, relevant_limit: int = 4) -> list[MemoryRecord]:
        """Recall short memory using hybrid strategy.

        Why:
        - recent records keep local conversational continuity
        - relevance hits reduce unrelated history pollution
        """
        recent = self.short_term.list_recent(limit=recent_limit)
        relevant = self.short_term.search(query=query, limit=relevant_limit)

        # Dedup while preserving order; use record_id to keep stable identity.
        seen: set[str] = set()
        merged: list[MemoryRecord] = []
        for record in [*relevant, *recent]:
            if record.record_id in seen:
                continue
            seen.add(record.record_id)
            merged.append(record)
        return merged

    def recall_long(self, query: str, limit: int = 3) -> list[MemoryRecord]:
        return self.long_term.search(query=query, limit=limit)

    def format_short_context(self, query: str = "", limit: int = 8) -> str:
        # For query-aware prompting, prefer hybrid recall to reduce stale context.
        if query.strip():
            records = self.recall_short_hybrid(query=query, recent_limit=limit, relevant_limit=max(2, limit // 2))
        else:
            records = self.recall_short(limit=limit)
        if not records:
            return "(empty)"
        lines: list[str] = []
        for r in records:
            role = str(r.metadata.get("role", r.record_type))
            lines.append(f"- [{role}] {r.content}")
        return "\n".join(lines)

    def format_long_context(self, query: str, limit: int = 3) -> str:
        records = self.recall_long(query=query, limit=limit)
        if not records:
            return "(empty)"
        lines: list[str] = []
        for r in records:
            topic = str(r.metadata.get("topic", "general"))
            lines.append(f"- [{topic}] {r.content}")
        return "\n".join(lines)

    def clear_short(self) -> None:
        """Reset short-term memory for a new clean session."""
        self.short_term.clear()
