"""Main entry point for the trading bot."""

import logging
import sys
from typing import TYPE_CHECKING

from src.core.alpaca_service import AlpacaService
from src.core.bot import TradingBot
from src.strategies.moving_average import MovingAverageCrossover
from src.utils.config import Config

if TYPE_CHECKING:
    from src.core.strategy import Strategy

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point for the trading bot."""
    try:
        # Load configuration
        config = Config()

        # Initialize Alpaca service
        alpaca_service = AlpacaService(
            api_key=config.alpaca_api_key_id,
            secret_key=config.alpaca_api_secret_key,
            trading_mode=config.trading_mode,
        )

        # Initialize strategy
        strategy: Strategy = MovingAverageCrossover(
            short_window=config.short_window, long_window=config.long_window
        )

        # Create and run bot
        bot = TradingBot(config=config, strategy=strategy, alpaca_service=alpaca_service)
        bot.start()
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
