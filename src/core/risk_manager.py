"""Risk management module."""

from typing import Dict, Any, Optional
import pandas as pd
import logging

from src.utils.logger import setup_logger
from src.utils.helpers import format_price

logger = setup_logger(__name__)


class RiskManager:
    """Risk management system for the trading bot."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize risk manager with configuration.
        
        Args:
            config: Trading configuration dictionary
        """
        self.config = config
        risk_config = config.get("risk", {})
        self._max_position_size = risk_config.get("max_position_size", 0.1)
        self._stop_loss = risk_config.get("stop_loss", 0.02)
        self._max_drawdown = risk_config.get("max_drawdown", 0.2)
        self._max_leverage = risk_config.get("max_leverage", 2.0)
        self._risk_per_trade = risk_config.get("risk_per_trade", 0.02)
        self._take_profit = risk_config.get("take_profit", 0.04)
        self._peak_value = 0.0  # Track peak portfolio value
        
        logger.info("Risk manager initialized with max_position_size=%.2f, stop_loss=%.2f, max_drawdown=%.2f, max_leverage=%.2f",
                   self._max_position_size, self._stop_loss, self._max_drawdown, self._max_leverage)

    @property
    def max_position_size(self) -> float:
        """Get maximum position size as percentage of portfolio."""
        return self._max_position_size

    @property
    def stop_loss(self) -> float:
        """Get stop loss percentage."""
        return self._stop_loss

    @property
    def take_profit(self) -> float:
        """Get take profit percentage."""
        return self._take_profit

    @property
    def max_drawdown(self) -> float:
        """Get maximum drawdown percentage."""
        return self._max_drawdown

    @property
    def max_leverage(self) -> float:
        """Get maximum leverage ratio."""
        return self._max_leverage

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
            # Update peak value
            self._peak_value = max(self._peak_value, account_value)
            
            # Check position size
            position_value = price * float(position.get('size', 0))
            if position_value > self._max_position_size * account_value:
                logger.warning(f"Position size {position_value} exceeds maximum allowed {self._max_position_size * account_value}")
                return False
                
            # Check stop loss
            if 'avg_price' in position:
                unrealized_pl_pct = (price - position['avg_price']) / position['avg_price']
                if unrealized_pl_pct < -self._stop_loss:
                    logger.warning(f"Stop loss triggered at {unrealized_pl_pct:.2%}")
                    return False
                
            # Check drawdown
            if self._peak_value > 0:
                drawdown = (account_value - self._peak_value) / self._peak_value
                if drawdown < -self._max_drawdown:
                    logger.warning(f"Maximum drawdown exceeded: {drawdown:.2%}")
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

    def calculate_take_profit(self, price: float, quantity: float) -> float:
        """Calculate take profit price for a position.
        
        Args:
            price: Current price of the asset
            quantity: Position quantity (positive for long, negative for short)
            
        Returns:
            float: Take profit price
        """
        if quantity > 0:  # Long position
            return price * (1 + self._take_profit)
        else:  # Short position
            return price * (1 - self._take_profit)

    def calculate_position_size(
        self,
        portfolio_value: float,
        price: float,
        risk_per_trade: Optional[float] = None
    ) -> int:
        """Calculate position size based on risk parameters.
        
        Args:
            portfolio_value: Current portfolio value
            price: Current price of the asset
            risk_per_trade: Risk per trade (optional, uses default if not provided)
            
        Returns:
            int: Number of shares to trade
        """
        try:
            risk = risk_per_trade if risk_per_trade is not None else self._risk_per_trade
            max_position_value = portfolio_value * self._max_position_size
            risk_amount = portfolio_value * risk
            
            # Calculate position size based on both max position size and risk per trade
            position_size_by_max = max_position_value / price
            position_size_by_risk = risk_amount / (price * self._stop_loss)
            
            # Take the minimum of the two calculations
            position_size = min(position_size_by_max, position_size_by_risk)
            
            return int(position_size)  # Round down to nearest whole share
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return 0

    def check_leverage(self, portfolio_value: float, position_value: float) -> bool:
        """Check if leverage is within limits.
        
        Args:
            portfolio_value: Current portfolio value
            position_value: Total position value
            
        Returns:
            bool: True if leverage is acceptable, False otherwise
        """
        try:
            leverage = position_value / portfolio_value
            return leverage <= self._max_leverage
        except Exception as e:
            logger.error(f"Error checking leverage: {str(e)}")
            return False
