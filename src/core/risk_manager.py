"""Risk management module."""

from typing import Dict, Optional
from decimal import Decimal

from src.utils.config import get_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class RiskManager:
    """Risk management class."""

    def __init__(self) -> None:
        """Initialize risk manager."""
        self.max_position_size = float(get_config('RISK_MAX_POSITION_SIZE', 0.1))
        self.stop_loss_pct = float(get_config('RISK_STOP_LOSS_PCT', 0.02))
        self.max_drawdown = float(get_config('RISK_MAX_DRAWDOWN', 0.1))
        self.risk_per_trade = float(get_config('RISK_PER_TRADE', 0.01))
        self.logger = logger

    def check_position_risk(
        self,
        price: float,
        position: Optional[Dict[str, float]],
        portfolio_value: float
    ) -> bool:
        """Check if position meets risk management criteria.

        Args:
            price: Current price of the asset
            position: Current position details
            portfolio_value: Current portfolio value

        Returns:
            True if position meets risk criteria, False otherwise
        """
        try:
            # Check position size
            if position:
                position_value = position['quantity'] * price
                if position_value / portfolio_value > self.max_position_size:
                    logger.warning(
                        "Position size exceeds maximum: %s",
                        position_value / portfolio_value
                    )
                    return False

            # Check stop loss
            if position and position['entry_price']:
                loss_pct = (price - position['entry_price']) / position['entry_price']
                if loss_pct < -self.stop_loss_pct:
                    logger.warning("Stop loss triggered: %s", loss_pct)
                    return False

            # Check drawdown
            if position:
                drawdown = (price - position['entry_price']) / position['entry_price']
                if abs(drawdown) > self.max_drawdown:
                    logger.warning("Maximum drawdown exceeded: %s", drawdown)
                    return False

            # Check risk per trade
            trade_value = price * (position['quantity'] if position else 1.0)
            if trade_value / portfolio_value > self.risk_per_trade:
                logger.warning(
                    "Trade risk exceeds maximum: %s",
                    trade_value / portfolio_value
                )
                return False

            return True

        except Exception as e:
            logger.error("Error checking position risk: %s", e)
            return False

    def calculate_position_size(
        self,
        price: float,
        portfolio_value: float,
        risk_factor: float = 1.0
    ) -> float:
        """Calculate position size based on risk parameters.

        Args:
            price: Current price of the asset
            portfolio_value: Current portfolio value
            risk_factor: Risk factor multiplier (default: 1.0)

        Returns:
            Position size in units
        """
        try:
            # Calculate maximum position value
            max_position_value = portfolio_value * self.max_position_size * risk_factor
            
            # Calculate position size in units
            position_size = max_position_value / price
            
            return position_size

        except Exception as e:
            logger.error("Error calculating position size: %s", e)
            return 0.0

    def validate_trade(
        self,
        symbol: str,
        quantity: float,
        price: float,
        portfolio_value: float
    ) -> bool:
        """Validate if trade meets risk management criteria.

        Args:
            symbol: Trading symbol
            quantity: Trade quantity
            price: Trade price
            portfolio_value: Current portfolio value

        Returns:
            True if trade is valid, False otherwise
        """
        try:
            # Check trade value against portfolio
            trade_value = quantity * price
            if trade_value / portfolio_value > self.max_position_size:
                logger.warning(
                    "Trade size exceeds maximum: %s",
                    trade_value / portfolio_value
                )
                return False

            # Check risk per trade
            if trade_value / portfolio_value > self.risk_per_trade:
                logger.warning(
                    "Trade risk exceeds maximum: %s",
                    trade_value / portfolio_value
                )
                return False

            return True

        except Exception as e:
            logger.error("Error validating trade: %s", e)
            return False
