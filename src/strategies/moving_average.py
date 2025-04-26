import pandas as pd
import numpy as np
from typing import Dict, Any
from .base import Strategy

class MovingAverageCrossover(Strategy):
    def __init__(self, params: Dict[str, Any] = None):
        default_params = {
            'short_window': 20,
            'long_window': 50,
            'signal_threshold': 0.01
        }
        if params:
            default_params.update(params)
        super().__init__(default_params)
        
    def calculate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate moving averages and their crossover signals"""
        df = data.copy()
        
        # Calculate moving averages
        df['short_ma'] = df['close'].rolling(window=self.params['short_window']).mean()
        df['long_ma'] = df['close'].rolling(window=self.params['long_window']).mean()
        
        # Calculate the difference between moving averages
        df['ma_diff'] = df['short_ma'] - df['long_ma']
        
        # Calculate percentage difference
        df['ma_diff_pct'] = df['ma_diff'] / df['long_ma']
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals based on moving average crossover"""
        df = self.calculate_signals(data)
        
        # Initialize signal column
        df['signal'] = 0
        
        # Generate signals
        df.loc[df['ma_diff_pct'] > self.params['signal_threshold'], 'signal'] = 1  # Buy signal
        df.loc[df['ma_diff_pct'] < -self.params['signal_threshold'], 'signal'] = -1  # Sell signal
        
        # Remove signals during the warmup period
        df.loc[:self.params['long_window'], 'signal'] = 0
        
        return df
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters"""
        return self.params
    
    def set_parameters(self, params: Dict[str, Any]):
        """Update strategy parameters"""
        self.params.update(params) 