"""Backtesting engine for trading strategies."""

from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from pandas import Series

from ..types import BacktestMetrics, BacktestResult
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class Backtest:
    """Backtesting engine for trading strategies."""

    def __init__(self, strategy: Any, initial_capital: float = 100000.0) -> None:
        """Initialize backtesting engine.

        Args:
            strategy: Trading strategy to backtest
            initial_capital: Initial capital for backtesting
        """
        self.strategy = strategy
        self.initial_capital = initial_capital

    def run(
        self,
        data: pd.DataFrame,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> BacktestResult:
        """Run backtest on historical data.

        Args:
            data: Historical price data
            start_date: Optional start date for backtest
            end_date: Optional end date for backtest

        Returns:
            Backtest results including portfolio and metrics

        Raises:
            Exception: If backtest fails
        """
        try:
            # Filter data by date range if specified
            if start_date and end_date:
                data = data[(data.index >= start_date) & (data.index <= end_date)]

            # Initialize portfolio
            portfolio: dict[str, Any] = {
                "cash": self.initial_capital,
                "positions": {},
                "trades": [],
            }

            # Run strategy on each bar
            for i in range(len(data)):
                current_bar: Series[float] = data.iloc[i]
                current_time = data.index[i]

                # Update strategy state
                self.strategy.update_state(current_bar, current_time)

                # Get signals
                signals = self.strategy.generate_signals()

                # Execute trades based on signals
                self._execute_trades(signals, current_bar, current_time, portfolio)

                # Update portfolio value
                self._update_portfolio_value(portfolio, current_bar)

            # Calculate metrics
            metrics = self._calculate_metrics(portfolio, data)

            return BacktestResult(
                portfolio=portfolio,
                metrics=metrics,
                trades=portfolio["trades"],
            )

        except Exception as e:
            logger.error("Error running backtest: %s", str(e))
            raise

    def _execute_trades(
        self,
        signals: dict[str, float],
        current_bar: Series[float],
        current_time: datetime,
        portfolio: dict[str, Any],
    ) -> None:
        """Execute trades based on strategy signals.

        Args:
            signals: Trading signals from strategy
            current_bar: Current price bar
            current_time: Current timestamp
            portfolio: Portfolio state

        Raises:
            Exception: If trade execution fails
        """
        try:
            for symbol, signal in signals.items():
                if signal > 0:  # Buy signal
                    if symbol not in portfolio["positions"]:
                        # Calculate position size
                        position_size = portfolio["cash"] * 0.1  # Use 10% of cash
                        price = float(current_bar["close"])
                        shares = position_size / price

                        # Execute buy
                        portfolio["cash"] -= position_size
                        portfolio["positions"][symbol] = {
                            "shares": shares,
                            "entry_price": price,
                        }

                        # Record trade
                        portfolio["trades"].append(
                            {
                                "symbol": symbol,
                                "side": "buy",
                                "shares": shares,
                                "price": price,
                                "timestamp": current_time,
                            }
                        )

                elif signal < 0 and symbol in portfolio["positions"]:  # Sell signal
                    position = portfolio["positions"][symbol]
                    price = float(current_bar["close"])

                    # Execute sell
                    portfolio["cash"] += position["shares"] * price
                    del portfolio["positions"][symbol]

                    # Record trade
                    portfolio["trades"].append(
                        {
                            "symbol": symbol,
                            "side": "sell",
                            "shares": position["shares"],
                            "price": price,
                            "timestamp": current_time,
                        }
                    )

        except Exception as e:
            logger.error("Error executing trades: %s", str(e))
            raise

    def _update_portfolio_value(
        self, portfolio: dict[str, Any], current_bar: Series[float]
    ) -> None:
        """Update portfolio value based on current prices.

        Args:
            portfolio: Portfolio state
            current_bar: Current price bar

        Raises:
            Exception: If portfolio update fails
        """
        try:
            total_value = portfolio["cash"]

            for _symbol, position in portfolio["positions"].items():
                price = float(current_bar["close"])
                total_value += position["shares"] * price

            portfolio["total_value"] = total_value
        except Exception as e:
            logger.error("Error updating portfolio value: %s", str(e))
            raise

    def _calculate_metrics(self, portfolio: dict[str, Any], data: pd.DataFrame) -> BacktestMetrics:
        """Calculate backtest performance metrics.

        Args:
            portfolio: Portfolio state
            data: Historical price data

        Returns:
            BacktestMetrics: Performance metrics

        Raises:
            Exception: If metric calculation fails
        """
        try:
            # Calculate returns
            returns = []
            for _i in range(1, len(data)):
                prev_value = portfolio["total_value"]
                current_value = portfolio["total_value"]
                returns.append((current_value - prev_value) / prev_value)

            # Calculate metrics
            total_return = (portfolio["total_value"] - self.initial_capital) / self.initial_capital
            annual_return = (1 + total_return) ** (252 / len(data)) - 1
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
            max_drawdown = self._calculate_max_drawdown(returns)

            return BacktestMetrics(
                total_return=total_return,
                annual_return=annual_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                num_trades=len(portfolio["trades"]),
            )
        except Exception as e:
            logger.error("Error calculating metrics: %s", str(e))
            raise

    def _calculate_max_drawdown(self, returns: list[float]) -> float:
        """Calculate maximum drawdown.

        Args:
            returns: List of returns

        Returns:
            float: Maximum drawdown

        Raises:
            Exception: If drawdown calculation fails
        """
        try:
            cumulative_returns = np.cumprod(1 + np.array(returns))
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdowns = (running_max - cumulative_returns) / running_max
            return float(np.max(drawdowns))
        except Exception as e:
            logger.error("Error calculating max drawdown: %s", str(e))
            raise
