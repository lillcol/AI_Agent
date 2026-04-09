"""Weather demo: AMap query + DeepSeek natural-language summary.

Goals:
1) Learn how to call a third-party HTTP API (AMap weather).
2) Learn how to pass structured JSON to an LLM for readable summarization.
3) Learn a minimal two-step flow: data retrieval -> LLM summary.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import sys
from pathlib import Path
from urllib import request
from urllib.parse import quote

if __package__ is None or __package__ == "":
    # Keep imports working when running this file directly:
    # python src/ai_agent/learning/stage_01_native_llm/weather_info_demo.py
    #
    # Current file path:
    # .../AI_Agent/src/ai_agent/learning/stage_01_native_llm/weather_info_demo.py
    # parents[3] points to .../AI_Agent/src
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from ai_agent.config.settings import settings
from ai_agent.core.llm.factory import build_deepseek_client


@dataclass
class WeatherClient:
    """AMap weather API client.

    Single responsibility: fetch raw weather JSON only.
    """

    base_url: str
    api_key: str
    timeout: int = 60

    def get_weather_info(self, city_name: str) -> dict:
        """Fetch AMap weather JSON by city name.

        Args:
            city_name: City name, e.g. "Beijing" / "Xingning".

        Returns:
            dict: Raw JSON dictionary returned by AMap API.
        """
        # City names may contain non-ASCII chars, so URL encoding is required.
        city_encoded = quote(city_name, safe="")

        # Notes:
        # - weatherInfo: AMap weather endpoint path
        # - extensions=all: include forecast data
        # - output=json: JSON output format
        # - key: your AMap key from private.local.yaml
        url = (
            f"{self.base_url.rstrip('/')}/weatherInfo"
            f"?city={city_encoded}&extensions=all&output=json&key={self.api_key}"
        )

        # Use urllib here as a minimal HTTP GET example.
        req = request.Request(
            url,
            method="GET",
            headers={
                "Content-Type": "application/json",
            },
        )

        # Decode response body into JSON.
        with request.urlopen(req, timeout=self.timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body


def summarize_weather_with_llm(weather_info: dict) -> str:
    """Use shared DeepSeek client to summarize weather JSON."""
    llm_client = build_deepseek_client()
    user_query = (
        "请将下面天气 JSON 解析为简洁自然语言，"
        "包含当前时间、省市信息、天气、温度范围、风向风力等出行关键信息；"
        "如果有未来几天天气，请补充一句趋势；不要输出思考过程。\n\n"
        + json.dumps(weather_info, ensure_ascii=False)
    )
    return llm_client.chat(user_query)


def main(city: str | None = None) -> None:
    """Program entrypoint: weather query -> LLM summary."""
    # 1) Read service config from centralized settings (AMap + DeepSeek).
    amap_cfg = settings.services.get("amap_weather", {})
    # 2) Initialize weather client.
    weather_client = WeatherClient(
        base_url=amap_cfg.get("base_url", ""),
        api_key=amap_cfg.get("api_key", ""),
    )

    # 3) City source:
    # - Prefer CLI args (supports spaces)
    # - Fallback default: "Beijing"
    cli_city = " ".join(sys.argv[1:]).strip()
    city_name = city or cli_city or "北京"

    # 4) Fetch raw weather JSON from AMap.
    weather_info = weather_client.get_weather_info(city_name)

    # 5) Send JSON to DeepSeek and get a concise summary.
    summary = summarize_weather_with_llm(weather_info)

    # 6) Print final result.
    print(summary)


if __name__ == "__main__":
    main()
