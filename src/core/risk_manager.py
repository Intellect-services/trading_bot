from typing import Dict, List, Optional
import logging
import pandas as pd
import numpy as np

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.utils.helpers import calculate_position_size, format_price

logger = setup_logger(__name__)

class RiskManager:
    """Manages risk for trading strategies."""
    
    def __init__(self, config: Config) -> None:
        """Initialize the risk manager with configuration.
        
        Args:
            config: Configuration object containing risk parameters
        """
        self.config = config
        self.max_drawdown = config.get('risk.max_drawdown', 0.2)
        self.max_leverage = config.get('risk.max_leverage', 2.0)
        self.stop_loss = config.get('risk.stop_loss', 0.02)
        self.take_profit = config.get('risk.take_profit', 0.04)
        logger.info("Initialized risk manager")
    
    def apply_risk_management(self, signals: pd.DataFrame) -> pd.DataFrame:
        """Apply risk management rules to trading signals.
        
        Args:
            signals: DataFrame containing trading signals
            
        Returns:
            DataFrame with risk-adjusted signals
        """
        if signals.empty:
            return signals
            
        # Apply stop loss and take profit
        signals['stop_loss'] = signals['price'] * (1 - self.stop_loss)
        signals['take_profit'] = signals['price'] * (1 + self.take_profit)
        
        # Calculate position sizes
        signals['position_size'] = signals.apply(
            lambda x: self.calculate_position_size(x['price'], self.config.get('risk.risk_per_trade', 0.01)),
            axis=1
        )
        
        return signals
    
    def calculate_position_size(self, price: float, risk_per_trade: float) -> float:
        """Calculate position size based on risk parameters.
        
        Args:
            price: Current price of the asset
            risk_per_trade: Maximum risk per trade as a percentage of portfolio
            
        Returns:
            Position size in units of the asset
        """
        return calculate_position_size(price, risk_per_trade)
    
    def check_stop_loss(self, current_price: float, entry_price: float) -> bool:
        """Check if stop loss has been hit.
        
        Args:
            current_price: Current price of the asset
            entry_price: Entry price of the position
            
        Returns:
            True if stop loss has been hit, False otherwise
        """
        return current_price <= entry_price * (1 - self.stop_loss)
    
    def check_take_profit(self, current_price: float, entry_price: float) -> bool:
        """Check if take profit has been hit.
        
        Args:
            current_price: Current price of the asset
            entry_price: Entry price of the position
            
        Returns:
            True if take profit has been hit, False otherwise
        """
        return current_price >= entry_price * (1 + self.take_profit)
    
    def check_max_drawdown(self, portfolio_value: float, peak_value: float) -> bool:
        """Check if maximum drawdown has been exceeded.
        
        Args:
            portfolio_value: Current portfolio value
            peak_value: Peak portfolio value
            
        Returns:
            True if maximum drawdown has been exceeded, False otherwise
        """
        drawdown = (peak_value - portfolio_value) / peak_value
        return drawdown > self.max_drawdown
    
    def check_leverage(self, position_value: float, portfolio_value: float) -> bool:
        """Check if leverage exceeds maximum allowed.
        
        Args:
            position_value: Value of the position
            portfolio_value: Current portfolio value
            
        Returns:
            True if leverage is within limits, False otherwise
        """
        leverage = position_value / portfolio_value
        return leverage <= self.max_leverage 