"""Script to run the trading bot."""

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from .core.alpaca_service import AlpacaService
from .core.trading_bot import TradingBot
from .utils.config import Config
from .utils.logger import setup_logger

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def run_bot(config_data: Optional[Dict[str, Any]] = None) -> None:
    """Run the trading bot.

    Args:
        config_data: Optional configuration data. If None, uses default configuration.
    """
    try:
        # Load configuration
        if config_data is None:
            config_data = {
                "RISK_MAX_POSITION_SIZE": 0.1,
                "RISK_STOP_LOSS_PCT": 0.02,
                "RISK_MAX_DRAWDOWN": 0.1,
                "RISK_MAX_LEVERAGE": 2.0,
                "RISK_PER_TRADE": 0.01,
                "INITIAL_BALANCE": 10000.0,
                "ALPACA_API_KEY": os.getenv("ALPACA_API_KEY", ""),
                "ALPACA_SECRET_KEY": os.getenv("ALPACA_API_SECRET", ""),
                "ALPACA_PAPER": True,
            }
        config = Config.from_dict(config_data)

        # Initialize services
        alpaca_service = AlpacaService(config_data)
        trading_bot = TradingBot(alpaca_service)

        # Start bot
        logger.info("Starting trading bot...")
        trading_bot.start()

    except Exception as e:
        logger.error(f"Error running bot: {e}")
        raise


if __name__ == "__main__":
    run_bot()
