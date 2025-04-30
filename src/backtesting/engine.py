"""Backtesting engine module."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TypedDict, Union

import numpy as np
import pandas as pd

from src.core.portfolio import Portfolio, PositionDict, OrderDict
from src.core.strategy import Strategy
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
        strategy: Strategy,
        historical_data: pd.DataFrame,
        initial_capital: float = 100000.0,
        commission: float = 0.001,
    ) -> None:
        """Initialize backtesting engine.

        Args:
            strategy: Trading strategy
            historical_data: Historical price data
            initial_capital: Initial capital amount
            commission: Commission rate
        """
        self.strategy = strategy
        self.historical_data = historical_data
        self.initial_capital = initial_capital
        self.commission = commission
        self.portfolio = Portfolio(initial_capital)
        self.trades: List[BacktestTrade] = []
        self.equity_curve: List[float] = []
        self.logger = logging.getLogger(__name__)

    def run(self) -> BacktestResult:
        """Run backtest.

        Returns:
            Backtest results
        """
        try:
            for i in range(len(self.historical_data)):
                current_data = self.historical_data.iloc[i]
                current_date = self.historical_data.index[i]

                # Update portfolio prices
                self.portfolio.update_prices({"AAPL": float(current_data["close"])})

                # Generate signals
                signals = self.strategy.generate_signals(pd.DataFrame([current_data]))
                if signals is not None and not signals.empty:
                    # Get the latest signal
                    latest_signal = signals.iloc[-1]["signal"]

                    # Execute trades
                    if latest_signal > 0:  # Buy signal
                        position = self.portfolio.get_position("AAPL")
                        if not position:
                            size = self.portfolio.calculate_position_size(
                                current_data["close"]
                            )
                            self.portfolio.execute_order(
                                "AAPL", size, "buy", current_data["close"]
                            )
                            self.trades.append(
                                {
                                    "timestamp": current_date.isoformat(),
                                    "symbol": "AAPL",
                                    "side": "buy",
                                    "size": size,
                                    "price": current_data["close"],
                                    "pnl": 0.0,
                                }
                            )
                    elif latest_signal < 0:  # Sell signal
                        position = self.portfolio.get_position("AAPL")
                        if position:
                            size = position["size"]
                            self.portfolio.execute_order(
                                "AAPL", size, "sell", current_data["close"]
                            )
                            self.trades.append(
                                {
                                    "timestamp": current_date.isoformat(),
                                    "symbol": "AAPL",
                                    "side": "sell",
                                    "size": size,
                                    "price": current_data["close"],
                                    "pnl": 0.0,
                                }
                            )

                # Record equity
                self.equity_curve.append(self.portfolio.get_value())

            # Calculate performance metrics
            return self._calculate_metrics()
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return {
                "trades": [],
                "total_return": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "avg_trade": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "max_win": 0.0,
                "max_loss": 0.0,
            }

    def _calculate_metrics(self) -> BacktestResult:
        try:
            trades_dict = [dict(trade) for trade in self.trades]

            # Calculate returns
            returns = [trade["pnl"] for trade in self.trades]
            total_return = float(np.sum(returns))

            # Calculate Sharpe ratio
            if len(returns) > 1:
                sharpe_ratio = float(np.mean(returns) / np.std(returns) * np.sqrt(252))
            else:
                sharpe_ratio = 0.0

            # Calculate maximum drawdown
            cumulative_returns = np.cumsum(returns)
            rolling_max = np.maximum.accumulate(cumulative_returns)
            drawdowns = rolling_max - cumulative_returns
            max_drawdown = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0

            # Calculate win rate and profit factor
            winning_trades = [t for t in self.trades if t["pnl"] > 0]
            losing_trades = [t for t in self.trades if t["pnl"] < 0]

            win_rate = (
                float(len(winning_trades) / len(self.trades)) if self.trades else 0.0
            )

            total_profits = sum(t["pnl"] for t in winning_trades)
            total_losses = abs(sum(t["pnl"] for t in losing_trades))
            profit_factor = (
                float(total_profits / total_losses) if total_losses != 0 else 0.0
            )

            # Calculate average metrics
            avg_trade = float(np.mean(returns)) if returns else 0.0
            avg_win = (
                float(np.mean([t["pnl"] for t in winning_trades]))
                if winning_trades
                else 0.0
            )
            avg_loss = (
                float(np.mean([t["pnl"] for t in losing_trades]))
                if losing_trades
                else 0.0
            )
            max_win = (
                float(max(t["pnl"] for t in winning_trades)) if winning_trades else 0.0
            )
            max_loss = (
                float(min(t["pnl"] for t in losing_trades)) if losing_trades else 0.0
            )

            return {
                "trades": trades_dict,
                "total_return": total_return,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "avg_trade": avg_trade,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "max_win": max_win,
                "max_loss": max_loss,
            }
        except Exception as e:
            self.logger.error(f"Error calculating metrics: {e}")
            return {
                "trades": [],
                "total_return": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "avg_trade": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "max_win": 0.0,
                "max_loss": 0.0,
            }

    def calculate_returns(self) -> float:
        """Calculate total returns.

        Returns:
            Total returns as percentage
        """
        try:
            if not self.equity_curve:
                return 0.0
            return (self.equity_curve[-1] - self.initial_capital) / self.initial_capital
        except Exception as e:
            logger.error(f"Error calculating returns: {e}")
            return 0.0

    def calculate_sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio.

        Returns:
            Sharpe ratio
        """
        try:
            if not self.equity_curve:
                return 0.0
            returns = np.diff(self.equity_curve) / self.equity_curve[:-1]
            if len(returns) < 2:
                return 0.0
            return np.sqrt(252) * np.mean(returns) / np.std(returns)
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {e}")
            return 0.0

    def calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown.

        Returns:
            Maximum drawdown as percentage
        """
        try:
            if not self.equity_curve:
                return 0.0
            peak = self.equity_curve[0]
            max_dd = 0.0
            for value in self.equity_curve[1:]:
                if value > peak:
                    peak = value
                dd = (peak - value) / peak
                if dd > max_dd:
                    max_dd = dd
            return max_dd
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {e}")
            return 0.0

    def calculate_win_rate(self) -> float:
        """Calculate win rate.

        Returns:
            Win rate as percentage
        """
        try:
            if not self.trades:
                return 0.0
            wins = len([trade for trade in self.trades if trade["side"] == "sell"])
            return float(wins) / len(self.trades) if len(self.trades) > 0 else 0.0
        except Exception as e:
            logger.error(f"Error calculating win rate: {e}")
            return 0.0

    def calculate_profit_factor(self) -> float:
        """Calculate profit factor.

        Returns:
            Profit factor
        """
        try:
            if not self.trades:
                return 0.0
            total_profit = sum(
                trade["price"] * trade["size"]
                for trade in self.trades
                if trade["side"] == "sell"
            )
            total_loss = sum(
                trade["price"] * trade["size"]
                for trade in self.trades
                if trade["side"] == "buy"
            )
            return total_profit / total_loss if total_loss != 0 else 0.0
        except Exception as e:
            logger.error(f"Error calculating profit factor: {e}")
            return 0.0

    def calculate_avg_trade(self) -> float:
        """Calculate average trade profit/loss.

        Returns:
            Average trade profit/loss
        """
        try:
            if not self.trades:
                return 0.0
            total_pnl = sum(
                trade["price"] * trade["size"] * (1 if trade["side"] == "sell" else -1)
                for trade in self.trades
            )
            return total_pnl / len(self.trades)
        except Exception as e:
            logger.error(f"Error calculating average trade: {e}")
            return 0.0

    def calculate_avg_win(self) -> float:
        """Calculate average winning trade.

        Returns:
            Average winning trade amount
        """
        try:
            winning_trades = [t["pnl"] for t in self.trades if t["pnl"] > 0]
            if not winning_trades:
                return 0.0
            return float(np.mean(winning_trades))
        except Exception as e:
            logger.error(f"Error calculating average win: {e}")
            return 0.0

    def calculate_avg_loss(self) -> float:
        """Calculate average losing trade.

        Returns:
            Average losing trade amount
        """
        try:
            losing_trades = [t["pnl"] for t in self.trades if t["pnl"] < 0]
            if not losing_trades:
                return 0.0
            return float(np.mean(losing_trades))
        except Exception as e:
            logger.error(f"Error calculating average loss: {e}")
            return 0.0

    def calculate_max_win(self) -> float:
        """Calculate maximum winning trade.

        Returns:
            Maximum winning trade profit
        """
        try:
            winning_trades = [
                trade["price"] * trade["size"]
                for trade in self.trades
                if trade["side"] == "sell"
            ]
            return max(winning_trades) if winning_trades else 0.0
        except Exception as e:
            logger.error(f"Error calculating max win: {e}")
            return 0.0

    def calculate_max_loss(self) -> float:
        """Calculate maximum losing trade.

        Returns:
            Maximum losing trade loss
        """
        try:
            losing_trades = [
                trade["price"] * trade["size"]
                for trade in self.trades
                if trade["side"] == "buy"
            ]
            return max(losing_trades) if losing_trades else 0.0
        except Exception as e:
            logger.error(f"Error calculating max loss: {e}")
            return 0.0
