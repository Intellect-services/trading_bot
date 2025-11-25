"""Lightweight Alpaca WebSocket client for free-tier streaming."""

from __future__ import annotations

import json
import logging
import threading
from collections.abc import Callable, Iterable

import websocket

logger = logging.getLogger(__name__)


class AlpacaWebSocket:
    """Manage Alpaca streaming connections for market data."""

    MARKET_STREAMS = {
        "paper": "wss://stream.data.alpaca.markets/v2/iex",
        "live": "wss://stream.data.alpaca.markets/v2/sip",
    }

    def __init__(
        self,
        *,
        api_key: str,
        secret_key: str,
        trading_mode: str = "paper",
    ) -> None:
        self.api_key = api_key
        self.secret_key = secret_key
        self.trading_mode = trading_mode

        self._market_ws: websocket.WebSocketApp | None = None
        self._market_thread: threading.Thread | None = None
        self._market_ready = threading.Event()
        self._market_on_bar: Callable[[dict], None] | None = None
        self._market_symbols: set[str] = set()
        self._stop_event = threading.Event()

    # --------------------------------------------------------------------- #
    # Market data stream
    # --------------------------------------------------------------------- #
    def start_market_stream(
        self,
        symbols: Iterable[str],
        on_bar: Callable[[dict], None],
    ) -> None:
        """Start (or update) the market data stream with bar subscriptions."""

        clean_symbols = {symbol.upper() for symbol in symbols if symbol}
        if not clean_symbols:
            logger.warning("No symbols provided for market stream")
            return

        self._market_symbols |= clean_symbols
        self._market_on_bar = on_bar

        if self._market_thread and self._market_thread.is_alive():
            self._send_market_subscribe()
            return

        stream_url = self.MARKET_STREAMS.get(self.trading_mode, self.MARKET_STREAMS["paper"])
        self._stop_event.clear()
        self._market_ws = websocket.WebSocketApp(
            stream_url,
            on_open=self._on_market_open,
            on_message=self._on_market_message,
            on_error=self._on_market_error,
            on_close=self._on_market_close,
        )
        self._market_thread = threading.Thread(
            target=self._market_ws.run_forever,
            kwargs={"ping_interval": 20, "ping_timeout": 10},
            daemon=True,
            name="alpaca-market-ws",
        )
        self._market_thread.start()

    def stop(self) -> None:
        """Stop all websocket activity."""

        self._stop_event.set()
        if self._market_ws:
            try:
                self._market_ws.close()
            except Exception as exc:  # pragma: no cover - best effort
                logger.debug("Error closing market websocket: %s", exc)
        if self._market_thread and self._market_thread.is_alive():
            self._market_thread.join(timeout=2)
        self._market_ws = None
        self._market_thread = None
        self._market_ready.clear()

    # ------------------------------------------------------------------ #
    # Internal handlers
    # ------------------------------------------------------------------ #
    def _on_market_open(self, ws: websocket.WebSocketApp) -> None:
        logger.info("Alpaca market stream connected")
        auth_payload = {"action": "auth", "key": self.api_key, "secret": self.secret_key}
        ws.send(json.dumps(auth_payload))

    def _on_market_message(self, _ws: websocket.WebSocketApp, message: str) -> None:
        try:
            events = json.loads(message)
        except json.JSONDecodeError:
            logger.warning("Failed to decode websocket payload: %s", message)
            return

        if not isinstance(events, list):
            events = [events]

        for event in events:
            event_type = event.get("T")
            if event_type == "success" and event.get("msg") == "authenticated":
                logger.info("Alpaca market stream authenticated")
                self._market_ready.set()
                self._send_market_subscribe()
            elif event_type == "subscription":
                logger.debug("Market stream subscription confirmed: %s", event)
            elif event_type == "b" and self._market_on_bar:
                self._market_on_bar(event)
            elif event_type == "error":
                logger.error("Market stream error: %s", event)

    def _on_market_error(self, _ws: websocket.WebSocketApp, error: Exception) -> None:
        if self._stop_event.is_set():
            return
        logger.error("Alpaca market stream error: %s", error)

    def _on_market_close(self, _ws: websocket.WebSocketApp, code: int, msg: str) -> None:
        logger.warning("Alpaca market stream closed (%s): %s", code, msg)
        self._market_ready.clear()
        self._market_thread = None
        self._market_ws = None
        if not self._stop_event.is_set():
            logger.info("Attempting to reconnect Alpaca market stream")
            callback = self._market_on_bar or (lambda *_: None)
            self.start_market_stream(self._market_symbols, callback)

    def _send_market_subscribe(self) -> None:
        if not self._market_ws or not self._market_ready.is_set():
            return
        if not self._market_symbols:
            return

        payload = {"action": "subscribe", "bars": sorted(self._market_symbols)}
        try:
            self._market_ws.send(json.dumps(payload))
            logger.info("Subscribed to market bars: %s", ", ".join(sorted(self._market_symbols)))
        except Exception as exc:  # pragma: no cover - best effort
            logger.error("Failed to send subscribe payload: %s", exc)
