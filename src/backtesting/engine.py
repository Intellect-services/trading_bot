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
        """Run the backtest simulation"""
        # Initialize strategy and risk manager
        self.strategy.initialize()
        self.risk_manager.initialize()
        
        # Get historical data
        self.data_feed.load_data(start_date, end_date)
        
        # Main simulation loop
        for timestamp in self.data_feed.get_timestamps():
            self.current_time = timestamp
            self.current_data = self.data_feed.get_data(timestamp)
            
            # Update portfolio and positions
            self._update_portfolio()
            
            # Generate signals from strategy
            signals = self.strategy.generate_signals(self.current_data)
            
            # Apply risk management
            signals = self.risk_manager.apply_risk_rules(signals, self.portfolio)
            
            # Execute trades
            self._execute_trades(signals)
            
            # Update performance metrics
            self._update_performance()
        
        # Calculate final performance metrics
        return self._calculate_performance_metrics()
    
    def _update_portfolio(self) -> None:
        """Update portfolio values based on current market data"""
        for symbol, position in self.positions.items():
            if symbol in self.current_data:
                current_price = self.current_data[symbol]['close'].iloc[-1]
                position.update_market_value(current_price)
        
        self.portfolio.update_values()
    
    def _execute_trades(self, signals: Dict[str, Any]) -> None:
        """Execute trades based on signals"""
        for symbol, signal in signals.items():
            if symbol not in self.current_data:
                continue
                
            current_price = self.current_data[symbol]['close'].iloc[-1]
            
            # Calculate position size based on risk management
            position_size = self.risk_manager.calculate_position_size(
                symbol, current_price, self.portfolio
            )
            
            # Create and execute order
            if position_size > 0:
                order = Order(
                    symbol=symbol,
                    quantity=position_size,
                    price=current_price,
                    order_type='market',
                    side='buy',
                    timestamp=self.current_time
                )
                self._execute_order(order)
            elif position_size < 0:
                order = Order(
                    symbol=symbol,
                    quantity=abs(position_size),
                    price=current_price,
                    order_type='market',
                    side='sell',
                    timestamp=self.current_time
                )
                self._execute_order(order)
    
    def _execute_order(self, order: Order) -> None:
        """Execute a single order"""
        # Apply slippage and commission
        execution_price = order.price * (1 + self.slippage if order.side == 'buy' else 1 - self.slippage)
        commission = order.quantity * execution_price * self.commission
        
        # Update portfolio
        if order.side == 'buy':
            self.portfolio.cash -= order.quantity * execution_price + commission
        else:
            self.portfolio.cash += order.quantity * execution_price - commission
        
        # Update position
        if order.symbol not in self.positions:
            self.positions[order.symbol] = Position(order.symbol)
        
        position = self.positions[order.symbol]
        position.update_from_order(order, execution_price)
        
        # Record trade
        trade = Trade(
            symbol=order.symbol,
            quantity=order.quantity,
            price=execution_price,
            side=order.side,
            timestamp=order.timestamp,
            commission=commission
        )
        self.trades.append(trade)
        self.orders.append(order)
    
    def _update_performance(self) -> None:
        """Update performance metrics for current time period"""
        # Update portfolio returns
        self.portfolio.update_returns()
        
        # Update position returns
        for position in self.positions.values():
            position.update_returns()
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate final performance metrics"""
        # Calculate portfolio metrics
        portfolio_returns = self.portfolio.get_returns()
        total_return = (self.portfolio.total_value / self.initial_capital) - 1
        sharpe_ratio = self._calculate_sharpe_ratio(portfolio_returns)
        max_drawdown = self._calculate_max_drawdown(portfolio_returns)
        
        # Calculate trade metrics
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t.pnl > 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'final_portfolio_value': self.portfolio.total_value,
            'final_cash': self.portfolio.cash
        }
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        excess_returns = returns - risk_free_rate/252  # Daily risk-free rate
        if len(excess_returns) < 2:
            return 0.0
        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdowns = (cumulative_returns - running_max) / running_max
        return drawdowns.min() 