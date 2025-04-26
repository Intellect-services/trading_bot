"""Risk management module."""

from typing import Dict, Any, Optional
import pandas as pd
import logging

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.utils.helpers import format_price

logger = setup_logger(__name__)


class RiskManager:
    """Risk management system for the trading bot."""

    def __init__(self, config: Config) -> None:
        """Initialize risk manager with configuration.
        
        Args:
            config: Trading configuration
        """
        self.config = config
        self._max_position_size = config.RISK_MAX_POSITION_SIZE
        self._stop_loss = config.RISK_STOP_LOSS_PCT
        self._max_drawdown = config.RISK_MAX_DRAWDOWN
        self._max_leverage = config.RISK_MAX_LEVERAGE
        self._risk_per_trade = config.RISK_PER_TRADE
        self.initial_balance = config.INITIAL_BALANCE
        
        logger.info("Risk manager initialized")

    def apply_risk_management(
        self,
        price: float,
        position: Dict[str, Any],
        account_value: float
    ) -> bool:
        """Apply risk management rules to a potential trade.
        
        Args:
            price: Current price of the asset
            position: Current position details
            account_value: Current account value
            
        Returns:
            bool: True if trade passes risk checks, False otherwise
        """
        try:
            # Check position size
            position_value = price * float(position.get('quantity', 0))
            if position_value > self._max_position_size * account_value:
                logger.warning(f"Position size {position_value} exceeds maximum allowed {self._max_position_size * account_value}")
                return False
                
            # Check stop loss
            unrealized_pl_pct = float(position.get('unrealized_pl_pct', 0))
            if unrealized_pl_pct < -self._stop_loss:
                logger.warning(f"Stop loss triggered at {unrealized_pl_pct}%")
                return False
                
            # Check drawdown
            initial_value = float(position.get('initial_value', account_value))
            drawdown = (account_value - initial_value) / account_value
            if drawdown < -self._max_drawdown:
                logger.warning(f"Maximum drawdown exceeded")
                return False
                
            # Check risk per trade
            risk_amount = position_value * self._risk_per_trade
            if risk_amount > account_value * self._risk_per_trade:
                logger.warning(f"Risk per trade {risk_amount} exceeds maximum allowed {account_value * self._risk_per_trade}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error in risk management: {str(e)}")
            return False

    def calculate_stop_loss(self, price: float, quantity: float) -> float:
        """Calculate stop loss price for a position.
        
        Args:
            price: Current price of the asset
            quantity: Position quantity (positive for long, negative for short)
            
        Returns:
            float: Stop loss price
        """
        if quantity > 0:  # Long position
            return price * (1 - self._stop_loss)
        else:  # Short position
            return price * (1 + self._stop_loss)
