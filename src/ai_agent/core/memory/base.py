"""Memory abstraction interfaces and shared record models."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class MemoryRecord:
    """Normalized memory record used by both short/long memory backends."""

    record_id: str = field(default_factory=lambda: uuid4().hex)
    record_type: str = "generic"
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "record_type": self.record_type,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryRecord":
        return cls(
            record_id=str(data.get("record_id", uuid4().hex)),
            record_type=str(data.get("record_type", "generic")),
            content=str(data.get("content", "")),
            metadata=data.get("metadata", {}) if isinstance(data.get("metadata"), dict) else {},
            created_at=str(data.get("created_at", datetime.now(timezone.utc).isoformat())),
        )


class BaseMemory(ABC):
    """Unified memory protocol for interchangeable memory implementations."""

    @abstractmethod
    def add(self, record: MemoryRecord) -> None:
        """Write one memory record."""

    @abstractmethod
    def list_recent(self, limit: int = 10) -> list[MemoryRecord]:
        """Return recent records ordered from old to new."""

    @abstractmethod
    def search(self, query: str, limit: int = 5) -> list[MemoryRecord]:
        """Return records related to `query`."""

    @abstractmethod
    def clear(self) -> None:
        """Clear memory backend."""
