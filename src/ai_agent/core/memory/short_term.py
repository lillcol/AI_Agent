"""In-memory short-term conversation memory with pruning."""

from __future__ import annotations

from ai_agent.core.memory.base import BaseMemory, MemoryRecord


class ShortTermMemory(BaseMemory):
    """Simple list-based short-term memory for the current session."""

    def __init__(self, max_records: int = 30, max_chars: int = 6000) -> None:
        # max_records: hard cap by record count.
        # max_chars: soft budget to avoid context blow-up in prompts.
        self.max_records = max_records
        self.max_chars = max_chars
        self._records: list[MemoryRecord] = []

    def add(self, record: MemoryRecord) -> None:
        self._records.append(record)
        self._prune()

    def _total_chars(self) -> int:
        return sum(len(r.content) for r in self._records)

    def _prune(self) -> None:
        # Two-stage pruning:
        # 1) trim by max record count
        # 2) trim by total character budget (drop oldest first)
        if len(self._records) > self.max_records:
            overflow = len(self._records) - self.max_records
            self._records = self._records[overflow:]
        while self._records and self._total_chars() > self.max_chars:
            self._records.pop(0)

    def list_recent(self, limit: int = 10) -> list[MemoryRecord]:
        if limit <= 0:
            return []
        return self._records[-limit:]

    def search(self, query: str, limit: int = 5) -> list[MemoryRecord]:
        if not query.strip() or limit <= 0:
            return []
        q = query.lower()
        hits = [record for record in self._records if q in record.content.lower()]
        return hits[-limit:]

    def clear(self) -> None:
        self._records.clear()
