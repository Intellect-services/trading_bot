from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd

class Strategy(ABC):
    def __init__(self, params: Dict[str, Any] = None):
        self.params = params or {}
        self.name = self.__class__.__name__
        self.positions = {}
        self.trades = []
        
    @abstractmethod
    def calculate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate trading signals based on the strategy logic"""
        pass
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate buy/sell signals based on the strategy"""
        pass
    
    def update_position(self, symbol: str, quantity: float, price: float, side: str):
        """Update position information"""
        if symbol not in self.positions:
            self.positions[symbol] = {
                'quantity': 0,
                'avg_price': 0,
                'total_cost': 0
            }
        
        position = self.positions[symbol]
        if side == 'buy':
            new_quantity = position['quantity'] + quantity
            new_cost = position['total_cost'] + (quantity * price)
            position['quantity'] = new_quantity
            position['total_cost'] = new_cost
            position['avg_price'] = new_cost / new_quantity if new_quantity > 0 else 0
        elif side == 'sell':
            position['quantity'] -= quantity
            position['total_cost'] = position['quantity'] * position['avg_price']
            
        # Record the trade
        self.trades.append({
            'timestamp': pd.Timestamp.now(),
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'side': side
        })
    
    def get_position(self, symbol: str) -> Optional[Dict[str, float]]:
        """Get current position for a symbol"""
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> Dict[str, Dict[str, float]]:
        """Get all current positions"""
        return self.positions
    
    def get_trade_history(self) -> list:
        """Get trade history"""
        return self.trades 