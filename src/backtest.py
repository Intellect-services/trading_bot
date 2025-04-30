"""Backtesting module."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from src.backtesting.engine import BacktestEngine
from src.core.bot import TradingBot
from src.core.data_feed import MockDataFeed
from src.core.portfolio import Portfolio
from src.core.risk_manager import RiskManager
from src.core.strategy import BaseStrategy
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
            "RISK_MAX_DRAWDOWN": 0.1,
            "RISK_MAX_LEVERAGE": 2.0,
            "RISK_PER_TRADE": 0.01,
            "INITIAL_BALANCE": 10000.0,
            "ALPACA_API_KEY": "",
            "ALPACA_SECRET_KEY": "",
            "ALPACA_PAPER": True,
        }
        config = Config(config_data)

        # Initialize components
        risk_manager = RiskManager(
            {
                "max_position_size": config_data["RISK_MAX_POSITION_SIZE"],
                "stop_loss": config_data["RISK_STOP_LOSS_PCT"],
                "take_profit": config_data["RISK_STOP_LOSS_PCT"]
                * 2,  # Use 2x stop loss as take profit
                "max_drawdown": config_data["RISK_MAX_DRAWDOWN"],
                "max_leverage": config_data["RISK_MAX_LEVERAGE"],
                "risk_per_trade": config_data["RISK_PER_TRADE"],
            }
        )

        portfolio = Portfolio(float(config_data["INITIAL_BALANCE"]))
        data_feed = MockDataFeed()
        strategy = BaseStrategy(config_data)

        # Initialize and run backtest
        bot = TradingBot(
            strategy=strategy,
            risk_manager=risk_manager,
            portfolio=portfolio,
            data_feed=data_feed,
        )

        # Run backtest
        results = bot.run_backtest()

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
