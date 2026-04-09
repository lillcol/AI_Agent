"""File-based long-term memory backend (JSONL)."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from ai_agent.core.memory.base import BaseMemory, MemoryRecord


class LongTermMemoryFile(BaseMemory):
    """Persistent long-term memory stored as JSON lines."""

    def __init__(self, file_path: Path | None = None) -> None:
        default_path = Path("logs") / "memory" / "long_term_memory.jsonl"
        self.file_path = file_path or default_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text("", encoding="utf-8")

    def _read_all(self) -> list[MemoryRecord]:
        records: list[MemoryRecord] = []
        text = self.file_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                records.append(MemoryRecord.from_dict(obj))
        return records

    @staticmethod
    def _normalize(text: str) -> str:
        # Minimal normalization for stable dedup keys.
        return " ".join(text.lower().strip().split())

    def _dedup_key(self, record: MemoryRecord) -> str:
        topic = str(record.metadata.get("topic", ""))
        raw = f"{self._normalize(topic)}||{self._normalize(record.content)}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()

    def add(self, record: MemoryRecord) -> None:
        # Skip duplicate long-term knowledge to reduce noisy accumulation.
        existing = self._read_all()
        current_key = self._dedup_key(record)
        for item in existing:
            if self._dedup_key(item) == current_key:
                logging.getLogger("memory_react_agent").info(
                    "Long-term memory dedup hit | topic=%s | skip write.",
                    str(record.metadata.get("topic", "general")),
                )
                return
        with self.file_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    def list_recent(self, limit: int = 10) -> list[MemoryRecord]:
        if limit <= 0:
            return []
        return self._read_all()[-limit:]

    def search(self, query: str, limit: int = 5) -> list[MemoryRecord]:
        if not query.strip() or limit <= 0:
            return []
        tokens = [token.lower() for token in query.split() if token.strip()]
        records = self._read_all()
        if not tokens:
            return records[-limit:]

        scored: list[tuple[int, MemoryRecord]] = []
        for record in records:
            text = (record.content + " " + json.dumps(record.metadata, ensure_ascii=False)).lower()
            score = sum(1 for token in tokens if token in text)
            if score > 0:
                scored.append((score, record))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [record for _, record in scored[:limit]]

    def clear(self) -> None:
        self.file_path.write_text("", encoding="utf-8")
