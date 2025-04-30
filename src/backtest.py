"""Backtesting module."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from src.backtesting.engine import BacktestEngine
from src.core.bot import TradingBot
from src.core.data_feed import DataFeed
from src.core.portfolio import Portfolio
from src.core.risk_manager import RiskManager
from src.core.strategy import Strategy
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def run_backtest():
    """Run backtest simulation."""
    try:
        # Load configuration
        config = Config()

        # Initialize components
        risk_manager = RiskManager(
            {
                "max_position_size": config.RISK_MAX_POSITION_SIZE,
                "stop_loss": config.RISK_STOP_LOSS_PCT,
                "take_profit": config.RISK_STOP_LOSS_PCT * 2,  # Use 2x stop loss as take profit
                "max_drawdown": config.RISK_MAX_DRAWDOWN,
                "max_leverage": config.RISK_MAX_LEVERAGE,
                "risk_per_trade": config.RISK_PER_TRADE,
            }
        )

        portfolio = Portfolio(config.INITIAL_BALANCE)
        data_feed = DataFeed(config)
        strategy = Strategy(config)

        # Initialize and run backtest
        bot = TradingBot(
            config=config,
            strategy=strategy,
            risk_manager=risk_manager,
            portfolio=portfolio,
            data_feed=data_feed,
        )

        # Run backtest
        results = bot.backtest()

        # Save results
        save_results(results)

        return results

    except Exception as e:
        logger.error(f"Error in backtest: {str(e)}")
        raise


def save_results(results: Dict[str, Any]) -> None:
    """Save backtest results to file.

    Args:
        results: Dictionary containing backtest results
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backtest_results_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(results, f, indent=4, default=str)

        logger.info(f"Results saved to {filename}")

    except Exception as e:
        logger.error(f"Error saving results: {str(e)}")


def main() -> None:
    """Main entry point."""
    try:
        results = run_backtest()
        print("\nBacktest Results:")
        print("================")
        print(f"Initial Value: ${results.get('initial_value', 0):,.2f}")
        print(f"Final Value: ${results.get('final_value', 0):,.2f}")
        print(f"Total Return: {results.get('total_return', 0) * 100:.2f}%")
        print(f"Total Trades: {results.get('total_trades', 0)}")
        print(f"Sharpe Ratio: {results.get('sharpe_ratio', 0):.2f}")
        print(f"Max Drawdown: {results.get('max_drawdown', 0) * 100:.2f}%")
        print(f"Win Rate: {results.get('win_rate', 0) * 100:.2f}%")
        print(f"Average Trade Return: {results.get('avg_trade_return', 0) * 100:.2f}%")

    except Exception as e:
        logger.error(f"Error in main: {str(e)}")


if __name__ == "__main__":
    main()
