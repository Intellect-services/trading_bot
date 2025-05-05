"""Risk management module."""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Optional, Union

import pandas as pd

from ..utils.config import Config
from ..utils.logger import setup_logger

logger = logging.getLogger(__name__)


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
    """Risk manager for trading operations."""

    def __init__(
        self,
        initial_capital: float,
        risk_per_trade: float = 0.01,
        max_position_size: float = 0.1,
        stop_loss_pct: float = 0.02,
        take_profit_pct: float = 0.04,
        max_drawdown: float = 0.2,
        max_leverage: float = 2.0,
    ) -> None:
        """Initialize the risk manager.

        Args:
            initial_capital: Initial capital in dollars
            risk_per_trade: Maximum risk per trade as a fraction of capital (default: 1%)
            max_position_size: Maximum position size as a fraction of capital (default: 10%)
            stop_loss_pct: Stop loss percentage (default: 2%)
            take_profit_pct: Take profit percentage (default: 4%)
            max_drawdown: Maximum drawdown allowed (default: 20%)
            max_leverage: Maximum leverage allowed (default: 2.0)
        """
        self.initial_capital = initial_capital
        self._risk_per_trade = risk_per_trade
        self._max_position_size = max_position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self._max_drawdown = max_drawdown
        self._max_leverage = max_leverage

        # Track positions and their risk metrics
        self.positions: Dict[str, Dict[str, float]] = {}
        self.highest_prices: Dict[str, float] = {}
        self.lowest_prices: Dict[str, float] = {}

    @property
    def risk_per_trade(self) -> float:
        """Get the risk per trade percentage."""
        return self._risk_per_trade

    @risk_per_trade.setter
    def risk_per_trade(self, value: float) -> None:
        """Set the risk per trade percentage."""
        if value <= 0 or value > 0.1:  # Max 10% risk per trade
            raise ValueError("Risk per trade must be between 0 and 0.1 (10%)")
        self._risk_per_trade = value

    @property
    def max_position_size(self) -> float:
        """Get the maximum position size."""
        return self._max_position_size

    @max_position_size.setter
    def max_position_size(self, value: float) -> None:
        """Set the maximum position size."""
        if value <= 0 or value > 1:
            raise ValueError("Maximum position size must be between 0 and 1")
        self._max_position_size = value

    @property
    def max_drawdown(self) -> float:
        """Get the maximum drawdown percentage."""
        return self._max_drawdown

    @max_drawdown.setter
    def max_drawdown(self, value: float) -> None:
        """Set the maximum drawdown percentage."""
        if value <= 0 or value > 1:
            raise ValueError("Maximum drawdown must be between 0 and 1")
        self._max_drawdown = value

    @property
    def max_leverage(self) -> float:
        """Get the maximum leverage."""
        return self._max_leverage

    @max_leverage.setter
    def max_leverage(self, value: float) -> None:
        """Set the maximum leverage."""
        if value < 1:
            raise ValueError("Maximum leverage must be at least 1")
        self._max_leverage = value

    def calculate_position_size(self, price: float, symbol: str) -> float:
        """Calculate the position size for a trade.

        Args:
            price: Current price of the asset
            symbol: Asset symbol

        Returns:
            Position size in units
        """
        try:
            # Calculate maximum position value based on capital
            max_position_value = self.initial_capital * self.max_position_size

            # Calculate position size based on risk per trade
            risk_amount = self.initial_capital * self.risk_per_trade
            stop_loss_amount = price * self.stop_loss_pct
            position_size = risk_amount / stop_loss_amount

            # Ensure position size doesn't exceed maximum
            position_value = position_size * price
            if position_value > max_position_value:
                position_size = max_position_value / price

            return position_size
        except Exception as e:
            logger.error(f"Failed to calculate position size: {e}")
            raise

    def get_stop_loss(self, symbol: str) -> Optional[float]:
        """Get the stop loss price for a position.

        Args:
            symbol: Asset symbol

        Returns:
            Stop loss price or None if no position exists
        """
        try:
            if symbol not in self.positions:
                return None

            position = self.positions[symbol]
            return position.get("stop_loss")
        except Exception as e:
            logger.error(f"Failed to get stop loss: {e}")
            raise

    def get_take_profit(self, symbol: str) -> Optional[float]:
        """Get the take profit price for a position.

        Args:
            symbol: Asset symbol

        Returns:
            Take profit price or None if no position exists
        """
        try:
            if symbol not in self.positions:
                return None

            position = self.positions[symbol]
            return position.get("take_profit")
        except Exception as e:
            logger.error(f"Failed to get take profit: {e}")
            raise

    def update_position(
        self,
        symbol: str,
        price: float,
        quantity: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> None:
        """Update position information.

        Args:
            symbol: Asset symbol
            price: Current price
            quantity: Position quantity
            stop_loss: Stop loss price
            take_profit: Take profit price
        """
        try:
            self.positions[symbol] = {
                "price": price,
                "quantity": quantity,
                "stop_loss": stop_loss or price * (1 - self.stop_loss_pct),
                "take_profit": take_profit or price * (1 + self.take_profit_pct),
            }

            # Update highest and lowest prices
            if symbol not in self.highest_prices or price > self.highest_prices[symbol]:
                self.highest_prices[symbol] = price
            if symbol not in self.lowest_prices or price < self.lowest_prices[symbol]:
                self.lowest_prices[symbol] = price
        except Exception as e:
            logger.error(f"Failed to update position: {e}")
            raise

    def reset(self) -> None:
        """Reset the risk manager state."""
        self.positions.clear()
        self.highest_prices.clear()
        self.lowest_prices.clear()

    @property
    def stop_loss(self) -> float:
        """Get stop loss percentage."""
        return self.stop_loss_pct

    @property
    def take_profit(self) -> float:
        """Get take profit percentage."""
        return self.take_profit_pct

    def apply_risk_management(
        self,
        price: float,
        position: Optional[Union[Position, Dict[str, float]]],
        account_value: float,
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
            position = Position(
                size=float(position["size"]), avg_price=float(position["avg_price"])
            )

        position_value = position.size * price
        if position_value / account_value > self.max_position_size:
            logger.warning(
                "Position size exceeds maximum: %.2f%%",
                (position_value / account_value) * 100,
            )
            return False

        if not self.check_leverage(account_value, position_value):
            logger.warning(
                "Position leverage exceeds maximum: %.2f",
                position_value / account_value,
            )
            return False

        loss_pct = (price - position.avg_price) / position.avg_price
        if loss_pct < -self.stop_loss_pct:
            logger.warning(
                "Position loss exceeds stop loss: %.2f%%",
                loss_pct * 100,
            )
            return False

        return True

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
            return price * (1 - self.stop_loss_pct)
        else:
            return price * (1 + self.stop_loss_pct)

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
            return price * (1 + self.take_profit_pct)
        else:
            return price * (1 - self.take_profit_pct)

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
            if trade_value / portfolio_value > self.max_position_size:
                logger.warning(
                    "Trade size exceeds maximum: %.2f%%",
                    (trade_value / portfolio_value) * 100,
                )
                return False

            if trade_value / portfolio_value > self.risk_per_trade:
                logger.warning(
                    "Trade risk exceeds maximum: %.2f%%",
                    (trade_value / portfolio_value) * 100,
                )
                return False

            return True

        except Exception as e:
            logger.error("Error validating trade: %s", str(e))
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
                if profit_pct >= self.risk_per_trade:
                    stop_price = self.highest_prices[symbol] * (1 - self.risk_per_trade)
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
                if profit_pct >= self.risk_per_trade:
                    stop_price = self.lowest_prices[symbol] * (1 + self.risk_per_trade)
                    if current_price >= stop_price:
                        return stop_price

            return None

        except Exception as e:
            logger.error("Error updating trailing stops: %s", str(e))
            return None

    def reset_trailing_stop(self, symbol: str) -> None:
        """Reset trailing stop for a symbol.

        Args:
            symbol: Trading symbol
        """
        self.highest_prices.pop(symbol, None)
        self.lowest_prices.pop(symbol, None)
