"""Main module for trading bot."""

import json
import os
import signal
import sys
from typing import Any, Dict, Optional

from src.core.bot import TradingBot
from src.core.data_feed import DataFeed
from src.core.portfolio import Portfolio
from src.core.risk_manager import RiskManager
from src.core.alpaca_client import AlpacaClient
from src.strategies.moving_average import MovingAverageCrossover
from src.utils.config import Config
from src.utils.logger import setup_logger
from src.core.alpaca_service import AlpacaService

logger = setup_logger(__name__)


def load_config(config_file: str = "config.json") -> Config:
    """Load configuration from file.

    Args:
        config_file: Path to configuration file

    Returns:
        Configuration instance
    """
    try:
        with open(config_file, "r") as f:
            config_data = json.load(f)
        return Config(config_data)
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        sys.exit(1)


def initialize_bot(config_data: Dict[str, Any]) -> TradingBot:
    """Initialize the trading bot with configuration.

    Args:
        config_data: Configuration data dictionary

    Returns:
        Initialized trading bot instance
    """
    try:
        # Set environment variables for Alpaca API
        os.environ["ALPACA_API_KEY"] = config_data.get("ALPACA_API_KEY", "")
        os.environ["ALPACA_API_SECRET"] = config_data.get("ALPACA_SECRET_KEY", "")
        
        # Initialize services
        alpaca_client = AlpacaClient(
            api_key=config_data.get("ALPACA_API_KEY", ""),
            secret_key=config_data.get("ALPACA_SECRET_KEY", ""),
            paper=config_data.get("ALPACA_PAPER", True)
        )
        alpaca_service = AlpacaService()
        bot = TradingBot(alpaca_service)
        return bot
    except Exception as e:
        logger.error(f"Error initializing bot: {e}")
        raise


def handle_shutdown(bot: TradingBot) -> None:
    """Handle graceful shutdown.

    Args:
        bot: Trading bot instance
    """

    def signal_handler(signum: int, frame: Any) -> None:
        """Handle shutdown signal.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info("Shutting down...")
        bot.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main() -> None:
    """Main entry point for the trading bot."""
    try:
        # Load configuration
        config = load_config()
        
        # Initialize Alpaca service
        alpaca_service = AlpacaService()
        
        # Initialize and start trading bot
        bot = TradingBot(alpaca_service)
        handle_shutdown(bot)
        
        # Start the bot
        bot.start()

    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise


if __name__ == "__main__":
    main()
