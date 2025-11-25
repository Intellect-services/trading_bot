"""Tests for MarketDataStreamer."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

import pytest

from src.core.data_cache import DataCache
from src.core.market_data_stream import MarketDataStreamer


class DummyWebSocket:
    """Fake websocket to capture subscriptions."""

    def __init__(self, **_: Any) -> None:
        self.started_with: list[str] | None = None
        self.callback: Callable[[dict], None] | None = None

    def start_market_stream(
        self,
        symbols: list[str],
        on_bar: Callable[[dict], None],
    ) -> None:
        self.started_with = symbols
        self.callback = on_bar

    def stop(self) -> None:
        self.started_with = []


class DummyService:
    api_key = "demo"
    secret_key = "demo"
    trading_mode = "paper"


@pytest.fixture()
def streamer(flask_app) -> MarketDataStreamer:
    """Instantiate a MarketDataStreamer with dummy websocket."""

    with flask_app.app_context():
        cache = DataCache()
        provider = type(
            "ProviderProxy",
            (),
            {"cache": cache},
        )()

        return MarketDataStreamer(
            alpaca_service=DummyService(),
            data_provider=provider,
            data_cache=cache,
            websocket_cls=lambda **kwargs: DummyWebSocket(**kwargs),
        )


def test_streamer_starts_subscription(streamer: MarketDataStreamer) -> None:
    """Streamer should request websocket subscriptions for provided symbols."""

    dummy_ws: DummyWebSocket = streamer.websocket_cls(
        api_key="x", secret_key="y", trading_mode="paper"
    )  # type: ignore[assignment]
    streamer._websocket = dummy_ws  # type: ignore[attr-defined]
    streamer.start(["AAPL", "msft"], timeframe="1Min")

    assert dummy_ws.started_with == ["AAPL", "MSFT"]


def test_streamer_persists_bar(streamer: MarketDataStreamer, flask_app) -> None:
    """Bar payloads should be stored via DataCache."""

    dummy_ws: DummyWebSocket = streamer.websocket_cls(
        api_key="x", secret_key="y", trading_mode="paper"
    )  # type: ignore[assignment]
    streamer._websocket = dummy_ws  # type: ignore[attr-defined]
    streamer.start(["AAPL"], timeframe="1Min")

    assert dummy_ws.callback is not None
    payload = {
        "T": "b",
        "S": "AAPL",
        "o": 100.0,
        "h": 101.0,
        "l": 99.5,
        "c": 100.5,
        "v": 1000,
        "t": datetime.utcnow().isoformat(),
        "i": "1Min",
    }
    dummy_ws.callback(payload)

    with flask_app.app_context():
        bars = streamer.data_cache.get_bars(symbol="AAPL", timeframe="1Min")
        assert len(bars) == 1
        assert bars[0].close == pytest.approx(100.5)
