"""Backtesting module."""

import json
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from src.backtesting.engine import BacktestEngine
from src.strategies.moving_average import MovingAverageCrossover
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def _build_synthetic_data(days: int) -> pd.DataFrame:
    """Create a simple synthetic price series for backtesting."""
    periods = max(days, 100)
    end = datetime.now()
    dates = pd.date_range(end=end, periods=periods, freq="D")
    prices = 100 + np.sin(np.linspace(0, 6.28, periods)) * 5 + np.linspace(0, 2, periods)
    return pd.DataFrame({"close": prices}, index=dates)


def run_backtest() -> dict[str, Any]:
    """Run backtest simulation."""
    config = Config()
    strategy = MovingAverageCrossover(
        short_window=config.short_window,
        long_window=config.long_window,
    )

    data = _build_synthetic_data(config.lookback_days)
    engine = BacktestEngine(strategy=strategy, initial_capital=10000.0)
    results = engine.run(data)
    save_results(results)
    return results


def save_results(results: dict[str, Any]) -> None:
    """Save backtest results to file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backtest_results_{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as output_file:
        json.dump(results, output_file, indent=4)
    logger.info("Saved backtest results to %s", filename)


def main() -> None:
    """Main entry point for backtesting."""
    results = run_backtest()
    logger.info("Backtest completed successfully")
    logger.info("Results: %s", results)


if __name__ == "__main__":
    main()
