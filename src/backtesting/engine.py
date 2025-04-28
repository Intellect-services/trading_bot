"""Backtesting engine implementation."""

from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
import numpy as np

from src.core.data_feed import DataFeed
from src.core.portfolio import Portfolio
from src.core.risk_manager import RiskManager
from src.utils.logger import setup_logger
from src.core.alpaca_client import AlpacaClient

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
        self.client = AlpacaClient()
        self.data_feed = DataFeed(self.client)
        
        # Initialize data storage
        self.data: Dict[str, pd.DataFrame] = {}
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

    def _generate_signals(self, date: datetime) -> Dict[str, str]:
        """Generate trading signals for given date.

        Args:
            date: Date to generate signals for

        Returns:
            Dictionary mapping symbols to signals
        """
        signals: Dict[str, str] = {}
        
        for symbol in self.symbols:
            if symbol not in self.data:
                continue
                
            df = self.data[symbol]
            if date not in df.index:
                continue
                
            # Get current values
            sma_20 = float(df.loc[date, 'sma_20'])
            sma_50 = float(df.loc[date, 'sma_50'])
            
            # Get previous values
            prev_idx = df.index.get_loc(date) - 1
            if prev_idx >= 0:
                prev_date = df.index[prev_idx]
                sma_20_prev = float(df.loc[prev_date, 'sma_20'])
                sma_50_prev = float(df.loc[prev_date, 'sma_50'])
                
                # Generate signals based on moving average crossover
                if sma_20 > sma_50 and sma_20_prev <= sma_50_prev:
                    signals[symbol] = 'buy'
                elif sma_20 < sma_50 and sma_20_prev >= sma_50_prev:
                    signals[symbol] = 'sell'
                    
        return signals

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
        current_prices: Dict[str, float] = {}
        
        for symbol in self.symbols:
            if symbol not in self.data:
                continue
            
            if date in self.data[symbol].index:
                price = float(self.data[symbol].loc[date, 'close'])
                current_prices[symbol] = price
                
                # Update position
                position = self.portfolio.get_position(symbol)
                if position:
                    self.portfolio.update_position(
                        symbol=symbol,
                        quantity=position['quantity'],
                        price=price,
                        action='update'
                    )

    def _execute_buy(self, symbol: str, date: datetime) -> bool:
        """Execute buy order.

        Args:
            symbol: Symbol to buy
            date: Date of execution

        Returns:
            True if order executed successfully
        """
        try:
            if date not in self.data[symbol].index:
                return False
                
            price = float(self.data[symbol].loc[date, 'close'])
            position = self.portfolio.get_position(symbol)
            
            # Calculate current portfolio value
            current_prices = {
                sym: float(self.data[sym].loc[date, 'close'])
                for sym in self.symbols
                if date in self.data[sym].index
            }
            portfolio_value = self.portfolio.calculate_portfolio_value(current_prices)
            
            # Check risk management
            position_dict = None
            if position:
                position_dict = {
                    'quantity': position['quantity'],
                    'entry_price': position['entry_price']
                }
                
            if not self.risk_manager.check_position_risk(
                price=price,
                position=position_dict,
                portfolio_value=portfolio_value
            ):
                return False
            
            # Calculate position size
            size = self.risk_manager.calculate_position_size(
                price=price,
                portfolio_value=portfolio_value
            )
            
            # Execute trade
            return bool(self.portfolio.execute_order(
                symbol=symbol,
                qty=size,
                side='buy',
                price=price
            ))
            
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
            if date not in self.data[symbol].index:
                return False
                
            price = float(self.data[symbol].loc[date, 'close'])
            position = self.portfolio.get_position(symbol)
            
            if not position:
                return False
            
            return bool(self.portfolio.execute_order(
                symbol=symbol,
                qty=position['quantity'],
                side='sell',
                price=price
            ))
            
        except Exception as e:
            logger.error("Error executing sell for %s: %s", symbol, e)
            return False

    def _calculate_results(self) -> Dict[str, float]:
        """Calculate backtest results.

        Returns:
            Dictionary containing backtest metrics
        """
        current_prices = {
            symbol: float(self.data[symbol].iloc[-1]['close'])
            for symbol in self.symbols
            if not self.data[symbol].empty
        }
        final_value = self.portfolio.calculate_portfolio_value(current_prices)
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        # Calculate daily returns for Sharpe ratio
        daily_returns = []
        dates = pd.date_range(self.start_date, self.end_date)
        prev_value = self.initial_capital
        
        for date in dates:
            prices = {
                symbol: float(self.data[symbol].loc[date, 'close'])
                for symbol in self.symbols
                if date in self.data[symbol].index
            }
            if prices:
                curr_value = self.portfolio.calculate_portfolio_value(prices)
                daily_return = (curr_value - prev_value) / prev_value
                daily_returns.append(daily_return)
                prev_value = curr_value
        
        # Calculate metrics
        daily_returns_array = np.array(daily_returns)
        sharpe_ratio = np.sqrt(252) * (np.mean(daily_returns_array) / np.std(daily_returns_array)) if len(daily_returns) > 0 else 0.0
        
        # Calculate maximum drawdown
        cumulative_returns = np.cumprod(1 + daily_returns_array)
        rolling_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = abs(float(np.min(drawdowns))) if len(drawdowns) > 0 else 0.0
        
        # Calculate win rate
        trades = self.portfolio.trades
        winning_trades = sum(1 for trade in trades if trade.get('profit', 0) > 0)
        win_rate = winning_trades / len(trades) if trades else 0.0
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate
        }
