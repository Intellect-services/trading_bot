"""Yahoo Finance data provider (no API key required)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

import pandas as pd
import yfinance as yf


class YahooFinanceProvider:
    """Fetch historical market data from Yahoo Finance."""

    INTERVAL_MAP: ClassVar[dict[str, str]] = {
        "1Min": "1m",
        "5Min": "5m",
        "15Min": "15m",
        "30Min": "30m",
        "1Hour": "60m",
        "1Day": "1d",
        "1Week": "1wk",
        "1Month": "1mo",
    }

    def get_historical_data(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch OHLCV data for the requested period."""

        interval = self.INTERVAL_MAP.get(timeframe, "1d")
        ticker = yf.Ticker(symbol)
        hist = ticker.history(interval=interval, start=start, end=end)
        if hist.empty:
            return []

        if limit is not None:
            hist = hist.tail(limit)

        hist = hist.reset_index()
        date_column = hist.columns[0]
        if date_column != "Date":
            hist = hist.rename(columns={date_column: "Date"})
        records: list[dict[str, Any]] = []
        for row in hist.to_dict("records"):
            timestamp = (
                row["Date"] if isinstance(row["Date"], datetime) else pd.to_datetime(row["Date"])
            )
            records.append(
                {
                    "timestamp": timestamp.isoformat(),
                    "open": float(row.get("Open", 0.0)),
                    "high": float(row.get("High", 0.0)),
                    "low": float(row.get("Low", 0.0)),
                    "close": float(row.get("Close", 0.0)),
                    "volume": float(row.get("Volume", 0.0)),
                    "source": "yahoo",
                }
            )
        return records
