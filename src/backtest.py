"""Backtesting module."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, cast

import pandas as pd

from src.backtesting.engine import BacktestEngine
from src.core.bot import TradingBot
from src.core.data_feed import MockDataFeed
from src.core.portfolio import Portfolio
from src.core.risk_manager import RiskManager
from src.core.strategy import Strategy
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def run_backtest() -> Dict[str, Any]:
    """Run backtest simulation."""
    try:
        # Load configuration
        config_data = {
            "RISK_MAX_POSITION_SIZE": 0.1,
            "RISK_STOP_LOSS_PCT": 0.02,
            "RISK_TAKE_PROFIT_PCT": 0.04,
            "RISK_MAX_DRAWDOWN": 0.1,
            "RISK_MAX_LEVERAGE": 2.0,
            "RISK_PER_TRADE": 0.01,
            "INITIAL_CAPITAL": 10000.0,
            "ALPACA_API_KEY": "",
            "ALPACA_SECRET_KEY": "",
            "ALPACA_PAPER": True,
        }
        config = Config(config_data)

        # Initialize components
        from src.core.alpaca_client import AlpacaClient
        from src.core.alpaca_service import AlpacaService
        from src.strategies.moving_average import MovingAverageCrossover

        alpaca_client = AlpacaClient(
            api_key=str(config.ALPACA_API_KEY),
            api_secret=str(config.ALPACA_SECRET_KEY),
            base_url="https://paper-api.alpaca.markets"
            if config.ALPACA_PAPER
            else "https://api.alpaca.markets",
        )
        alpaca_service = AlpacaService(config_data)

        # Initialize strategy
        strategy = MovingAverageCrossover(config)

        # Initialize and run backtest
        bot = TradingBot(config=config, strategy=strategy)

        # Run backtest
        results = bot.backtest()

        # Save results
        save_results(results)

        return results

    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        raise


def save_results(results: Dict[str, Any]) -> None:
    """Save backtest results to file.

    Args:
        results: Backtest results dictionary
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backtest_results_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(results, f, indent=4)
        logger.info(f"Saved backtest results to {filename}")
    except Exception as e:
        logger.error(f"Error saving backtest results: {e}")
        raise


def main() -> None:
    """Main entry point for backtesting."""
    try:
        results = run_backtest()
        logger.info("Backtest completed successfully")
        logger.info(f"Results: {results}")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    main()
