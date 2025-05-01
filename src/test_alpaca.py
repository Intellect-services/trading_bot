import logging
import os
from typing import List, cast

from alpaca.trading.client import TradingClient
from alpaca.trading.models import Position, TradeAccount

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_alpaca_connection() -> None:
    """Test the Alpaca API connection and basic functionality."""
    try:
        # Initialize trading client
        logger.info("Initializing Alpaca trading client...")
        trading_client = TradingClient(
            os.environ["ALPACA_API_KEY"],
            os.environ["ALPACA_API_SECRET"],
            paper=True,
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
        logger.info("Fetching positions...")
        positions = cast(List[Position], trading_client.get_all_positions())
        if positions:
            for position in positions:
                logger.info(f"Symbol: {position.symbol}")
                logger.info(f"Quantity: {position.qty}")
                logger.info(f"Market Value: ${position.market_value}")
                logger.info(f"Unrealized PL: ${position.unrealized_pl}")
                logger.info("---")
        else:
            logger.info("No positions found")

        logger.info("Alpaca API integration test completed successfully!")
    except Exception as e:
        logger.error(f"Error testing Alpaca integration: {e}")
        raise


if __name__ == "__main__":
    # Set up test environment variables
    os.environ["ALPACA_API_KEY"] = "test_api_key"
    os.environ["ALPACA_API_SECRET"] = "test_secret_key"

    # Run test
    test_alpaca_connection()
