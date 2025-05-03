"""Risk management module."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Optional, Union

from ..utils.config import Config
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class Position:
    """Position details."""

    size: float
    avg_price: float


@dataclass
class RiskConfig:
    """Risk management configuration."""

    max_position_size: float = 0.1
    stop_loss: float = 0.02
    take_profit: float = 0.04
    max_drawdown: float = 0.2
    max_leverage: float = 1.0
    risk_per_trade: float = 0.01
    trailing_stop: float = 0.01
    trailing_stop_activation: float = 0.02


class RiskManager:
    """Risk management class."""

    def __init__(
        self, config: Optional[Union[Config, Dict[str, Union[int, float, str]]]] = None
    ) -> None:
        """Initialize risk manager.

        Args:
            config: Configuration object or dictionary
        """
        if isinstance(config, Config):
            self.config = RiskConfig(
                max_position_size=config.RISK_MAX_POSITION_SIZE,
                stop_loss=config.RISK_STOP_LOSS_PCT,
                take_profit=config.RISK_STOP_LOSS_PCT * 2,
                max_drawdown=config.RISK_MAX_DRAWDOWN,
                max_leverage=config.RISK_MAX_LEVERAGE,
                risk_per_trade=config.RISK_PER_TRADE,
            )
        elif isinstance(config, dict):
            risk_config = config.get("risk", {})
            self.config = RiskConfig(
                max_position_size=float(risk_config.get("max_position_size", 0.1)),
                stop_loss=float(risk_config.get("stop_loss", 0.02)),
                take_profit=float(risk_config.get("take_profit", 0.04)),
                max_drawdown=float(risk_config.get("max_drawdown", 0.2)),
                max_leverage=float(risk_config.get("max_leverage", 1.0)),
                risk_per_trade=float(risk_config.get("risk_per_trade", 0.01)),
                trailing_stop=float(risk_config.get("trailing_stop", 0.01)),
                trailing_stop_activation=float(risk_config.get("trailing_stop_activation", 0.02)),
            )
        else:
            self.config = RiskConfig()

        self.logger = logger
        self.highest_prices: Dict[str, float] = {}
        self.lowest_prices: Dict[str, float] = {}

    @property
    def max_position_size(self) -> float:
        """Get maximum position size."""
        return self.config.max_position_size

    @property
    def stop_loss(self) -> float:
        """Get stop loss percentage."""
        return self.config.stop_loss

    @property
    def take_profit(self) -> float:
        """Get take profit percentage."""
        return self.config.take_profit

    @property
    def max_drawdown(self) -> float:
        """Get maximum drawdown percentage."""
        return self.config.max_drawdown

    @property
    def max_leverage(self) -> float:
        """Get maximum leverage."""
        return self.config.max_leverage

    @property
    def risk_per_trade(self) -> float:
        """Get risk per trade percentage."""
        return self.config.risk_per_trade

    def apply_risk_management(
        self, price: float, position: Optional[Union[Position, Dict[str, float]]], account_value: float
    ) -> bool:
        """Apply risk management rules to a position.

        Args:
            price: Current price
            position: Position details
            account_value: Account value

        Returns:
            bool: True if position meets risk criteria

        Raises:
            ValueError: If price or account_value is not positive
        """
        if price <= 0:
            raise ValueError("Price must be positive")
        if account_value <= 0:
            raise ValueError("Account value must be positive")

        if position is None:
            return True

        # Convert dictionary position to Position object if needed
        if isinstance(position, dict):
            position = Position(size=float(position["size"]), avg_price=float(position["avg_price"]))

        position_value = position.size * price
        if position_value / account_value > self.config.max_position_size:
            self.logger.warning(
                "Position size exceeds maximum: %.2f%%",
                (position_value / account_value) * 100,
            )
            return False

        if not self.check_leverage(account_value, position_value):
            self.logger.warning(
                "Position leverage exceeds maximum: %.2f",
                position_value / account_value,
            )
            return False

        loss_pct = (price - position.avg_price) / position.avg_price
        if loss_pct < -self.config.stop_loss:
            self.logger.warning(
                "Position loss exceeds stop loss: %.2f%%",
                loss_pct * 100,
            )
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
            int: Position size in units

        Raises:
            ValueError: If portfolio_value, price, or risk_factor is not positive
        """
        if portfolio_value <= 0:
            raise ValueError("Portfolio value must be positive")
        if price <= 0:
            raise ValueError("Price must be positive")
        if risk_factor <= 0:
            raise ValueError("Risk factor must be positive")

        try:
            max_position_value = portfolio_value * self.config.max_position_size * risk_factor
            position_size = int(max_position_value / price)
            return max(0, position_size)
        except Exception as e:
            self.logger.error("Error calculating position size: %s", str(e))
            return 0

    def calculate_stop_loss(self, price: float, quantity: float) -> float:
        """Calculate stop loss price.

        Args:
            price: Current price
            quantity: Position quantity

        Returns:
            float: Stop loss price

        Raises:
            ValueError: If price is not positive
        """
        if price <= 0:
            raise ValueError("Price must be positive")

        if quantity > 0:
            return price * (1 - self.config.stop_loss)
        else:
            return price * (1 + self.config.stop_loss)

    def calculate_take_profit(self, price: float, quantity: float) -> float:
        """Calculate take profit price.

        Args:
            price: Current price
            quantity: Position quantity

        Returns:
            float: Take profit price

        Raises:
            ValueError: If price is not positive
        """
        if price <= 0:
            raise ValueError("Price must be positive")

        if quantity > 0:
            return price * (1 + self.config.take_profit)
        else:
            return price * (1 - self.config.take_profit)

    def check_leverage(self, portfolio_value: float, position_value: float) -> bool:
        """Check if leverage is within limits.

        Args:
            portfolio_value: Current portfolio value
            position_value: Position value

        Returns:
            bool: True if leverage is within limits

        Raises:
            ValueError: If portfolio_value or position_value is not positive
        """
        if portfolio_value <= 0:
            raise ValueError("Portfolio value must be positive")
        if position_value < 0:
            raise ValueError("Position value cannot be negative")

        leverage = position_value / portfolio_value
        return leverage <= self.config.max_leverage

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
            bool: True if trade is valid

        Raises:
            ValueError: If price or portfolio_value is not positive
        """
        if price <= 0:
            raise ValueError("Price must be positive")
        if portfolio_value <= 0:
            raise ValueError("Portfolio value must be positive")

        try:
            trade_value = abs(quantity) * price
            if trade_value / portfolio_value > self.config.max_position_size:
                self.logger.warning(
                    "Trade size exceeds maximum: %.2f%%",
                    (trade_value / portfolio_value) * 100,
                )
                return False

            if trade_value / portfolio_value > self.config.risk_per_trade:
                self.logger.warning(
                    "Trade risk exceeds maximum: %.2f%%",
                    (trade_value / portfolio_value) * 100,
                )
                return False

            return True

        except Exception as e:
            self.logger.error("Error validating trade: %s", str(e))
            return False

    def update_trailing_stops(
        self, symbol: str, current_price: float, position_type: str = "long"
    ) -> Optional[float]:
        """Update trailing stops for a position.

        Args:
            symbol: Trading symbol
            current_price: Current price
            position_type: Position type (long/short)

        Returns:
            Optional[float]: New stop price if triggered, None otherwise

        Raises:
            ValueError: If current_price is not positive or position_type is invalid
        """
        if current_price <= 0:
            raise ValueError("Current price must be positive")
        if position_type not in ["long", "short"]:
            raise ValueError("Position type must be 'long' or 'short'")

        try:
            if position_type == "long":
                if symbol not in self.highest_prices:
                    self.highest_prices[symbol] = current_price
                elif current_price > self.highest_prices[symbol]:
                    self.highest_prices[symbol] = current_price

                profit_pct = (current_price - self.highest_prices[symbol]) / self.highest_prices[
                    symbol
                ]
                if profit_pct >= self.config.trailing_stop_activation:
                    stop_price = self.highest_prices[symbol] * (1 - self.config.trailing_stop)
                    if current_price <= stop_price:
                        return stop_price
            else:
                if symbol not in self.lowest_prices:
                    self.lowest_prices[symbol] = current_price
                elif current_price < self.lowest_prices[symbol]:
                    self.lowest_prices[symbol] = current_price

                profit_pct = (self.lowest_prices[symbol] - current_price) / self.lowest_prices[
                    symbol
                ]
                if profit_pct >= self.config.trailing_stop_activation:
                    stop_price = self.lowest_prices[symbol] * (1 + self.config.trailing_stop)
                    if current_price >= stop_price:
                        return stop_price

            return None

        except Exception as e:
            self.logger.error("Error updating trailing stops: %s", str(e))
            return None

    def reset_trailing_stop(self, symbol: str) -> None:
        """Reset trailing stop for a symbol.

        Args:
            symbol: Trading symbol
        """
        self.highest_prices.pop(symbol, None)
        self.lowest_prices.pop(symbol, None)
