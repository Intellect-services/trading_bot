"""Manage live market data streaming and caching."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import datetime

from src.core.alpaca_websocket import AlpacaWebSocket
from src.core.data_cache import DataCache
from src.core.data_provider import DataProvider

logger = logging.getLogger(__name__)


class MarketDataStreamer:
    """Subscribe to Alpaca WebSocket bars and persist them via DataCache."""

    def __init__(
        self,
        *,
        alpaca_service,
        data_provider: DataProvider,
        data_cache: DataCache | None = None,
        websocket_cls: type[AlpacaWebSocket] | None = None,
    ) -> None:
        self.alpaca_service = alpaca_service
        self.data_provider = data_provider
        self.data_cache = data_cache or data_provider.cache
        self.websocket_cls = websocket_cls or AlpacaWebSocket
        self._websocket: AlpacaWebSocket | None = None
        self._timeframe = "1Min"

    def start(self, symbols: Iterable[str], timeframe: str = "1Min") -> None:
        """Start streaming market data for the given symbols."""

        symbol_list = [symbol.upper() for symbol in symbols if symbol]
        if not symbol_list:
            logger.warning("MarketDataStreamer.start called with no symbols")
            return

        self._timeframe = timeframe or "1Min"
        if not self._websocket:
            self._websocket = self.websocket_cls(
                api_key=self.alpaca_service.api_key,
                secret_key=self.alpaca_service.secret_key,
                trading_mode=getattr(self.alpaca_service, "trading_mode", "paper"),
            )

        self._websocket.start_market_stream(symbol_list, self._handle_bar)
        logger.info(
            "Market data streaming started for %s (timeframe %s)",
            ", ".join(symbol_list),
            self._timeframe,
        )

    def stop(self) -> None:
        """Stop streaming."""

        if self._websocket:
            self._websocket.stop()
            self._websocket = None
            logger.info("Market data streaming stopped")

    # ------------------------------------------------------------------ #
    # Internal handlers
    # ------------------------------------------------------------------ #
    def _handle_bar(self, payload: dict) -> None:
        """Persist streamed bars into the cache."""

        symbol = payload.get("S")
        if not symbol or not self.data_cache:
            return

        timestamp_value = payload.get("t")
        if isinstance(timestamp_value, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp_value).isoformat()
        elif isinstance(timestamp_value, str):
            timestamp = timestamp_value.replace("Z", "+00:00")
        else:
            timestamp = datetime.utcnow().isoformat()

        bar = {
            "timestamp": timestamp,
            "open": float(payload.get("o", 0.0)),
            "high": float(payload.get("h", 0.0)),
            "low": float(payload.get("l", 0.0)),
            "close": float(payload.get("c", 0.0)),
            "volume": float(payload.get("v", 0.0)),
            "source": "alpaca_stream",
        }
        self.data_cache.store_bars(
            symbol=symbol,
            timeframe=payload.get("i", self._timeframe),
            bars=[bar],
            source="alpaca_stream",
        )
