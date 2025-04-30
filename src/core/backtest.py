"""Backtesting engine for trading strategies."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from pandas import Series

from ..types import BacktestMetrics, BacktestResult
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class Backtest:
    """Backtesting engine for trading strategies."""

    def __init__(self, strategy: Any, initial_capital: float = 100000.0):
        """Initialize backtesting engine.

        Args:
            strategy: Trading strategy to backtest
            initial_capital: Initial capital for backtesting
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.logger = logger

    def run(
        self,
        data: pd.DataFrame,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> BacktestResult:
        """Run backtest on historical data.

        Args:
            data: Historical price data
            start_date: Optional start date for backtest
            end_date: Optional end date for backtest

        Returns:
            Backtest results including portfolio and metrics
        """
        try:
            # Filter data by date range if specified
            if start_date and end_date:
                data = data[(data.index >= start_date) & (data.index <= end_date)]

            # Initialize portfolio
            portfolio: Dict[str, Any] = {
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
            self.logger.error(f"Error running backtest: {str(e)}")
            raise

    def _execute_trades(
        self,
        signals: Dict[str, float],
        current_bar: Series[float],
        current_time: datetime,
        portfolio: Dict[str, Any],
    ) -> None:
        """Execute trades based on strategy signals.

        Args:
            signals: Trading signals from strategy
            current_bar: Current price bar
            current_time: Current timestamp
            portfolio: Portfolio state
        """
        for symbol, signal in signals.items():
            if signal > 0:  # Buy signal
                if symbol not in portfolio["positions"]:
                    # Calculate position size
                    position_size = portfolio["cash"] * 0.1  # Use 10% of cash
                    price = current_bar["close"]
                    shares = position_size / price

                    # Execute buy
                    portfolio["positions"][symbol] = {
                        "shares": shares,
                        "entry_price": price,
                        "entry_time": current_time,
                    }
                    portfolio["cash"] -= position_size

                    # Record trade
                    portfolio["trades"].append(
                        {
                            "symbol": symbol,
                            "type": "buy",
                            "shares": shares,
                            "price": price,
                            "time": current_time,
                        }
                    )

            elif signal < 0:  # Sell signal
                if symbol in portfolio["positions"]:
                    position = portfolio["positions"][symbol]
                    price = current_bar["close"]

                    # Execute sell
                    portfolio["cash"] += position["shares"] * price
                    del portfolio["positions"][symbol]

                    # Record trade
                    portfolio["trades"].append(
                        {
                            "symbol": symbol,
                            "type": "sell",
                            "shares": position["shares"],
                            "price": price,
                            "time": current_time,
                        }
                    )

    def _update_portfolio_value(
        self, portfolio: Dict[str, Any], current_bar: Series[float]
    ) -> None:
        """Update portfolio value based on current prices.

        Args:
            portfolio: Portfolio state
            current_bar: Current price bar
        """
        portfolio["value"] = portfolio["cash"]
        for symbol, position in portfolio["positions"].items():
            if symbol in current_bar.index:
                portfolio["value"] += position["shares"] * current_bar["close"]

    def _calculate_metrics(
        self, portfolio: Dict[str, Any], data: pd.DataFrame
    ) -> BacktestMetrics:
        """Calculate backtest performance metrics.

        Args:
            portfolio: Portfolio state
            data: Historical price data

        Returns:
            Performance metrics
        """
        # Calculate returns
        returns: List[float] = []
        for i in range(1, len(data)):
            prev_value = portfolio["value"] if i == 1 else returns[-1]
            current_value = portfolio["value"]
            returns.append((current_value - prev_value) / prev_value)

        returns_array = np.array(returns)

        # Calculate metrics
        total_return = (
            portfolio["value"] - self.initial_capital
        ) / self.initial_capital
        annual_return = (1 + total_return) ** (252 / len(data)) - 1
        sharpe_ratio = np.mean(returns_array) / np.std(returns_array) * np.sqrt(252)
        max_drawdown = np.min(returns_array)

        return BacktestMetrics(
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            num_trades=len(portfolio["trades"]),
        )
