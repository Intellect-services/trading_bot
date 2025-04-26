"""Backtesting engine module."""
from typing import Any, Dict, List, Optional
from datetime import datetime
import pandas as pd
import numpy as np

from src.core.strategy import Strategy
from src.core.risk_manager import RiskManager
from src.core.data_feed import DataFeed
from src.core.portfolio import Portfolio
from src.core.order import Order
from src.core.position import Position
from src.core.trade import Trade

class BacktestingEngine:
    def __init__(
        self,
        strategy: Strategy,
        risk_manager: RiskManager,
        data_feed: DataFeed,
        initial_capital: float = 100000.0,
        commission: float = 0.001,
        slippage: float = 0.001
    ):
        """Initialize the backtesting engine.

        Args:
            strategy: Trading strategy instance
            risk_manager: Risk management instance
            data_feed: Data feed instance
            initial_capital: Initial capital amount
            commission: Commission rate
            slippage: Slippage rate
        """
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.data_feed = data_feed
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        
        self.portfolio = Portfolio(initial_capital)
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.orders: List[Order] = []
        
        self.current_time: Optional[datetime] = None
        self.current_data: Dict[str, pd.DataFrame] = {}
        
    def run(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Run the backtest simulation.

        Args:
            start_date: Start date for the backtest
            end_date: End date for the backtest

        Returns:
            Dict containing performance metrics
        """
        # Get historical data for the period
        historical_data = self.data_feed.get_historical_data(
            symbol=self.strategy.config['symbol'],
            timeframe=self.strategy.config['timeframe'],
            start=start_date,
            end=end_date
        )
        
        if historical_data is None or historical_data.empty:
            raise ValueError("No historical data available for backtesting")
        
        # Main simulation loop
        for timestamp, data in historical_data.groupby(level=0):
            self.current_time = timestamp
            self.current_data = {self.strategy.config['symbol']: data}
            
            # Update portfolio and positions
            self._update_portfolio()
            
            # Generate signals from strategy
            signals = self.strategy.generate_signals(data)
            
            # Apply risk management
            signals = self.risk_manager.apply_risk_management(signals)
            
            # Execute trades
            self._execute_trades(signals)
            
            # Update performance metrics
            self._update_performance()
        
        # Calculate final performance metrics
        return self._calculate_performance_metrics()
    
    def _update_portfolio(self) -> None:
        """Update portfolio values based on current market data."""
        prices = {}
        for symbol, data in self.current_data.items():
            if not data.empty:
                prices[symbol] = data['close'].iloc[-1]
        
        self.portfolio.update_prices(prices)
    
    def _execute_trades(self, signals: pd.DataFrame) -> None:
        """Execute trades based on signals.

        Args:
            signals: DataFrame containing trading signals
        """
        if signals is None or signals.empty:
            return

        for _, signal in signals.iterrows():
            symbol = signal['symbol']
            if symbol not in self.current_data:
                continue
                
            current_price = self.current_data[symbol]['close'].iloc[-1]
            
            # Calculate position size
            if signal['action'] == 'buy':
                position_size = self.strategy.calculate_position_size(current_price)
            elif signal['action'] == 'sell':
                position_size = -self.strategy.calculate_position_size(current_price)
            else:
                continue
            
            # Update portfolio position
            self.portfolio.update_position(
                symbol=symbol,
                quantity=position_size,
                price=current_price,
                timestamp=self.current_time
            )
    
    def _update_performance(self) -> None:
        """Update performance metrics for current time period."""
        # Portfolio metrics are updated automatically by update_position and update_prices
        pass
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate final performance metrics.

        Returns:
            Dict containing performance metrics
        """
        # Calculate portfolio metrics
        portfolio_returns = self.portfolio.get_returns()
        total_return = (self.portfolio.equity / self.initial_capital) - 1
        sharpe_ratio = self._calculate_sharpe_ratio(portfolio_returns)
        max_drawdown = self._calculate_max_drawdown(portfolio_returns)
        
        # Calculate trade metrics
        total_trades = len(self.portfolio.trades)
        winning_trades = len([t for t in self.portfolio.trades if t['value'] > 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'final_portfolio_value': self.portfolio.equity,
            'final_cash': self.portfolio.cash
        }
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio.

        Args:
            returns: Series of returns
            risk_free_rate: Annual risk-free rate

        Returns:
            float: Sharpe ratio
        """
        excess_returns = returns - risk_free_rate/252  # Daily risk-free rate
        if len(excess_returns) < 2:
            return 0.0
        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown.

        Args:
            returns: Series of returns

        Returns:
            float: Maximum drawdown
        """
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdowns = (cumulative_returns - running_max) / running_max
        return drawdowns.min() 