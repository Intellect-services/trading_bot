"""Backtesting engine implementation."""

from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

from src.core.data_feed import DataFeed
from src.core.portfolio import Portfolio
from src.core.risk_manager import RiskManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class BacktestingEngine:
    """Engine for running backtests."""

    def __init__(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 100000.0,
    ) -> None:
        """Initialize backtesting engine.

        Args:
            symbols: List of symbols to trade
            start_date: Start date for backtest
            end_date: End date for backtest
            initial_capital: Initial capital for backtest
        """
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        
        self.portfolio = Portfolio(initial_capital)
        self.risk_manager = RiskManager()
        self.data_feed = DataFeed()
        
        self._initialize_data()

    def _initialize_data(self) -> None:
        """Initialize historical data for backtesting."""
        for symbol in self.symbols:
            data = self.data_feed.get_historical_data(
                symbol=symbol,
                start=self.start_date,
                end=self.end_date
            )
            if data.empty:
                logger.warning("No data found for %s", symbol)
                continue
            
            # Calculate technical indicators
            self._calculate_indicators(data)
            
            # Store data
            self.data[symbol] = data

    def _calculate_indicators(self, data: pd.DataFrame) -> None:
        """Calculate technical indicators for strategy.

        Args:
            data: DataFrame containing price data
        """
        # Calculate moving averages
        data['sma_20'] = data['close'].rolling(window=20).mean()
        data['sma_50'] = data['close'].rolling(window=50).mean()
        
        # Calculate RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))

    def run(self) -> Dict[str, float]:
        """Run backtest.

        Returns:
            Dictionary containing backtest results
        """
        results = {
            'total_return': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0
        }
        
        try:
            # Iterate through each day
            dates = pd.date_range(self.start_date, self.end_date)
            for date in dates:
                # Update portfolio values
                self._update_portfolio(date)
                
                # Generate signals
                signals = self._generate_signals(date)
                
                # Execute trades
                for symbol, signal in signals.items():
                    if signal == 'buy':
                        self._execute_buy(symbol, date)
                    elif signal == 'sell':
                        self._execute_sell(symbol, date)
            
            # Calculate final results
            results = self._calculate_results()
            
        except Exception as e:
            logger.error("Error running backtest: %s", e)
        
        return results

    def _update_portfolio(self, date: datetime) -> None:
        """Update portfolio values for given date.

        Args:
            date: Date to update portfolio for
        """
        for symbol in self.symbols:
            if symbol not in self.data:
                continue
            
            price = self.data[symbol].loc[date, 'close']
            self.portfolio.update_position_value(symbol, price)

    def _execute_buy(self, symbol: str, date: datetime) -> bool:
        """Execute buy order.

        Args:
            symbol: Symbol to buy
            date: Date of execution

        Returns:
            True if order executed successfully
        """
        try:
            price = self.data[symbol].loc[date, 'close']
            position = self.portfolio.get_position(symbol)
            
            # Check risk management
            if not self.risk_manager.check_position_risk(
                price=price,
                position=position,
                portfolio_value=self.portfolio.total_value
            ):
                return False
            
            # Calculate position size
            size = self.position_sizer.calculate_position_size(
                price=price,
                portfolio_value=self.portfolio.total_value
            )
            
            # Execute trade
            return self.portfolio.execute_buy(
                symbol=symbol,
                quantity=size,
                price=price
            )
            
        except Exception as e:
            logger.error("Error executing buy for %s: %s", symbol, e)
            return False

    def _execute_sell(self, symbol: str, date: datetime) -> bool:
        """Execute sell order.

        Args:
            symbol: Symbol to sell
            date: Date of execution

        Returns:
            True if order executed successfully
        """
        try:
            price = self.data[symbol].loc[date, 'close']
            position = self.portfolio.get_position(symbol)
            
            if not position:
                return False
            
            return self.portfolio.execute_sell(
                symbol=symbol,
                quantity=position['quantity'],
                price=price
            )
            
        except Exception as e:
            logger.error("Error executing sell for %s: %s", symbol, e)
            return False

    def _calculate_results(self) -> Dict[str, float]:
        """Calculate backtest results.

        Returns:
            Dictionary containing backtest metrics
        """
        return {
            'total_return': self.portfolio.total_return,
            'sharpe_ratio': self.portfolio.sharpe_ratio,
            'max_drawdown': self.portfolio.max_drawdown,
            'win_rate': self.portfolio.win_rate
        }
