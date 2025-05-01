"""Backtesting engine module."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TypedDict, Union

import numpy as np
import pandas as pd

from src.core.portfolio import OrderDict, Portfolio, PositionDict
from src.core.strategy import BaseStrategy
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class BacktestResult(TypedDict):
    """Type definition for backtest result."""

    trades: List[Dict[str, Any]]
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    avg_trade: float
    avg_win: float
    avg_loss: float
    max_win: float
    max_loss: float


class BacktestTrade(TypedDict):
    """Type definition for backtest trade."""

    timestamp: str
    symbol: str
    side: str
    size: float
    price: float
    pnl: float


class BacktestEngine:
    """Backtesting engine class."""

    def __init__(
        self,
        strategy: BaseStrategy,
        initial_capital: float,
        commission: float = 0.0,
        slippage: float = 0.0,
    ) -> None:
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.portfolio_value = initial_capital
        self.positions: Dict[str, float] = {}
        self.trades: List[Dict[str, Any]] = []
        self.metrics: Dict[str, float] = {}
        self.equity_curve: List[float] = [initial_capital]

    def run(
        self,
        data: pd.DataFrame,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Run the backtest."""
        if start_date is not None:
            data = data[data.index >= start_date]
        if end_date is not None:
            data = data[data.index <= end_date]

        self.portfolio_value = self.initial_capital
        self.positions = {}
        self.trades = []
        self.metrics = {}
        self.equity_curve = [self.initial_capital]

        for timestamp, row in data.iterrows():
            # Update strategy state
            self.strategy.update_state(row, timestamp)

            # Generate signals
            signals = self.strategy.generate_signals()

            # Execute trades based on signals
            self._execute_trades(signals, row, timestamp)

            # Update portfolio value
            self._update_portfolio_value(row)

        # Calculate final metrics
        self._calculate_metrics()

        return {
            "initial_capital": self.initial_capital,
            "final_value": self.portfolio_value,
            "total_return": (self.portfolio_value - self.initial_capital) / self.initial_capital,
            "trades": self.trades,
            "metrics": self.metrics,
        }

    def _execute_trades(
        self, signals: Dict[str, float], current_bar: pd.Series, current_time: datetime
    ) -> None:
        """Execute trades based on signals."""
        for symbol, signal in signals.items():
            if signal == 0.0:
                continue

            # Calculate position size
            price = float(current_bar[symbol])
            position_value = self.portfolio_value * abs(signal)
            shares = position_value / price

            # Apply slippage
            execution_price = price * (1 + self.slippage * (1 if signal > 0 else -1))

            # Calculate commission
            commission = execution_price * shares * self.commission

            # Record trade
            self.trades.append(
                {
                    "timestamp": current_time.isoformat(),
                    "symbol": symbol,
                    "signal": signal,
                    "price": execution_price,
                    "shares": shares,
                    "commission": commission,
                    "value": position_value,
                }
            )

            # Update positions
            self.positions[symbol] = shares if signal > 0 else -shares

    def _update_portfolio_value(self, current_bar: pd.Series) -> None:
        """Update portfolio value based on current prices."""
        portfolio_value = self.initial_capital

        for symbol, shares in self.positions.items():
            price = float(current_bar[symbol])
            portfolio_value += shares * price

        self.portfolio_value = portfolio_value
        self.equity_curve.append(portfolio_value)

    def _calculate_metrics(self) -> None:
        """Calculate performance metrics."""
        if not self.trades:
            self.metrics = {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "avg_return": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
            }
            return

        # Calculate returns
        returns = []
        equity = self.initial_capital
        peak = self.initial_capital
        max_drawdown = 0.0

        for trade in self.trades:
            pnl = trade["shares"] * trade["price"] - trade["commission"]
            equity += pnl
            returns.append(pnl / equity)

            # Update max drawdown
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak
            max_drawdown = max(max_drawdown, drawdown)

        # Convert returns to numpy array for calculations
        returns_array = np.array(returns)

        # Calculate metrics
        total_trades = len(self.trades)
        winning_trades = sum(1 for r in returns if r > 0)
        losing_trades = sum(1 for r in returns if r < 0)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        avg_return = float(np.mean(returns_array)) if len(returns_array) > 0 else 0.0
        sharpe_ratio = (
            float(np.mean(returns_array) / np.std(returns_array)) if len(returns_array) > 1 else 0.0
        )

        self.metrics = {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "avg_return": avg_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
        }

    def calculate_returns(self) -> float:
        """Calculate total returns."""
        if not self.equity_curve:
            return 0.0
        return (self.equity_curve[-1] - self.equity_curve[0]) / self.equity_curve[0]

    def calculate_sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio."""
        if len(self.equity_curve) < 2:
            return 0.0
        returns = np.diff(self.equity_curve) / self.equity_curve[:-1]
        if len(returns) < 2:
            return 0.0
        return float(np.mean(returns) / np.std(returns))

    def calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown."""
        if not self.equity_curve:
            return 0.0
        peak = self.equity_curve[0]
        max_drawdown = 0.0
        for value in self.equity_curve:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)
        return max_drawdown

    def calculate_win_rate(self) -> float:
        """Calculate win rate."""
        if not self.trades:
            return 0.0
        winning_trades = sum(1 for trade in self.trades if trade["shares"] * trade["price"] > 0)
        return winning_trades / len(self.trades)

    def calculate_profit_factor(self) -> float:
        """Calculate profit factor."""
        if not self.trades:
            return 0.0
        gross_profit = sum(
            trade["shares"] * trade["price"]
            for trade in self.trades
            if trade["shares"] * trade["price"] > 0
        )
        gross_loss = abs(
            sum(
                trade["shares"] * trade["price"]
                for trade in self.trades
                if trade["shares"] * trade["price"] < 0
            )
        )
        return gross_profit / gross_loss if gross_loss != 0 else float("inf")

    def calculate_avg_trade(self) -> float:
        """Calculate average trade profit/loss."""
        if not self.trades:
            return 0.0
        total_pnl = sum(trade["shares"] * trade["price"] for trade in self.trades)
        return total_pnl / len(self.trades)

    def calculate_avg_win(self) -> float:
        """Calculate average winning trade."""
        winning_trades = [
            trade["shares"] * trade["price"]
            for trade in self.trades
            if trade["shares"] * trade["price"] > 0
        ]
        return float(np.mean(winning_trades)) if winning_trades else 0.0

    def calculate_avg_loss(self) -> float:
        """Calculate average losing trade."""
        losing_trades = [
            trade["shares"] * trade["price"]
            for trade in self.trades
            if trade["shares"] * trade["price"] < 0
        ]
        return float(np.mean(losing_trades)) if losing_trades else 0.0

    def calculate_max_win(self) -> float:
        """Calculate maximum winning trade."""
        winning_trades = [
            trade["shares"] * trade["price"]
            for trade in self.trades
            if trade["shares"] * trade["price"] > 0
        ]
        return float(max(winning_trades)) if winning_trades else 0.0

    def calculate_max_loss(self) -> float:
        """Calculate maximum losing trade."""
        losing_trades = [
            trade["shares"] * trade["price"]
            for trade in self.trades
            if trade["shares"] * trade["price"] < 0
        ]
        return float(min(losing_trades)) if losing_trades else 0.0
