import os
import logging
import pytest
from datetime import datetime
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from unittest.mock import patch, MagicMock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@pytest.fixture
def mock_env_vars():
    """Fixture to set up test environment variables."""
    original_env = dict(os.environ)
    os.environ['ALPACA_API_KEY'] = 'test_api_key'
    os.environ['ALPACA_API_SECRET'] = 'test_secret_key'
    yield
    os.environ.clear()
    os.environ.update(original_env)

@pytest.fixture
def alpaca_service(mock_env_vars):
    """Fixture to create a test instance of AlpacaService."""
    from core.alpaca_service import AlpacaService
    return AlpacaService()

def test_alpaca_connection():
    try:
        # Initialize trading client
        logger.info("Initializing Alpaca trading client...")
        trading_client = TradingClient(os.environ['ALPACA_API_KEY'], os.environ['ALPACA_API_SECRET'], paper=True)
        
        # Test account information
        logger.info("Fetching account information...")
        account = trading_client.get_account()
        logger.info(f"Account ID: {account.account_number}")
        logger.info(f"Buying Power: ${account.buying_power}")
        logger.info(f"Equity: ${account.equity}")
        logger.info(f"Cash: ${account.cash}")
        logger.info(f"Status: {account.status}")
        
        # Test positions
        logger.info("\nFetching positions...")
        positions = trading_client.get_all_positions()
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
        clock = trading_client.get_clock()
        logger.info(f"Market is {'open' if clock.is_open else 'closed'}")
        logger.info(f"Next market open: {clock.next_open}")
        logger.info(f"Next market close: {clock.next_close}")
        
        # Test order creation (paper trading)
        logger.info("\nTesting order creation...")
        order_data = MarketOrderRequest(
            symbol="AAPL",
            qty=1,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY
        )
        
        try:
            order = trading_client.submit_order(order_data)
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
    test_alpaca_connection() 