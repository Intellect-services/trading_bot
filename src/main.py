"""Main module for trading bot."""

import sys
import signal
from typing import Dict, Any, Optional
import json
import os

from src.utils.config import Config
from src.core.strategy import Strategy
from src.core.risk_manager import RiskManager
from src.core.portfolio import Portfolio
from src.core.data_feed import DataFeed
from src.core.bot import TradingBot
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def load_config(config_file: str = "config.json") -> Config:
    """Load configuration from file.

    Args:
        config_file: Path to configuration file

    Returns:
        Configuration instance
    """
    try:
        return Config(config_file)
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        sys.exit(1)


def initialize_bot(config: Config) -> TradingBot:
    """Initialize trading bot.

    Args:
        config: Configuration instance

    Returns:
        Trading bot instance
    """
    try:
        # Initialize components
        strategy = Strategy(config)
        risk_manager = RiskManager({
            'max_position_size': config.RISK_MAX_POSITION_SIZE,
            'stop_loss': config.RISK_STOP_LOSS_PCT,
            'take_profit': config.RISK_STOP_LOSS_PCT * 2,
            'max_drawdown': config.RISK_MAX_DRAWDOWN,
            'max_leverage': config.RISK_MAX_LEVERAGE,
            'risk_per_trade': config.RISK_PER_TRADE
        })
        data_feed = DataFeed(config)
        portfolio = Portfolio(config.INITIAL_BALANCE)

        # Create bot
        bot = TradingBot(
            config=config,
            strategy=strategy,
            risk_manager=risk_manager,
            data_feed=data_feed,
            portfolio=portfolio
        )

        # Add symbols
        for symbol in config.STRATEGY_PARAMS.get("symbols", ["SPY"]):
            bot.add_symbol(symbol)

        return bot

    except Exception as e:
        logger.error(f"Error initializing bot: {str(e)}")
        sys.exit(1)


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
        config = Config()
        
        # Initialize components
        risk_manager = RiskManager({
            'max_position_size': config.RISK_MAX_POSITION_SIZE,
            'stop_loss': config.RISK_STOP_LOSS_PCT,
            'take_profit': config.RISK_STOP_LOSS_PCT * 2,
            'max_drawdown': config.RISK_MAX_DRAWDOWN,
            'max_leverage': config.RISK_MAX_LEVERAGE,
            'risk_per_trade': config.RISK_PER_TRADE
        })
        
        portfolio = Portfolio(config.INITIAL_BALANCE)
        data_feed = DataFeed(config)
        strategy = Strategy(config)
        
        # Initialize and start trading bot
        bot = TradingBot(
            config=config,
            strategy=strategy,
            risk_manager=risk_manager,
            portfolio=portfolio,
            data_feed=data_feed
        )
        
        bot.start()
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise


if __name__ == "__main__":
    main()
