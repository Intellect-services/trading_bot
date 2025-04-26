"""Mock trading bot for testing."""

from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd

from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class MockBot:
    """Mock trading bot for testing purposes."""
    
    def __init__(self, config: Config):
        """Initialize mock bot.
        
        Args:
            config: Configuration instance
        """
        self.config = config
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.portfolio_value = config.INITIAL_BALANCE
        
    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get position for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Position dictionary if exists, None otherwise
        """
        return self.positions.get(symbol)
        
    def get_portfolio_value(self) -> float:
        """Get current portfolio value.
        
        Returns:
            Current portfolio value
        """
        return self.portfolio_value
        
    def execute_trade(self, symbol: str, quantity: float, price: float, side: str) -> bool:
        """Execute a mock trade.
        
        Args:
            symbol: Trading symbol
            quantity: Trade quantity
            price: Trade price
            side: Trade side (buy/sell)
            
        Returns:
            True if trade executed successfully
        """
        try:
            trade_value = quantity * price
            
            if side == "buy":
                if trade_value > self.portfolio_value:
                    logger.warning("Insufficient funds for trade")
                    return False
                    
                self.portfolio_value -= trade_value
                if symbol in self.positions:
                    self.positions[symbol]["quantity"] += quantity
                else:
                    self.positions[symbol] = {
                        "quantity": quantity,
                        "entry_price": price,
                        "timestamp": datetime.now()
                    }
            else:  # sell
                if symbol not in self.positions or self.positions[symbol]["quantity"] < quantity:
                    logger.warning("Insufficient position for trade")
                    return False
                    
                self.portfolio_value += trade_value
                self.positions[symbol]["quantity"] -= quantity
                if self.positions[symbol]["quantity"] <= 0:
                    del self.positions[symbol]
                    
            return True
            
        except Exception as e:
            logger.error("Error executing mock trade: %s", e)
            return False
