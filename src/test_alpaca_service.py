"""Tests for Alpaca service."""

import os
from datetime import datetime
from typing import Generator

import pytest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.models import Order, Position

from src.core.alpaca_service import AlpacaService
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@pytest.fixture
def mock_env_vars() -> Generator[None, None, None]:
    """Fixture to set up test environment variables."""
    original_env = dict(os.environ)
    os.environ["ALPACA_API_KEY"] = "test_api_key"
    os.environ["ALPACA_SECRET_KEY"] = "test_secret_key"
    os.environ["ALPACA_PAPER"] = "True"
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def alpaca_service(mock_env_vars: None) -> AlpacaService:
    """Fixture to create a test instance of AlpacaService."""
    config = {
        "ALPACA_API_KEY": os.environ["ALPACA_API_KEY"],
        "ALPACA_SECRET_KEY": os.environ["ALPACA_SECRET_KEY"],
        "ALPACA_PAPER": os.environ["ALPACA_PAPER"].lower() == "true",
    }
    return AlpacaService(config)


def test_alpaca_connection(alpaca_service: AlpacaService) -> None:
    """Test Alpaca API connection and basic operations."""
    try:
        # Test account information
        logger.info("Fetching account information...")
        account = alpaca_service.get_account()
        logger.info(f"Account ID: {account.id}")
        logger.info(f"Buying Power: ${account.buying_power}")
        logger.info(f"Equity: ${account.equity}")
        logger.info(f"Cash: ${account.cash}")
        logger.info(f"Status: {account.status}")

        # Test positions
        logger.info("\nFetching positions...")
        positions = alpaca_service.get_positions()
        if positions:
            for position in positions:
                logger.info(f"Symbol: {position.symbol}")
                logger.info(f"Quantity: {position.qty}")
                logger.info(f"Market Value: ${position.market_value}")
                logger.info(f"Unrealized P/L: ${position.unrealized_pl}")
                logger.info("---")
        else:
            logger.info("No positions found")

        # Test market status
        logger.info("\nFetching market status...")
        status = alpaca_service.get_market_status()
        logger.info(f"Market is {'open' if status else 'closed'}")

        # Test order creation (paper trading)
        logger.info("\nTesting order creation...")
        order = alpaca_service.submit_order(
            symbol="AAPL",
            qty=1,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
        )
        logger.info(f"Order submitted successfully: {order.id}")
        logger.info(f"Order status: {order.status}")

        # Cancel the test order
        logger.info("\nCanceling test order...")
        alpaca_service.cancel_order(order.id)
        logger.info("Order canceled successfully")

        logger.info("\nAlpaca API integration test completed successfully!")

    except Exception as e:
        logger.error(f"Error testing Alpaca integration: {str(e)}")
        raise


if __name__ == "__main__":
    # Set up test environment variables
    os.environ["ALPACA_API_KEY"] = "test_api_key"
    os.environ["ALPACA_SECRET_KEY"] = "test_secret_key"
    os.environ["ALPACA_PAPER"] = "True"

    # Create AlpacaService instance
    config = {
        "ALPACA_API_KEY": os.environ["ALPACA_API_KEY"],
        "ALPACA_SECRET_KEY": os.environ["ALPACA_SECRET_KEY"],
        "ALPACA_PAPER": os.environ["ALPACA_PAPER"].lower() == "true",
    }
    service = AlpacaService(config)

    # Run the test
    test_alpaca_connection(service)
