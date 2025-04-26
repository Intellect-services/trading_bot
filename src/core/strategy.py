from typing import Dict, List, Optional, Tuple
import logging
import pandas as pd
import numpy as np
from datetime import datetime

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.utils.helpers import calculate_position_size, format_price

logger = setup_logger(__name__)

class Strategy:
    """Base class for trading strategies."""
    
    def __init__(self, config: Config) -> None:
        """Initialize the strategy with configuration.
        
        Args:
            config: Configuration object containing strategy parameters
        """
        self.config = config
        self.name = self.__class__.__name__
        logger.info(f"Initialized {self.name} strategy")
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals based on the input data.
        
        Args:
            data: DataFrame containing price and indicator data
            
        Returns:
            DataFrame with trading signals
        """
        raise NotImplementedError("Subclasses must implement generate_signals")
    
    def calculate_position_size(self, price: float, risk_per_trade: float) -> float:
        """Calculate position size based on risk parameters.
        
        Args:
            price: Current price of the asset
            risk_per_trade: Maximum risk per trade as a percentage of portfolio
            
        Returns:
            Position size in units of the asset
        """
        return calculate_position_size(price, risk_per_trade)
    
    def format_price(self, price: float) -> str:
        """Format price for display.
        
        Args:
            price: Price to format
            
        Returns:
            Formatted price string
        """
        return format_price(price) 