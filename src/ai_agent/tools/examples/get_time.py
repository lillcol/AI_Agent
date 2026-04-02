"""Get current time tool."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from ai_agent.tools.base import Tool
from ai_agent.tools.schemas import boolean_property, object_schema, string_property


class GetTimeTool(Tool):
    name = "get_time"
    description = "Get the current time."

    input_schema = object_schema(
        properties={
            "timezone": string_property("IANA timezone name, e.g. Asia/Shanghai. Default: Asia/Shanghai."),
            "iso": boolean_property("Whether to return ISO 8601 string. Default: true."),
        },
        required=[],
    )

    output_schema = object_schema(
        properties={
            "timezone": string_property("Resolved timezone."),
            "time": string_property("Time string representation."),
        },
        required=["timezone", "time"],
    )

    def run(self, args: dict[str, Any]) -> dict[str, Any]:
        """Tool entrypoint.

        Inputs (per input_schema):
        - timezone: IANA timezone string
        - iso: whether to return ISO 8601 format

        Output (per output_schema):
        - timezone
        - time
        """
        timezone = str(args.get("timezone") or "Asia/Shanghai")
        iso = bool(args.get("iso", True))

        now = datetime.now(ZoneInfo(timezone))
        time_str = now.isoformat() if iso else now.strftime("%Y-%m-%d %H:%M:%S")

        return {"timezone": timezone, "time": time_str}

