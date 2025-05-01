"""Tests for Alpaca service."""

import logging
import unittest
from typing import Any, Dict, NoReturn
from unittest.mock import MagicMock, patch

from src.core.alpaca_service import AlpacaService

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_alpaca_service() -> None:
    try:
        # Initialize service
        logger.info("Initializing AlpacaService...")
        service = AlpacaService()

        # Test account info
        logger.info("\nTesting account info...")
        account = service.get_account()
        logger.info(f"Account ID: {account['account_id']}")
        logger.info(f"Buying Power: ${account['buying_power']}")
        logger.info(f"Equity: ${account['equity']}")
        logger.info(f"Cash: ${account['cash']}")
        logger.info(f"Status: {account['status']}")

        # Test positions
        logger.info("\nTesting positions...")
        positions = service.get_positions()
        if positions:
            for position in positions:
                logger.info(f"Symbol: {position['symbol']}")
                logger.info(f"Quantity: {position['quantity']}")
                logger.info(f"Market Value: ${position['market_value']}")
                logger.info(f"Unrealized P/L: ${position['unrealized_pl']}")
                logger.info("---")
        else:
            logger.info("No positions found")

        # Test market status
        logger.info("\nTesting market status...")
        market_status = service.get_market_status()
        logger.info(f"Market is {'open' if market_status['is_open'] else 'closed'}")
        logger.info(f"Next market open: {market_status['next_open']}")
        logger.info(f"Next market close: {market_status['next_close']}")

        # Test order creation (paper trading)
        logger.info("\nTesting order creation...")
        try:
            order = service.create_order("AAPL", 1, "buy")
            logger.info(f"Order submitted successfully: {order['order_id']}")
            logger.info(f"Order status: {order['status']}")

            # Cancel the test order
            logger.info("\nCanceling test order...")
            cancel_result = service.cancel_order(order["order_id"])
            logger.info(cancel_result["message"])
        except Exception as e:
            logger.error(f"Error creating test order: {str(e)}")

        logger.info("\nAlpacaService test completed successfully!")

    except Exception as e:
        logger.error(f"Error testing AlpacaService: {str(e)}")
        raise


if __name__ == "__main__":
    test_alpaca_service()
