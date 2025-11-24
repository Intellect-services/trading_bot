"""Live integration tests for Alpaca API."""

import os
from datetime import datetime, timedelta, timezone

import pytest
from dotenv import load_dotenv

from src.core.alpaca_service import AlpacaService

load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_API_SECRET")

pytestmark = pytest.mark.skipif(
    not API_KEY or not SECRET_KEY,
    reason="Set ALPACA_API_KEY and ALPACA_API_SECRET to run Alpaca integration tests.",
)


@pytest.fixture(scope="module")
def alpaca_service() -> AlpacaService:
    """Create a real AlpacaService backed by env credentials."""
    return AlpacaService(api_key=API_KEY, secret_key=SECRET_KEY)


def test_account_integration(alpaca_service: AlpacaService) -> None:
    """Verify account payload structure."""
    account = alpaca_service.get_account()
    assert account["portfolio_value"] >= 0
    assert account["cash"] >= 0
    assert isinstance(account["currency"], str)


def test_positions_integration(alpaca_service: AlpacaService) -> None:
    """Ensure positions endpoint responds."""
    positions = alpaca_service.get_positions()
    assert isinstance(positions, list)
    if positions:
        position = positions[0]
        assert "symbol" in position
        assert "qty" in position


def test_orders_listing(alpaca_service: AlpacaService) -> None:
    """List recent orders without placing a new one."""
    orders = alpaca_service.get_orders(limit=5)
    assert isinstance(orders, list)
    if orders:
        sample = orders[0]
        assert "symbol" in sample
        assert "status" in sample


def test_asset_lookup(alpaca_service: AlpacaService) -> None:
    """Fetch metadata for a common symbol."""
    asset = alpaca_service.get_asset("AAPL")
    assert asset["symbol"] == "AAPL"
    assert asset["tradable"] is True


def test_bars_integration(alpaca_service: AlpacaService) -> None:
    """Fetch recent bar data."""
    start = datetime.now(timezone.utc) - timedelta(days=5)
    bars = alpaca_service.get_bars("AAPL", "1Day", start=start)
    assert "AAPL" in bars
    if not bars["AAPL"]:
        pytest.skip("Alpaca plan does not provide recent bar data for this symbol.")
    first = bars["AAPL"][0]
    assert "open" in first
    assert "close" in first


def test_market_clock(alpaca_service: AlpacaService) -> None:
    """Clock endpoint should always respond."""
    clock = alpaca_service.get_market_clock()
    assert "is_open" in clock
    assert "next_open" in clock
