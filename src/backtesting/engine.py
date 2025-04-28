"""Backtesting engine module."""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, cast
import pandas as pd
import numpy as np
from decimal import Decimal

from src.core.strategy import Strategy
from src.core.risk_manager import RiskManager
from src.core.portfolio import Portfolio
from src.core.data_feed import DataFeed
from src.core.alpaca_client import AlpacaClient
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class BacktestingEngine:
    """Backtesting engine for testing trading strategies."""

    def __init__(
        self,
        strategy: Strategy,
        symbols: List[str],
        initial_capital: float = 100000.0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> None:
        """Initialize backtesting engine.

        Args:
            strategy: Trading strategy
            symbols: List of symbols to backtest
            initial_capital: Initial capital
            start_date: Start date for backtest
            end_date: End date for backtest
        """
        self.strategy = strategy
        self.symbols = symbols
        self.portfolio = Portfolio(initial_capital)
        self.risk_manager = RiskManager()
        self.client = AlpacaClient()
        self.data_feed = DataFeed(self.client)
        self.start_date = start_date or datetime.now() - timedelta(days=365)
        self.end_date = end_date or datetime.now()
        self.data: Dict[str, pd.DataFrame] = {}
        self.results: Dict[str, Any] = {}
        self._load_data()

    def _load_data(self) -> None:
        """Load historical data for all symbols."""
        for symbol in self.symbols:
            data = self.data_feed.get_historical_data(
                symbol,
                start=self.start_date,
                end=self.end_date
            )
            if not data.empty:
                self.data[symbol] = data

    def _generate_signals(self, symbol: str) -> pd.Series:
        """Generate trading signals for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Series of trading signals
        """
        df = self.data[symbol]
        signals = pd.Series(0, index=df.index)
        
        # Calculate moving averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        
        # Generate signals
        signals.loc[df['sma_20'] > df['sma_50']] = 1
        signals.loc[df['sma_20'] < df['sma_50']] = -1
        
        return signals

    def run(self) -> Dict[str, Any]:
        """Run backtest.

        Returns:
            Dictionary with backtest results
        """
        for symbol in self.symbols:
            if symbol not in self.data:
                continue
                
            signals = self._generate_signals(symbol)
            df = self.data[symbol]
            
            for i in range(1, len(df)):
                current_date = df.index[i]
                current_price = float(df.iloc[i]['close'])
                signal = signals.iloc[i]
                
                # Get current position
                position = self.portfolio.get_position(symbol)
                position_dict = None if position is None else {
                    'size': float(position['quantity']),
                    'avg_price': float(position['entry_price'])
                }
                
                # Check risk management
                if not self.risk_manager.apply_risk_management(
                    price=current_price,
                    position=position_dict,
                    account_value=self.portfolio.current_balance
                ):
                    continue
                
                # Execute trade based on signal
                if signal > 0 and (position is None or position['quantity'] <= 0):
                    # Buy signal
                    position_size = self.risk_manager.calculate_position_size(
                        portfolio_value=self.portfolio.current_balance,
                        price=current_price
                    )
                    if position_size > 0:
                        self.portfolio.execute_order(
                            symbol=symbol,
                            qty=position_size,
                            side='buy',
                            price=current_price
                        )
                elif signal < 0 and position is not None and position['quantity'] > 0:
                    # Sell signal
                    self.portfolio.execute_order(
                        symbol=symbol,
                        qty=position['quantity'],
                        side='sell',
                        price=current_price
                    )
            
            # Calculate results
            self._calculate_results(symbol)
        
        return self.results

    def _calculate_results(self, symbol: str) -> None:
        """Calculate backtest results for a symbol.

        Args:
            symbol: Trading symbol
        """
        df = self.data[symbol]
        trades = [t for t in self.portfolio.trades if t['symbol'] == symbol]
        
        if not trades:
            return
            
        # Calculate returns
        daily_returns = df['close'].pct_change()
        daily_returns_array = daily_returns.to_numpy()
        cumulative_returns = np.cumprod(1 + daily_returns_array) - 1
        
        # Calculate metrics
        sharpe_ratio = np.sqrt(252) * daily_returns.mean() / daily_returns.std()
        max_drawdown = (cumulative_returns.max() - cumulative_returns) / (1 + cumulative_returns.max())
        
        self.results[symbol] = {
            'total_return': float(cumulative_returns[-1]),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown.max()),
            'num_trades': len(trades),
            'win_rate': sum(1 for t in trades if t.get('pnl', 0) > 0) / len(trades) if trades else 0.0
        }
