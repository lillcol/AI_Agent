"""AMap weather HTTP client shared by demos and tools."""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import request
from urllib.parse import quote


@dataclass
class AMapWeatherClient:
    """Minimal AMap weather API client (raw JSON response)."""

    base_url: str
    api_key: str
    timeout: int = 60

    def query_weather(self, city: str, extensions: str = "all") -> dict:
        city_encoded = quote(city, safe="")
        url = (
            f"{self.base_url.rstrip('/')}/weatherInfo"
            f"?city={city_encoded}&extensions={extensions}&output=json&key={self.api_key}"
        )
        req = request.Request(url, method="GET", headers={"Content-Type": "application/json"})
        with request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

