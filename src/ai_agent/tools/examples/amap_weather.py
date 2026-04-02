"""AMap weather tool (returns raw weather JSON)."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote
from urllib import request

from ai_agent.config.settings import settings
from ai_agent.tools.base import Tool
from ai_agent.tools.schemas import object_schema, string_property


class AMapWeatherTool(Tool):
    name = "amap_weather"
    description = "Get weather information from AMap Weather API and return raw JSON."

    input_schema = object_schema(
        properties={
            "city": string_property("City name to query, e.g. Beijing or Guangzhou."),
            "extensions": string_property("AMap extensions parameter. Usually 'all'. Optional."),
        },
        required=["city"],
    )

    output_schema = object_schema(
        properties={
            "raw": {
                "type": "object",
                "description": "Raw JSON returned by AMap weatherInfo endpoint.",
            },
        },
        required=["raw"],
    )

    def run(self, args: dict[str, Any]) -> dict[str, Any]:
        """Tool entrypoint.

        This is the "I/O tool" example:
        - fetches data from an external HTTP API (AMap)
        - returns the raw JSON under key `raw`

        The planner/LLM can then decide how to summarize `raw`.
        """
        amap_cfg = settings.services.get("amap_weather", {})
        base_url = amap_cfg.get("base_url", "")
        api_key = amap_cfg.get("api_key", "")
        city = str(args.get("city", "")).strip()
        extensions = str(args.get("extensions") or "all")

        city_encoded = quote(city, safe="")
        url = (
            f"{base_url.rstrip('/')}/weatherInfo"
            f"?city={city_encoded}&extensions={extensions}&output=json&key={api_key}"
        )

        req = request.Request(url, method="GET", headers={"Content-Type": "application/json"})
        with request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        return {"raw": body}

