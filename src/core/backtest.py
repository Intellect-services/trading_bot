"""Backtesting engine for trading strategies."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd

from ..types import BacktestResult, BacktestMetrics
from ..utils.logger import setup_logger


class Backtest:
    def __init__(self, strategy, initial_capital: float = 100000.0):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.logger = setup_logger(__name__)

    def run(
        self,
        data: pd.DataFrame,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> BacktestResult:
        """Run backtest on historical data."""
        try:
            # Filter data by date range if specified
            if start_date and end_date:
                data = data[(data.index >= start_date) & (data.index <= end_date)]

            # Initialize portfolio
            portfolio = {
                "cash": self.initial_capital,
                "positions": {},
                "trades": [],
            }

            # Run strategy on each bar
            for i in range(len(data)):
                current_bar = data.iloc[i]
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
        current_bar: pd.Series,
        current_time: datetime,
        portfolio: Dict,
    ):
        """Execute trades based on strategy signals."""
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

    def _update_portfolio_value(self, portfolio: Dict, current_bar: pd.Series):
        """Update portfolio value based on current prices."""
        portfolio["value"] = portfolio["cash"]
        for symbol, position in portfolio["positions"].items():
            if symbol in current_bar.index:
                portfolio["value"] += position["shares"] * current_bar["close"]

    def _calculate_metrics(self, portfolio: Dict, data: pd.DataFrame) -> BacktestMetrics:
        """Calculate backtest performance metrics."""
        # Calculate returns
        returns = []
        for i in range(1, len(data)):
            prev_value = portfolio["value"] if i == 1 else returns[-1]
            current_value = portfolio["value"]
            returns.append((current_value - prev_value) / prev_value)

        returns = np.array(returns)

        # Calculate metrics
        total_return = (portfolio["value"] - self.initial_capital) / self.initial_capital
        annual_return = (1 + total_return) ** (252 / len(data)) - 1
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
        max_drawdown = np.min(returns)

        return BacktestMetrics(
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            num_trades=len(portfolio["trades"]),
        )
