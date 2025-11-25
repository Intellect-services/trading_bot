"""Unit tests for AlpacaService request handling."""

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import patch

import pytest

from src.core.alpaca_service import AlpacaService
from src.core.alpaca_types import OrderSide, OrderType, TimeInForce


@pytest.fixture()
def service() -> AlpacaService:
    """Create an AlpacaService instance without real HTTP calls."""
    with patch.object(AlpacaService, "_request", return_value={"id": "account"}):
        return AlpacaService(api_key="demo", secret_key="demo")


def test_get_account_formats_numeric_fields(
    service: AlpacaService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Account payload should be normalized to floats/bools."""
    payload = {
        "cash": "1000",
        "portfolio_value": "2000",
        "buying_power": "4000",
        "initial_margin": "50",
        "maintenance_margin": "25",
        "daytrading_buying_power": "8000",
        "equity": "2500",
        "last_equity": "2400",
        "multiplier": "2",
        "shorting_enabled": True,
        "pattern_day_trader": False,
        "trading_blocked": False,
        "transfers_blocked": False,
        "account_blocked": False,
        "currency": "USD",
    }

    monkeypatch.setattr(service, "_request", lambda method, path, **_: payload)
    account = service.get_account()

    assert account["cash"] == 1000.0
    assert account["buying_power"] == 4000.0
    assert account["shorting_enabled"] is True
    assert account["pattern_day_trader"] is False


def test_get_positions_normalizes_values(
    service: AlpacaService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Positions endpoint should convert numeric strings to floats."""
    payload = [
        {
            "symbol": "AAPL",
            "qty": "10",
            "avg_entry_price": "150",
            "market_value": "1500",
            "unrealized_pl": "100",
            "current_price": "151",
            "lastday_price": "149",
            "change_today": "0.0134",
        }
    ]

    monkeypatch.setattr(service, "_request", lambda method, path, **_: payload)
    positions = service.get_positions()

    assert positions[0]["symbol"] == "AAPL"
    assert positions[0]["qty"] == 10.0
    assert positions[0]["market_value"] == 1500.0


def test_submit_order_builds_payload(
    service: AlpacaService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """submit_order should serialize enums and optional fields."""
    captured: dict[str, dict] = {}

    def fake_request(method, path, *, body=None, **kwargs):
        captured["method"] = method
        captured["path"] = path
        captured["body"] = body
        return {"id": "order123"}

    monkeypatch.setattr(service, "_request", fake_request)
    order = service.submit_order(
        symbol="AAPL",
        qty=5,
        side=OrderSide.BUY,
        type=OrderType.LIMIT,
        time_in_force=TimeInForce.DAY,
        limit_price=150.5,
        stop_price=None,
    )

    assert order["id"] == "order123"
    assert captured["method"] == "POST"
    assert captured["path"] == "/orders"
    assert captured["body"]["qty"] == 5
    assert captured["body"]["limit_price"] == 150.5
    assert captured["body"]["side"] == "buy"


def test_get_bars_converts_payload(service: AlpacaService, monkeypatch: pytest.MonkeyPatch) -> None:
    """get_bars should reshape the response into dict-of-lists format."""
    response = {
        "bars": [
            {"o": 100, "h": 105, "l": 99, "c": 104, "v": 1000, "t": "2024-01-01T00:00:00Z"},
            {"o": 104, "h": 106, "l": 101, "c": 102, "v": 900, "t": "2024-01-02T00:00:00Z"},
        ]
    }
    monkeypatch.setattr(service, "_request", lambda *args, **kwargs: response)

    start = datetime.now(timezone.utc) - timedelta(days=2)
    bars = service.get_bars("AAPL", "1Day", start=start)

    assert "AAPL" in bars
    assert len(bars["AAPL"]) == 2
    assert bars["AAPL"][0]["open"] == 100.0
    assert bars["AAPL"][0]["timestamp"] == "2024-01-01T00:00:00Z"


def test_get_orders_includes_optional_filters(
    service: AlpacaService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """get_orders should forward filters to the request payload."""
    captured: dict[str, dict] = {}

    def fake_request(method, path, *, params=None, **kwargs):
        captured["params"] = params
        return [
            {
                "id": "abc",
                "qty": "1",
                "filled_qty": "0",
                "symbol": "AAPL",
                "status": "new",
                "type": "limit",
                "side": "buy",
                "time_in_force": "day",
            }
        ]

    monkeypatch.setattr(service, "_request", fake_request)
    orders = service.get_orders(status="open", limit=1, direction="desc")

    assert orders[0]["id"] == "abc"
    assert captured["params"]["status"] == "open"
    assert captured["params"]["limit"] == 1
    assert captured["params"]["direction"] == "desc"


def test_submit_stop_order_includes_stop_price(
    service: AlpacaService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stop orders must include stop price."""

    captured: dict[str, Any] = {}

    def fake_request(method, path, *, body=None, **kwargs):
        captured["body"] = body
        return {"id": "stop_id"}

    monkeypatch.setattr(service, "_request", fake_request)
    service.submit_stop_order(symbol="AAPL", qty=1, side=OrderSide.BUY, stop_price=150.0)

    assert captured["body"]["type"] == "stop"
    assert captured["body"]["stop_price"] == 150.0


def test_submit_stop_limit_order_includes_prices(
    service: AlpacaService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stop limit orders must include both stop and limit prices."""

    captured: dict[str, Any] = {}

    def fake_request(method, path, *, body=None, **kwargs):
        captured["body"] = body
        return {"id": "stop_limit_id"}

    monkeypatch.setattr(service, "_request", fake_request)
    service.submit_stop_limit_order(
        symbol="AAPL",
        qty=1,
        side=OrderSide.SELL,
        stop_price=149.0,
        limit_price=148.5,
    )

    assert captured["body"]["type"] == "stop_limit"
    assert captured["body"]["stop_price"] == 149.0
    assert captured["body"]["limit_price"] == 148.5


def test_submit_trailing_stop_order_supports_trail_percent(
    service: AlpacaService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Trailing stop orders should include trail information."""

    captured: dict[str, Any] = {}

    def fake_request(method, path, *, body=None, **kwargs):
        captured["body"] = body
        return {"id": "trailing_id"}

    monkeypatch.setattr(service, "_request", fake_request)
    service.submit_trailing_stop_order(
        symbol="AAPL",
        qty=1,
        side=OrderSide.SELL,
        trail_percent=1.5,
    )

    assert captured["body"]["type"] == "trailing_stop"
    assert captured["body"]["trail_percent"] == 1.5


def test_submit_bracket_order_sets_order_class(
    service: AlpacaService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Bracket orders should configure TP and SL legs."""

    captured: dict[str, Any] = {}

    def fake_request(method, path, *, body=None, **kwargs):
        captured["body"] = body
        return {"id": "bracket_id"}

    monkeypatch.setattr(service, "_request", fake_request)
    service.submit_bracket_order(
        symbol="AAPL",
        qty=1,
        side=OrderSide.BUY,
        take_profit_limit_price=160.0,
        stop_loss_stop_price=145.0,
    )

    assert captured["body"]["order_class"] == "bracket"
    assert captured["body"]["take_profit"]["limit_price"] == 160.0
    assert captured["body"]["stop_loss"]["stop_price"] == 145.0


def test_submit_oco_order_configures_legs(
    service: AlpacaService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """OCO orders should include take profit and stop loss."""

    captured: dict[str, Any] = {}

    def fake_request(method, path, *, body=None, **kwargs):
        captured["body"] = body
        return {"id": "oco_id"}

    monkeypatch.setattr(service, "_request", fake_request)
    service.submit_oco_order(
        symbol="AAPL",
        qty=1,
        side=OrderSide.SELL,
        take_profit_limit_price=170.0,
        stop_loss_stop_price=155.0,
    )

    assert captured["body"]["order_class"] == "oco"
    assert captured["body"]["take_profit"]["limit_price"] == 170.0
    assert captured["body"]["stop_loss"]["stop_price"] == 155.0
