"""Backtesting engine module."""

from collections import defaultdict
from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Any, TypedDict, cast

import numpy as np
import pandas as pd
from pandas import Series

from src.core.strategy import Strategy
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class BacktestResult(TypedDict):
    """Type definition for backtest result."""

    trades: list[dict[str, Any]]
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
        initial_capital: float,
        commission: float = 0.0,
        slippage: float = 0.0,
    ) -> None:
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.portfolio_value = initial_capital
        self.positions: dict[str, float] = {}
        self.trades: list[dict[str, Any]] = []
        self.metrics: dict[str, float] = {}
        self.equity_curve: list[float] = [initial_capital]

    def run(
        self,
        data: pd.DataFrame,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
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

        raw_signals = self.strategy.generate_signals(data)
        signals_by_time = self._normalize_signals(data, raw_signals)

        for timestamp, row in data.iterrows():
            current_time = cast("datetime", timestamp)
            for signal in signals_by_time.get(current_time, []):
                self._execute_signal(signal, row, current_time)
            self._update_portfolio_value(row)

        # Calculate final metrics
        self._calculate_metrics()

        return {
            "initial_capital": self.initial_capital,
            "final_value": self.portfolio_value,
            "total_return": (self.portfolio_value - self.initial_capital) / self.initial_capital,
            "trades": self.trades,
            "metrics": self.metrics,
            "equity_curve": self.equity_curve,
        }

    def run_multiple(
        self,
        market_data: dict[str, pd.DataFrame],
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        strategy_factory: Callable[[], Strategy] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Run backtests for multiple symbols."""

        results: dict[str, dict[str, Any]] = {}
        for symbol, df in market_data.items():
            strategy_instance = strategy_factory() if strategy_factory else self.strategy
            engine = BacktestEngine(
                strategy=strategy_instance,
                initial_capital=self.initial_capital,
                commission=self.commission,
                slippage=self.slippage,
            )
            results[symbol] = engine.run(df, start_date=start_date, end_date=end_date)
        return results

    def _execute_signal(
        self,
        signal: dict[str, Any],
        current_bar: Series,
        current_time: datetime,
    ) -> None:
        """Execute a single normalized signal."""
        symbol = signal["symbol"]
        action = signal["action"]
        price = signal.get("price")
        if price is None:
            price = self._extract_price(current_bar, symbol)
        if price <= 0:
            logger.warning("Skipping signal for %s due to invalid price %s", symbol, price)
            return

        raw_shares = float(signal.get("shares", 0.0))
        if raw_shares > 0:
            shares = raw_shares
        else:
            size_fraction = abs(float(signal.get("size", signal.get("strength", 0.1))))
            size_fraction = min(max(size_fraction, 0.0), 1.0)
            position_value = self.portfolio_value * size_fraction
            shares = position_value / price if price else 0.0

        if shares <= 0:
            return

        side_multiplier = 1 if action == "buy" else -1

        execution_price = price * (1 + self.slippage * side_multiplier)
        commission = execution_price * shares * self.commission

        self.trades.append(
            {
                "timestamp": current_time.isoformat(),
                "symbol": symbol,
                "side": action,
                "shares": shares,
                "price": execution_price,
                "commission": commission,
                "value": shares * execution_price,
            }
        )

        self.positions[symbol] = side_multiplier * shares

    def _update_portfolio_value(self, current_bar: Series) -> None:
        """Update portfolio value based on current prices."""
        portfolio_value = self.initial_capital

        for symbol, shares in self.positions.items():
            price = self._extract_price(current_bar, symbol)
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
        pnls = [trade.get("pnl", 0.0) for trade in self.trades if trade.get("side") == "sell"]
        returns_array = (
            np.array([pnl / self.initial_capital for pnl in pnls], dtype=float)
            if pnls
            else np.array([], dtype=float)
        )

        total_trades = len(pnls)
        winning_trades = sum(1 for pnl in pnls if pnl > 0)
        losing_trades = sum(1 for pnl in pnls if pnl < 0)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        avg_return = float(returns_array.mean()) if returns_array.size else 0.0
        volatility = float(np.std(returns_array)) if returns_array.size > 1 else 0.0
        sharpe_ratio = float(avg_return / volatility) if volatility else 0.0
        downside = returns_array[returns_array < 0]
        downside_std = float(np.std(downside)) if downside.size else 0.0
        sortino_ratio = float(avg_return / downside_std) if downside_std else 0.0
        max_drawdown = self.calculate_max_drawdown()
        cagr = self._calculate_cagr()
        profit_factor = self.calculate_profit_factor()

        self.metrics = {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "avg_return": avg_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "max_drawdown": max_drawdown,
            "cagr": cagr,
            "profit_factor": profit_factor,
        }

    def calculate_returns(self) -> float:
        """Calculate total returns.

        Returns:
            float: Total returns as a percentage
        """
        try:
            return float((self.portfolio_value - self.initial_capital) / self.initial_capital)
        except Exception as e:
            logger.error("Error calculating returns: %s", str(e))
            return 0.0

    def calculate_sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio.

        Returns:
            float: Sharpe ratio
        """
        try:
            returns = np.diff(self.equity_curve) / self.equity_curve[:-1]
            if len(returns) < 2:
                return 0.0
            return float(np.mean(returns) / np.std(returns))
        except Exception as e:
            logger.error("Error calculating Sharpe ratio: %s", str(e))
            return 0.0

    def calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown.

        Returns:
            float: Maximum drawdown as a percentage
        """
        try:
            peak = self.equity_curve[0]
            max_drawdown = 0.0
            for value in self.equity_curve:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
            return float(max_drawdown)
        except Exception as e:
            logger.error("Error calculating max drawdown: %s", str(e))
            return 0.0

    def calculate_win_rate(self) -> float:
        """Calculate win rate.

        Returns:
            float: Win rate as a percentage
        """
        try:
            if not self.trades:
                return 0.0
            winning_trades = sum(1 for trade in self.trades if trade["shares"] * trade["price"] > 0)
            return float(winning_trades / len(self.trades))
        except Exception as e:
            logger.error("Error calculating win rate: %s", str(e))
            return 0.0

    def calculate_profit_factor(self) -> float:
        """Calculate profit factor.

        Returns:
            float: Profit factor
        """
        try:
            if not self.trades:
                return 0.0
            pnl_list = [trade.get("pnl", 0.0) for trade in self.trades if trade["side"] == "sell"]
            gross_profit = sum(pnl for pnl in pnl_list if pnl > 0)
            gross_loss = abs(sum(pnl for pnl in pnl_list if pnl < 0))
            return float(gross_profit / gross_loss) if gross_loss != 0 else float("inf")
        except Exception as e:
            logger.error("Error calculating profit factor: %s", str(e))
            return 0.0

    def calculate_avg_trade(self) -> float:
        """Calculate average trade.

        Returns:
            float: Average trade value
        """
        try:
            if not self.trades:
                return 0.0
            return float(
                sum(trade["shares"] * trade["price"] for trade in self.trades) / len(self.trades)
            )
        except Exception as e:
            logger.error("Error calculating average trade: %s", str(e))
            return 0.0

    def calculate_avg_win(self) -> float:
        """Calculate average winning trade.

        Returns:
            float: Average winning trade value
        """
        try:
            winning_trades = [
                trade["shares"] * trade["price"]
                for trade in self.trades
                if trade["shares"] * trade["price"] > 0
            ]
            if not winning_trades:
                return 0.0
            return float(sum(winning_trades) / len(winning_trades))
        except Exception as e:
            logger.error("Error calculating average win: %s", str(e))
            return 0.0

    def calculate_avg_loss(self) -> float:
        """Calculate average losing trade.

        Returns:
            float: Average losing trade value
        """
        try:
            losing_trades = [
                trade["shares"] * trade["price"]
                for trade in self.trades
                if trade["shares"] * trade["price"] < 0
            ]
            if not losing_trades:
                return 0.0
            return float(sum(losing_trades) / len(losing_trades))
        except Exception as e:
            logger.error("Error calculating average loss: %s", str(e))
            return 0.0

    def calculate_max_win(self) -> float:
        """Calculate maximum winning trade.

        Returns:
            float: Maximum winning trade value
        """
        try:
            winning_trades = [
                trade["shares"] * trade["price"]
                for trade in self.trades
                if trade["shares"] * trade["price"] > 0
            ]
            return float(max(winning_trades)) if winning_trades else 0.0
        except Exception as e:
            logger.error("Error calculating max win: %s", str(e))
            return 0.0

    def calculate_max_loss(self) -> float:
        """Calculate maximum losing trade.

        Returns:
            float: Maximum losing trade value
        """
        try:
            losing_trades = [
                trade["shares"] * trade["price"]
                for trade in self.trades
                if trade["shares"] * trade["price"] < 0
            ]
            return float(min(losing_trades)) if losing_trades else 0.0
        except Exception as e:
            logger.error("Error calculating max loss: %s", str(e))
            return 0.0

    def _calculate_cagr(self) -> float:
        """Calculate compound annual growth rate from the equity curve."""

        try:
            if len(self.equity_curve) < 2:
                return 0.0
            total_return = self.equity_curve[-1] / self.equity_curve[0]
            periods = len(self.equity_curve) - 1
            years = max(periods / 252, 1 / 252)
            return float(total_return ** (1 / years) - 1)
        except Exception as e:
            logger.error("Error calculating CAGR: %s", str(e))
            return 0.0

    def _normalize_signals(
        self,
        data: pd.DataFrame,
        raw_signals: Any,
    ) -> defaultdict[datetime, list[dict[str, Any]]]:
        """Normalize raw strategy signals into a dictionary keyed by timestamp."""
        normalized: defaultdict[datetime, list[dict[str, Any]]] = defaultdict(list)
        signals_iterable: list[dict[str, Any]] = []

        if isinstance(raw_signals, pd.DataFrame):
            raw_records = raw_signals.to_dict("records")
            signals_iterable = [
                {str(key): value for key, value in record.items()} for record in raw_records
            ]
        elif isinstance(raw_signals, dict):
            signals_iterable = [{str(key): value for key, value in raw_signals.items()}]
        elif isinstance(raw_signals, Iterable):
            for item in raw_signals:
                try:
                    converted = {str(key): value for key, value in dict(item).items()}
                    signals_iterable.append(converted)
                except TypeError:
                    continue
        else:
            return normalized

        for signal in signals_iterable:
            symbol = str(signal.get("symbol") or signal.get("ticker") or "UNKNOWN").upper()
            action = str(signal.get("action") or signal.get("side") or "hold").lower()
            if action not in {"buy", "sell"}:
                continue

            timestamp_raw = signal.get("timestamp")
            if timestamp_raw is None:
                timestamp = data.index[-1]
            else:
                timestamp = pd.to_datetime(timestamp_raw, errors="coerce")
                if pd.isna(timestamp):
                    timestamp = data.index[-1]

            aligned_timestamp = self._align_timestamp(data.index, timestamp)
            size = float(signal.get("size", signal.get("strength", 0.1)))
            shares = float(signal.get("shares", 0.0))
            price = signal.get("price")
            if price is not None:
                price = float(price)

            normalized[aligned_timestamp].append(
                {
                    "symbol": symbol,
                    "action": action,
                    "size": size,
                    "shares": shares,
                    "price": price,
                }
            )

        return normalized

    def _align_timestamp(self, index: pd.Index, timestamp: pd.Timestamp) -> pd.Timestamp:
        """Align arbitrary timestamp to the closest index entry."""
        try:
            loc = index.get_indexer([timestamp], method="nearest")[0]
            if loc == -1:
                return cast("pd.Timestamp", index[-1])
            return cast("pd.Timestamp", index[loc])
        except Exception:
            return cast("pd.Timestamp", index[-1])

    def _extract_price(self, row: Series, symbol: str) -> float:
        """Extract a price for the given symbol from the row."""
        candidates = [
            symbol,
            f"{symbol}_close",
            "close",
            "Close",
        ]
        for candidate in candidates:
            value = row.get(candidate, None)  # pandas Series provides .get
            if value is None:
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        if isinstance(row.index, pd.MultiIndex):
            for idx in row.index:
                if not isinstance(idx, tuple) or symbol not in idx:
                    continue
                value = row.get(idx, None)
                if value is None:
                    continue
                try:
                    return float(value)
                except (TypeError, ValueError):
                    continue
        try:
            return float(row.iloc[0])
        except (TypeError, ValueError, IndexError):
            return 0.0
