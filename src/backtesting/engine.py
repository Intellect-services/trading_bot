"""Backtesting engine module."""

from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import logging

from src.utils.config import Config
from src.core.strategy import Strategy
from src.core.risk_manager import RiskManager
from src.core.portfolio import Portfolio
from src.core.data_feed import DataFeed
from src.utils.logger import setup_logger
from src.strategies.base_strategy import BaseStrategy

logger = setup_logger(__name__)


class BacktestingEngine:
    """Engine for backtesting trading strategies."""

    def __init__(
        self,
        data_feed: DataFeed,
        strategy: BaseStrategy,
        initial_capital: float = 100000.0,
        commission: float = 0.0,
        slippage: float = 0.0
    ) -> None:
        """Initialize backtesting engine.

        Args:
            data_feed: Data feed instance
            strategy: Trading strategy instance
            initial_capital: Initial capital for the portfolio
            commission: Trading commission
            slippage: Trading slippage
        """
        self.data_feed = data_feed
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.portfolio = Portfolio(initial_capital)
        self.logger = logging.getLogger(__name__)
        self.trade_history: List[Dict[str, Any]] = []

    def run(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Run backtest simulation.

        Args:
            start_date: Start date of the backtest
            end_date: End date of the backtest

        Returns:
            Dictionary containing backtest results
        """
        try:
            logger.info("Starting backtest simulation")

            # Get historical data for all symbols
            historical_data = {}
            for symbol in self.strategy.symbols:
                data = self.data_feed.get_historical_data(
                    symbol=symbol,
                    start=start_date.strftime('%Y-%m-%d'),
                    end=end_date.strftime('%Y-%m-%d')
                )
                if not data.empty:
                    historical_data[symbol] = data

            if not historical_data:
                raise ValueError("No historical data available for backtesting")

            # Run backtest
            current_date = start_date
            while current_date <= end_date:
                self._process_trading_day(current_date, historical_data)
                current_date += timedelta(days=1)

            # Calculate and return performance metrics
            metrics = self._calculate_performance_metrics()
            logger.info("Backtest simulation completed")
            return {
                'metrics': metrics,
                'trade_history': self.trade_history
            }

        except Exception as e:
            logger.error(f"Error during backtesting: {str(e)}")
            return {
                'metrics': {
                    'total_return': 0.0,
                    'sharpe_ratio': 0.0,
                    'max_drawdown': 0.0
                },
                'trade_history': []
            }

    def _process_trading_day(self, current_date: datetime, historical_data: Dict[str, pd.DataFrame]) -> None:
        """Process a single trading day."""
        # Update data and generate signals
        for symbol, data in historical_data.items():
            # Get data up to current time
            mask = data.index <= current_date
            current_df = data[mask].copy()
            if current_df.empty:
                continue

            # Generate signals
            signals = self.strategy.generate_signals(current_df)
            if not signals:
                continue

            # Get latest data
            latest_data = current_df.iloc[-1]
            latest_price = float(latest_data['close'])

            # Get current position
            position = self.positions.get(symbol, {})

            # Check risk management
            if not self.risk_manager.apply_risk_management(
                price=latest_price,
                position=position,
                account_value=self.portfolio.current_balance
            ):
                continue

            # Execute trades based on signals
            if signals.get('action') == 'buy' and (not position or position['quantity'] <= 0):
                self._execute_trade(symbol, 1.0, latest_price, 'buy', current_date)
            elif signals.get('action') == 'sell' and position and position['quantity'] > 0:
                self._execute_trade(symbol, position['quantity'], latest_price, 'sell', current_date)

    def _execute_trade(
        self,
        symbol: str,
        quantity: float,
        price: float,
        action: str,
        current_date: datetime
    ) -> None:
        """Execute a simulated trade.

        Args:
            symbol: Trading symbol
            quantity: Trade quantity
            price: Execution price
            action: Trade action (buy/sell)
            current_date: Current date of the trade
        """
        try:
            # Apply slippage
            adjusted_price = price * (1 + self.slippage if action == 'buy' else -self.slippage)

            # Update portfolio
            if not self.portfolio.execute_order(
                symbol=symbol,
                qty=quantity,
                side=action,
                price=adjusted_price
            ):
                return

            # Update positions
            if action == 'buy':
                self.positions[symbol] = {
                    'quantity': quantity,
                    'entry_price': adjusted_price,
                    'timestamp': current_date
                }
            else:
                if symbol in self.positions:
                    del self.positions[symbol]

            # Record trade
            self.trade_history.append({
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': adjusted_price,
                'timestamp': current_date,
                'portfolio_value': self.portfolio.current_balance
            })

            logger.info(
                f"Executed {action} trade: {quantity} {symbol} @ {adjusted_price}"
            )

        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")

    def _calculate_performance_metrics(self) -> Dict[str, float]:
        """Calculate performance metrics for the backtest.

        Returns:
            Dictionary containing performance metrics
        """
        if not self.trade_history:
            return {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0
            }

        trade_df = pd.DataFrame(self.trade_history)
        trade_df['timestamp'] = pd.to_datetime(trade_df['timestamp'])
        trade_df.set_index('timestamp', inplace=True)

        # Calculate daily values and returns
        daily_values = trade_df['portfolio_value'].resample('D').last()
        daily_values = daily_values.fillna(method='ffill')
        daily_returns = daily_values.pct_change().dropna()

        # Calculate metrics
        total_return = (daily_values.iloc[-1] - self.initial_capital) / self.initial_capital
        sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
        max_drawdown = self._calculate_max_drawdown(daily_values)

        return {
            'total_return': float(total_return),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown)
        }

    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """Calculate Sharpe ratio.

        Args:
            returns: Series of returns

        Returns:
            Sharpe ratio value
        """
        if returns.empty or returns.std() == 0:
            return 0.0
        risk_free_rate = 0.02  # Assuming 2% annual risk-free rate
        daily_rf = (1 + risk_free_rate) ** (1/252) - 1
        excess_returns = returns - daily_rf
        return float((excess_returns.mean() / returns.std()) * (252 ** 0.5))

    def _calculate_max_drawdown(self, values: pd.Series) -> float:
        """Calculate maximum drawdown.

        Args:
            values: Series of portfolio values

        Returns:
            Maximum drawdown value
        """
        if values.empty:
            return 0.0
        rolling_max = values.expanding().max()
        drawdowns = values / rolling_max - 1.0
        return float(abs(drawdowns.min()))
