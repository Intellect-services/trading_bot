"""Unit tests for the unified DataProvider."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from src.core.data_provider import DataProvider


class FakeBar:
    """Simple stand-in for MarketDataBar."""

    def __init__(self, *, close: float) -> None:
        self.close = close
        self.symbol = "AAPL"
        self.timeframe = "1Day"
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""

        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp.isoformat(),
            "open": self.close,
            "high": self.close,
            "low": self.close,
            "close": self.close,
            "volume": 1,
            "source": "cache",
        }


class DummyCache:
    """Deterministic cache behaviour for tests."""

    def __init__(self, bars: list[FakeBar] | None = None) -> None:
        self._bars = bars or []
        self.store_calls: int = 0

    def get_bars(self, **_) -> list[FakeBar]:
        return self._bars

    def store_bars(self, **_) -> None:
        self.store_calls += 1


class DummyYahoo:
    """Yahoo provider stub."""

    def __init__(self, payload: list[dict[str, Any]] | None = None) -> None:
        self.payload = payload or []
        self.calls = 0

    def get_historical_data(self, **_) -> list[dict[str, Any]]:
        self.calls += 1
        return self.payload


class DummyAlpha:
    """Alpha Vantage provider stub."""

    def __init__(self, payload: list[dict[str, Any]] | None = None) -> None:
        self.payload = payload or []
        self.calls = 0

    def is_configured(self) -> bool:
        return True

    def get_intraday_data(self, **_) -> list[dict[str, Any]]:
        self.calls += 1
        return self.payload


def test_provider_prefers_cache() -> None:
    """Cached bars should be returned before hitting external providers."""

    cache = DummyCache(bars=[FakeBar(close=123.0)])
    provider = DataProvider(
        alpaca_service=None,
        cache=cache,
        yahoo_provider=DummyYahoo(),
        alpha_provider=DummyAlpha(),
    )

    start = datetime.utcnow() - timedelta(days=1)
    bars = provider.get_historical_bars(symbol="AAPL", timeframe="1Day", start=start)

    assert len(bars) == 1
    assert bars[0]["close"] == 123.0


def test_provider_falls_back_to_yahoo() -> None:
    """When cache and Alpaca are empty, Yahoo Finance should provide data."""

    yahoo_payload = [
        {
            "timestamp": datetime.utcnow().isoformat(),
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 1000,
            "source": "yahoo",
        }
    ]
    provider = DataProvider(
        alpaca_service=None,
        cache=DummyCache(),
        yahoo_provider=DummyYahoo(payload=yahoo_payload),
        alpha_provider=DummyAlpha(),
    )

    start = datetime.utcnow() - timedelta(days=1)
    bars = provider.get_historical_bars(symbol="AAPL", timeframe="1Day", start=start)

    assert len(bars) == 1
    assert bars[0]["source"] == "yahoo"


def test_provider_uses_alpha_vantage_as_last_resort() -> None:
    """Alpha Vantage should be used only after other options."""

    alpha_payload = [
        {
            "timestamp": datetime.utcnow().isoformat(),
            "open": 50.0,
            "high": 55.0,
            "low": 49.0,
            "close": 54.0,
            "volume": 500,
            "source": "alpha_vantage",
        }
    ]
    provider = DataProvider(
        alpaca_service=None,
        cache=DummyCache(),
        yahoo_provider=DummyYahoo(payload=[]),
        alpha_provider=DummyAlpha(payload=alpha_payload),
    )

    start = datetime.utcnow() - timedelta(days=1)
    bars = provider.get_historical_bars(symbol="AAPL", timeframe="1Day", start=start)

    assert len(bars) == 1
    assert bars[0]["source"] == "alpha_vantage"
