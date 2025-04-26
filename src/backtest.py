import pandas as pd
from datetime import date
from typing import Dict, List, Optional

from src.core.strategy import Strategy
from src.core.risk_manager import RiskManager
from src.core.portfolio import Portfolio
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class Backtester:
    """Backtesting engine for trading strategies."""

    def __init__(
        self,
        strategy: Strategy,
        risk_manager: RiskManager,
        portfolio: Portfolio,
        config: Config,
    ):
        """Initialize backtester with strategy and data.

        Args:
            strategy: Trading strategy instance
            risk_manager: Risk manager instance
            portfolio: Portfolio instance
            config: Configuration instance
        """
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.portfolio = portfolio
        self.config = config
        logger.info("Backtester initialized")


def run_backtest():
    # Load configuration
    config = get_config()

    # Create strategy with parameters
    strategy_params = {"short_window": 20, "long_window": 50, "signal_threshold": 0.01}
    strategy = MovingAverageCrossover(strategy_params)

    # Load historical data
    # In a real implementation, this would fetch data from your data source
    # For this example, we'll create sample data
    dates = pd.date_range(
        start=config["BACKTEST_START_DATE"], end=config["BACKTEST_END_DATE"], freq="D"
    )
    data = pd.DataFrame(
        {
            "open": 100 + pd.Series(range(len(dates))) * 0.1,
            "high": 100 + pd.Series(range(len(dates))) * 0.1 + 1,
            "low": 100 + pd.Series(range(len(dates))) * 0.1 - 1,
            "close": 100 + pd.Series(range(len(dates))) * 0.1,
            "volume": 1000000,
        },
        index=dates,
    )

    # Create and run backtest
    engine = BacktestEngine(
        strategy=strategy, initial_capital=config["BACKTEST_INITIAL_CAPITAL"]
    )

    results = engine.run(data, commission=config["BACKTEST_COMMISSION"])

    # Print results
    print("\nBacktest Results")
    print("=" * 50)

    # Print metrics
    formatted_metrics = format_metrics(results["metrics"])
    for metric, value in formatted_metrics.items():
        print(f"{metric}: {value}")

    # Print trade summary
    print("\nTrade Summary")
    print("=" * 50)
    print(f"Total Trades: {len(results['trades']) // 2}")

    # Print equity curve summary
    print("\nEquity Curve Summary")
    print("=" * 50)
    initial_equity = results["equity_curve"][0]["equity"]
    final_equity = results["equity_curve"][-1]["equity"]
    total_return = (final_equity - initial_equity) / initial_equity
    print(f"Initial Equity: ${initial_equity:,.2f}")
    print(f"Final Equity: ${final_equity:,.2f}")
    print(f"Total Return: {total_return:.2%}")


if __name__ == "__main__":
    run_backtest()
