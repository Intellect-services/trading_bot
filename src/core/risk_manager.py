"""Risk management module."""

from typing import Dict, Optional, Any
from decimal import Decimal

from src.utils.config import get_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class RiskManager:
    """Risk management class."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize risk manager.
        
        Args:
            config: Configuration dictionary (optional)
        """
        if config and 'risk' in config:
            risk_config = config['risk']
            self.max_position_size = float(risk_config.get('max_position_size', 0.1))
            self.stop_loss = float(risk_config.get('stop_loss_pct', 0.02))  # Renamed for test compatibility
            self.take_profit = float(risk_config.get('take_profit', 0.04))  # Added for test compatibility
            self.max_drawdown = float(risk_config.get('max_drawdown', 0.1))
            self.risk_per_trade = float(risk_config.get('risk_per_trade', 0.01))
            self.max_leverage = float(risk_config.get('max_leverage', 2.0))
        else:
            self.max_position_size = float(get_config('RISK_MAX_POSITION_SIZE', 0.1))
            self.stop_loss = float(get_config('RISK_STOP_LOSS_PCT', 0.02))  # Renamed for test compatibility
            self.take_profit = float(get_config('RISK_TAKE_PROFIT', 0.04))  # Added for test compatibility
            self.max_drawdown = float(get_config('RISK_MAX_DRAWDOWN', 0.1))
            self.risk_per_trade = float(get_config('RISK_PER_TRADE', 0.01))
            self.max_leverage = float(get_config('RISK_MAX_LEVERAGE', 2.0))
        self.logger = logger

    def apply_risk_management(
        self,
        price: float,
        position: Dict[str, float],
        account_value: float
    ) -> bool:
        """Apply risk management rules to a position.

        Args:
            price: Current price
            position: Position details
            account_value: Account value

        Returns:
            True if position meets risk criteria, False otherwise
        """
        # Check position size
        position_value = position['size'] * price
        if position_value / account_value > self.max_position_size:
            return False

        # Check leverage
        if not self.check_leverage(account_value, position_value):
            return False

        # Check stop loss
        if 'avg_price' in position:
            loss_pct = (price - position['avg_price']) / position['avg_price']
            if loss_pct < -self.stop_loss:
                return False

        return True

    def calculate_position_size(
        self,
        portfolio_value: float,
        price: float,
        risk_factor: float = 1.0
    ) -> int:
        """Calculate position size based on risk parameters.

        Args:
            portfolio_value: Current portfolio value
            price: Current price
            risk_factor: Risk factor multiplier (default: 1.0)

        Returns:
            Position size in units (as integer)
        """
        try:
            # Calculate maximum position value
            max_position_value = portfolio_value * self.max_position_size * risk_factor
            
            # Calculate position size in units and round down to nearest integer
            position_size = int(max_position_value / price)
            
            return position_size

        except Exception as e:
            logger.error("Error calculating position size: %s", e)
            return 0

    def calculate_stop_loss(self, price: float, quantity: float) -> float:
        """Calculate stop loss price.

        Args:
            price: Current price
            quantity: Position quantity

        Returns:
            Stop loss price
        """
        # For long positions, stop loss is below entry price
        # For short positions, stop loss is above entry price
        if quantity > 0:
            return price * (1 - self.stop_loss)
        else:
            return price * (1 + self.stop_loss)

    def calculate_take_profit(self, price: float, quantity: float) -> float:
        """Calculate take profit price.

        Args:
            price: Current price
            quantity: Position quantity

        Returns:
            Take profit price
        """
        # For long positions, take profit is above entry price
        # For short positions, take profit is below entry price
        if quantity > 0:
            return price * (1 + self.take_profit)
        else:
            return price * (1 - self.take_profit)

    def check_leverage(self, portfolio_value: float, position_value: float) -> bool:
        """Check if leverage is within limits.

        Args:
            portfolio_value: Current portfolio value
            position_value: Position value

        Returns:
            True if leverage is within limits, False otherwise
        """
        leverage = position_value / portfolio_value
        return leverage <= self.max_leverage

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
