"""Risk management module."""

from decimal import Decimal
from typing import Any, Dict, Optional, Union

from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class RiskManager:
    """Risk management class."""

    def __init__(self, config: Union[Config, Dict[str, Any], None] = None) -> None:
        """Initialize risk manager.

        Args:
            config: Configuration object or dictionary
        """
        if isinstance(config, Config):
            self.max_position_size = config.RISK_MAX_POSITION_SIZE
            self.stop_loss = config.RISK_STOP_LOSS_PCT
            self.take_profit = config.RISK_STOP_LOSS_PCT * 2
            self.max_drawdown = config.RISK_MAX_DRAWDOWN
            self.max_leverage = config.RISK_MAX_LEVERAGE
            self.risk_per_trade = config.RISK_PER_TRADE
            self.trailing_stop = 0.01  # Default trailing stop percentage
            self.trailing_stop_activation = 0.02  # Default activation threshold
        elif isinstance(config, dict):
            self.max_position_size = float(config.get("max_position_size", 0.1))
            self.stop_loss = float(config.get("stop_loss", 0.02))
            self.take_profit = float(config.get("take_profit", 0.04))
            self.max_drawdown = float(config.get("max_drawdown", 0.2))
            self.max_leverage = float(config.get("max_leverage", 1.0))
            self.risk_per_trade = float(config.get("risk_per_trade", 0.01))
            self.trailing_stop = float(config.get("trailing_stop", 0.01))
            self.trailing_stop_activation = float(
                config.get("trailing_stop_activation", 0.02)
            )
        else:
            # Default values
            self.max_position_size = 0.1
            self.stop_loss = 0.02
            self.take_profit = 0.04
            self.max_drawdown = 0.2
            self.max_leverage = 1.0
            self.risk_per_trade = 0.01
            self.trailing_stop = 0.01
            self.trailing_stop_activation = 0.02

        self.logger = logger
        self.highest_prices: Dict[
            str, float
        ] = {}  # New: track highest prices for trailing stops
        self.lowest_prices: Dict[
            str, float
        ] = {}  # New: track lowest prices for trailing stops

    def apply_risk_management(
        self, price: float, position: Optional[Dict[str, float]], account_value: float
    ) -> bool:
        """Apply risk management rules to a position.

        Args:
            price: Current price
            position: Position details (optional)
            account_value: Account value

        Returns:
            True if position meets risk criteria, False otherwise
        """
        # If no position, return True as there's no risk
        if position is None:
            return True

        # Check position size
        position_value = position["size"] * price
        if position_value / account_value > self.max_position_size:
            return False

        # Check leverage
        if not self.check_leverage(account_value, position_value):
            return False

        # Check stop loss
        if "avg_price" in position:
            loss_pct = (price - position["avg_price"]) / position["avg_price"]
            if loss_pct < -self.stop_loss:
                return False

        return True

    def calculate_position_size(
        self, portfolio_value: float, price: float, risk_factor: float = 1.0
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
        self, symbol: str, quantity: float, price: float, portfolio_value: float
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
                    "Trade size exceeds maximum: %s", trade_value / portfolio_value
                )
                return False

            # Check risk per trade
            if trade_value / portfolio_value > self.risk_per_trade:
                logger.warning(
                    "Trade risk exceeds maximum: %s", trade_value / portfolio_value
                )
                return False

            return True

        except Exception as e:
            logger.error("Error validating trade: %s", e)
            return False

    def update_trailing_stops(
        self, symbol: str, current_price: float, position_type: str = "long"
    ) -> Optional[float]:
        """Update trailing stops for a position.

        Args:
            symbol: Trading symbol
            current_price: Current price
            position_type: Position type ('long' or 'short')

        Returns:
            Trailing stop price if triggered, None otherwise
        """
        try:
            if position_type == "long":
                # For long positions
                if symbol not in self.highest_prices:
                    self.highest_prices[symbol] = current_price
                elif current_price > self.highest_prices[symbol]:
                    self.highest_prices[symbol] = current_price

                # Calculate profit percentage
                profit_pct = (
                    current_price - self.highest_prices[symbol]
                ) / self.highest_prices[symbol]

                # Check if trailing stop should be activated
                if profit_pct >= self.trailing_stop_activation:
                    trailing_stop_price = self.highest_prices[symbol] * (
                        1 - self.trailing_stop
                    )
                    if current_price <= trailing_stop_price:
                        return trailing_stop_price
            else:
                # For short positions
                if symbol not in self.lowest_prices:
                    self.lowest_prices[symbol] = current_price
                elif current_price < self.lowest_prices[symbol]:
                    self.lowest_prices[symbol] = current_price

                # Calculate profit percentage
                profit_pct = (
                    self.lowest_prices[symbol] - current_price
                ) / self.lowest_prices[symbol]

                # Check if trailing stop should be activated
                if profit_pct >= self.trailing_stop_activation:
                    trailing_stop_price = self.lowest_prices[symbol] * (
                        1 + self.trailing_stop
                    )
                    if current_price >= trailing_stop_price:
                        return trailing_stop_price

            return None

        except Exception as e:
            self.logger.error("Error updating trailing stops: %s", e)
            return None

    def reset_trailing_stop(self, symbol: str) -> None:
        """Reset trailing stop tracking for a symbol.

        Args:
            symbol: Trading symbol
        """
        if symbol in self.highest_prices:
            del self.highest_prices[symbol]
        if symbol in self.lowest_prices:
            del self.lowest_prices[symbol]
