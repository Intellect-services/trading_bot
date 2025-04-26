import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
from ..strategies.base import Strategy
from .metrics import calculate_metrics

class BacktestEngine:
    def __init__(self, strategy: Strategy, initial_capital: float = 100000.0):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: Dict[str, Dict[str, float]] = {}
        self.trades: List[Dict[str, Any]] = []
        self.equity_curve: List[Dict[str, Any]] = []
        
    def run(self, data: pd.DataFrame, commission: float = 0.001) -> Dict[str, Any]:
        """Run backtest on historical data"""
        # Generate signals
        signals = self.strategy.generate_signals(data)
        
        # Initialize portfolio
        portfolio = pd.DataFrame(index=signals.index)
        portfolio['signal'] = signals['signal']
        portfolio['price'] = data['close']
        portfolio['position'] = 0
        portfolio['cash'] = self.initial_capital
        portfolio['holdings'] = 0
        portfolio['total'] = self.initial_capital
        
        # Run backtest
        for i in range(1, len(portfolio)):
            current_signal = portfolio['signal'].iloc[i]
            current_price = portfolio['price'].iloc[i]
            
            # Update positions based on signals
            if current_signal == 1:  # Buy signal
                if portfolio['position'].iloc[i-1] <= 0:
                    # Calculate position size (simple fixed fraction of capital)
                    position_size = portfolio['cash'].iloc[i-1] * 0.1  # 10% of cash
                    shares = position_size / current_price
                    
                    # Update portfolio
                    portfolio.loc[portfolio.index[i], 'position'] = shares
                    portfolio.loc[portfolio.index[i], 'cash'] = portfolio['cash'].iloc[i-1] - (shares * current_price * (1 + commission))
                    
                    # Record trade
                    self.trades.append({
                        'timestamp': portfolio.index[i],
                        'type': 'buy',
                        'price': current_price,
                        'shares': shares,
                        'commission': shares * current_price * commission
                    })
                    
            elif current_signal == -1:  # Sell signal
                if portfolio['position'].iloc[i-1] > 0:
                    shares = portfolio['position'].iloc[i-1]
                    
                    # Update portfolio
                    portfolio.loc[portfolio.index[i], 'position'] = 0
                    portfolio.loc[portfolio.index[i], 'cash'] = portfolio['cash'].iloc[i-1] + (shares * current_price * (1 - commission))
                    
                    # Record trade
                    self.trades.append({
                        'timestamp': portfolio.index[i],
                        'type': 'sell',
                        'price': current_price,
                        'shares': shares,
                        'commission': shares * current_price * commission
                    })
            
            else:  # Hold signal
                portfolio.loc[portfolio.index[i], 'position'] = portfolio['position'].iloc[i-1]
                portfolio.loc[portfolio.index[i], 'cash'] = portfolio['cash'].iloc[i-1]
            
            # Update holdings and total portfolio value
            portfolio.loc[portfolio.index[i], 'holdings'] = portfolio['position'].iloc[i] * current_price
            portfolio.loc[portfolio.index[i], 'total'] = portfolio['cash'].iloc[i] + portfolio['holdings'].iloc[i]
            
            # Record equity curve point
            self.equity_curve.append({
                'timestamp': portfolio.index[i],
                'equity': portfolio['total'].iloc[i],
                'cash': portfolio['cash'].iloc[i],
                'holdings': portfolio['holdings'].iloc[i]
            })
        
        # Calculate performance metrics
        returns = portfolio['total'].pct_change().dropna()
        metrics = calculate_metrics(returns, self.trades)
        
        return {
            'portfolio': portfolio,
            'trades': self.trades,
            'equity_curve': self.equity_curve,
            'metrics': metrics
        }
    
    def get_trades(self) -> List[Dict[str, Any]]:
        """Get trade history"""
        return self.trades
    
    def get_equity_curve(self) -> List[Dict[str, Any]]:
        """Get equity curve data"""
        return self.equity_curve 