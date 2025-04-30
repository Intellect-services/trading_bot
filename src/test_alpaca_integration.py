import logging
import os
from datetime import datetime
from typing import Generator, Any, TYPE_CHECKING, cast
from unittest.mock import MagicMock, patch

import pytest
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.models import TradeAccount, Position, Clock, Order

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.core.alpaca_service import AlpacaService


@pytest.fixture
def mock_env_vars() -> Generator[None, None, None]:
    """Fixture to set up test environment variables."""
    original_env = dict(os.environ)
    os.environ["ALPACA_API_KEY"] = "test_api_key"
    os.environ["ALPACA_API_SECRET"] = "test_secret_key"
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def alpaca_service(mock_env_vars: None) -> "AlpacaService":
    """Fixture to create a test instance of AlpacaService."""
    from src.core.alpaca_service import AlpacaService

    return AlpacaService()


def test_alpaca_connection(alpaca_service: "AlpacaService") -> None:
    try:
        # Initialize trading client
        logger.info("Initializing Alpaca trading client...")
        trading_client = TradingClient(
            os.environ["ALPACA_API_KEY"], os.environ["ALPACA_API_SECRET"], paper=True
        )

        # Test account information
        logger.info("Fetching account information...")
        account = cast(TradeAccount, trading_client.get_account())
        logger.info(f"Account ID: {account.account_number}")
        logger.info(f"Buying Power: ${account.buying_power}")
        logger.info(f"Equity: ${account.equity}")
        logger.info(f"Cash: ${account.cash}")
        logger.info(f"Status: {account.status}")

        # Test positions
        logger.info("\nFetching positions...")
        positions = cast(list[Position], trading_client.get_all_positions())
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
        clock = cast(Clock, trading_client.get_clock())
        logger.info(f"Market is {'open' if clock.is_open else 'closed'}")
        logger.info(f"Next market open: {clock.next_open}")
        logger.info(f"Next market close: {clock.next_close}")

        # Test order creation (paper trading)
        logger.info("\nTesting order creation...")
        order_data = MarketOrderRequest(
            symbol="AAPL", qty=1, side=OrderSide.BUY, time_in_force=TimeInForce.DAY
        )

        try:
            order = cast(Order, trading_client.submit_order(order_data))
            logger.info(f"Order submitted successfully: {order.id}")
            logger.info(f"Order status: {order.status}")

            # Cancel the test order
            logger.info("\nCanceling test order...")
            trading_client.cancel_order_by_id(order.id)
            logger.info("Order canceled successfully")
        except Exception as e:
            logger.error(f"Error creating test order: {str(e)}")

        logger.info("\nAlpaca API integration test completed successfully!")

    except Exception as e:
        logger.error(f"Error testing Alpaca integration: {str(e)}")
        raise


if __name__ == "__main__":
    # Set up test environment variables
    os.environ["ALPACA_API_KEY"] = "test_api_key"
    os.environ["ALPACA_API_SECRET"] = "test_secret_key"

    # Create AlpacaService instance
    from src.core.alpaca_service import AlpacaService

    service = AlpacaService()

    # Run the test
    test_alpaca_connection(service)
