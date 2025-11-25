"""Unit tests for AlpacaWebSocket internals."""

from __future__ import annotations

import json

from src.core.alpaca_websocket import AlpacaWebSocket


class DummySocket:
    """Capture payloads sent to websocket."""

    def __init__(self) -> None:
        self.sent: list[dict] = []
        self.closed = False

    def send(self, payload: str) -> None:
        self.sent.append(json.loads(payload))

    def close(self) -> None:
        self.closed = True


def test_websocket_authentication_triggers_subscribe(monkeypatch) -> None:
    """Authentication success should mark stream ready and subscribe."""

    ws = AlpacaWebSocket(api_key="key", secret_key="secret")
    dummy = DummySocket()
    ws._market_ws = dummy  # type: ignore[attr-defined]
    ws._market_symbols = {"AAPL", "MSFT"}  # type: ignore[attr-defined]
    ws._on_market_message(None, '[{"T":"success","msg":"authenticated"}]')

    assert ws._market_ready.is_set()
    assert dummy.sent[0]["bars"] == ["AAPL", "MSFT"]


def test_websocket_bar_event_calls_callback() -> None:
    """Bar events should forward payload to callback."""

    captured: list[dict] = []
    ws = AlpacaWebSocket(api_key="key", secret_key="secret")
    ws._market_on_bar = captured.append  # type: ignore[attr-defined]
    ws._on_market_message(None, '[{"T":"b","S":"AAPL","o":1,"h":1,"l":1,"c":1,"v":1}]')

    assert captured[0]["S"] == "AAPL"


def test_websocket_on_open_sends_auth() -> None:
    """Opening the connection should immediately send auth payload."""

    ws = AlpacaWebSocket(api_key="demo", secret_key="secret")
    dummy = DummySocket()
    ws._on_market_open(dummy)  # type: ignore[arg-type]

    assert dummy.sent[0]["action"] == "auth"
