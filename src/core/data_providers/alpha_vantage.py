"""Alpha Vantage data provider (free tier)."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import logging
import requests

logger = logging.getLogger(__name__)


class AlphaVantageProvider:
    """Fetch historical data from Alpha Vantage using the free tier."""

    BASE_URL = "https://www.alphavantage.co/query"
    INTERVAL_MAP: dict[str, str] = {
        "1Min": "1min",
        "5Min": "5min",
        "15Min": "15min",
        "30Min": "30min",
        "1Hour": "60min",
        "1Day": "daily",
    }

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")

    def is_configured(self) -> bool:
        """Return True if an API key is available."""

        return bool(self.api_key)

    def get_intraday_data(
        self,
        *,
        symbol: str,
        timeframe: str,
        limit: int | None = 100,
    ) -> list[dict[str, Any]]:
        """Fetch intraday data."""

        if not self.is_configured():
            return []

        interval = self.INTERVAL_MAP.get(timeframe, "5min")
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": interval,
            "outputsize": "compact",
            "apikey": self.api_key,
        }
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            logger.warning("Alpha Vantage request failed: %s", exc)
            return []
        time_series = data.get(f"Time Series ({interval})", {})
        bars: list[dict[str, Any]] = []
        for timestamp_str, values in list(time_series.items())[: limit or 100]:
            timestamp = datetime.fromisoformat(timestamp_str)
            bars.append(
                {
                    "timestamp": timestamp.isoformat(),
                    "open": float(values.get("1. open", 0.0)),
                    "high": float(values.get("2. high", 0.0)),
                    "low": float(values.get("3. low", 0.0)),
                    "close": float(values.get("4. close", 0.0)),
                    "volume": float(values.get("5. volume", 0.0)),
                    "source": "alpha_vantage",
                }
            )
        return bars
