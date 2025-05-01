"""Integration tests for Alpaca API."""

# Standard library imports
import logging
import os
from typing import TYPE_CHECKING, Generator

# Third-party imports
import pytest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
from alpaca.trading.models import Order as AlpacaOrder, Position as AlpacaPosition

# Local imports
from core.types import Order, Position

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.core.alpaca_service import AlpacaService


@pytest.fixture
def mock_env_vars() -> Generator[None, None, None]:
    """Set up test environment variables."""
    os.environ["ALPACA_API_KEY"] = "test_api_key"
    os.environ["ALPACA_SECRET_KEY"] = "test_secret_key"
    os.environ["ALPACA_PAPER"] = "True"
    yield
    os.environ.pop("ALPACA_API_KEY", None)
    os.environ.pop("ALPACA_SECRET_KEY", None)
    os.environ.pop("ALPACA_PAPER", None)


@pytest.fixture
def alpaca_service(mock_env_vars: Generator[None, None, None]) -> "AlpacaService":
    """Create a test instance of AlpacaService."""
    config = {
        "ALPACA_API_KEY": os.environ["ALPACA_API_KEY"],
        "ALPACA_SECRET_KEY": os.environ["ALPACA_SECRET_KEY"],
        "ALPACA_PAPER": os.environ["ALPACA_PAPER"] == "True",
    }
    return AlpacaService(config)


def test_alpaca_connection(alpaca_service: "AlpacaService") -> None:
    """Test Alpaca API connection and basic operations."""
    # Test account info
    account = alpaca_service.get_account()
    assert account is not None
    assert hasattr(account, "cash")
    assert hasattr(account, "equity")
    assert hasattr(account, "buying_power")

    # Test positions
    positions = alpaca_service.get_positions()
    assert isinstance(positions, list)
    for position in positions:
        assert isinstance(position, Position)
        assert hasattr(position, "symbol")
        assert hasattr(position, "qty")
        assert hasattr(position, "avg_entry_price")

    # Test market status
    market_status = alpaca_service.get_market_status()
    assert isinstance(market_status, dict)
    assert "is_open" in market_status
    assert "next_open" in market_status
    assert "next_close" in market_status

    # Test order creation
    order = alpaca_service.submit_order(
        symbol="AAPL",
        qty=1,
        side=OrderSide.BUY,
        type=OrderType.MARKET,
        time_in_force=TimeInForce.DAY,
    )
    assert isinstance(order, Order)
    assert order.symbol == "AAPL"
    assert order.qty == 1
    assert order.side == OrderSide.BUY

    # Test order cancellation
    success = alpaca_service.cancel_order(order.id)
    assert success is True

    # Test portfolio history
    history = alpaca_service.get_portfolio_history()
    assert isinstance(history, dict)
    assert "timestamp" in history
    assert "equity" in history
    assert "profit_loss" in history


if __name__ == "__main__":
    # Set up test environment variables
    os.environ["ALPACA_API_KEY"] = "test_api_key"
    os.environ["ALPACA_SECRET_KEY"] = "test_secret_key"
    os.environ["ALPACA_PAPER"] = "True"

    # Create AlpacaService instance
    from src.core.alpaca_service import AlpacaService

    config = {
        "ALPACA_API_KEY": os.environ["ALPACA_API_KEY"],
        "ALPACA_SECRET_KEY": os.environ["ALPACA_SECRET_KEY"],
        "ALPACA_PAPER": os.environ["ALPACA_PAPER"].lower() == "true",
    }
    service = AlpacaService(config)

    # Run the test
    test_alpaca_connection(service)
