"""Risk management module."""

import logging
from dataclasses import dataclass
from typing import TypedDict

logger = logging.getLogger(__name__)


class Position(TypedDict):
    symbol: str
    size: float
    avg_price: float
    current_price: float
    side: str
    stop_loss: float | None
    take_profit: float | None


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
        trailing_stop_pct: float = 0.01,
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
            trailing_stop_pct: Trailing stop percentage (default: 1%)
        """
        self.initial_capital = initial_capital
        self._risk_per_trade = risk_per_trade
        self._max_position_size = max_position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self._max_drawdown = max_drawdown
        self._max_leverage = max_leverage
        self.trailing_stop_pct = trailing_stop_pct

        # Track positions and their risk metrics
        self.positions: dict[str, dict[str, float]] = {}
        self.highest_prices: dict[str, float] = {}
        self.lowest_prices: dict[str, float] = {}

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

    def calculate_position_size(self, price: float, risk_amount: float) -> float:
        """Calculate position size based on risk amount and price."""
        if price <= 0:
            raise ValueError("Price must be positive")
        if risk_amount <= 0:
            raise ValueError("Risk amount must be positive")

        position_size = risk_amount / price
        max_size = self.initial_capital * self.max_position_size / price
        return min(position_size, max_size)

    def get_stop_loss(self, symbol: str) -> float | None:
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

    def get_take_profit(self, symbol: str) -> float | None:
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
        stop_loss: float | None = None,
        take_profit: float | None = None,
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
        position: Position | dict[str, float] | None = None,
        account_value: float = 0.0,
    ) -> bool:
        """Apply risk management rules to a position."""
        if position is None:
            return True

        # Check position size
        position_value = abs(position["size"] * price)
        if position_value > self.max_position_size * account_value:
            return False

        # Check stop loss
        stop_loss = position.get("stop_loss")
        if stop_loss is not None and price <= stop_loss:
            loss_pct = ((stop_loss - price) / stop_loss) * 100
            logger.warning(f"Position loss exceeds stop loss: {loss_pct:.2f}%")
            return False

        # Check take profit
        take_profit = position.get("take_profit")
        if take_profit is not None and price >= take_profit:
            profit_pct = ((price - take_profit) / take_profit) * 100
            logger.warning(f"Position profit exceeds take profit: {profit_pct:.2f}%")
            return False

        return True

    def calculate_stop_loss(self, price: float, quantity: float) -> float:
        """Calculate stop loss price based on position direction."""
        if price <= 0:
            raise ValueError("Price must be positive")

        if quantity > 0:  # Long position
            return price * (1 - self.stop_loss_pct)
        # Short position
        return price * (1 + self.stop_loss_pct)

    def calculate_take_profit(self, price: float, quantity: float) -> float:
        """Calculate take profit price based on position direction."""
        if price <= 0:
            raise ValueError("Price must be positive")

        if quantity > 0:  # Long position
            return price * (1 + self.take_profit_pct)
        # Short position
        return price * (1 - self.take_profit_pct)

    def check_leverage(self, leverage: float, account_value: float) -> bool:
        """Check if leverage is within acceptable limits."""
        if account_value <= 0:
            raise ValueError("Account value must be positive")

        return leverage <= self.max_leverage

    def validate_trade(
        self,
        symbol: str,  # noqa: ARG002
        quantity: float,
        price: float,
        portfolio_value: float,
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

    def update_trailing_stops(self, positions: dict[str, Position]) -> None:
        """Update trailing stops for open positions."""
        for symbol, position in positions.items():
            try:
                current_price = float(position["current_price"])
                float(position["avg_price"])
                stop_price = position["stop_loss"]
                if stop_price is None:
                    continue
                # Calculate new stop price based on trailing percentage
                if position["side"] == "long":
                    new_stop = current_price * (1 - self.trailing_stop_pct)
                    if new_stop > stop_price:
                        self.update_stop_loss(position, current_price)
                else:  # short position
                    new_stop = current_price * (1 + self.trailing_stop_pct)
                    if new_stop < stop_price:
                        self.update_stop_loss(position, current_price)
            except (ValueError, AttributeError) as e:
                logger.error(f"Error updating trailing stop for {symbol}: {e}")
                continue

    def reset_trailing_stop(self, symbol: str) -> None:
        """Reset trailing stop for a symbol.

        Args:
            symbol: Trading symbol
        """
        self.highest_prices.pop(symbol, None)
        self.lowest_prices.pop(symbol, None)

    def update_stop_loss(self, position: Position, current_price: float) -> None:
        """Update trailing stop loss for a position."""
        stop_loss = position["stop_loss"]
        if stop_loss is None:
            return
        if position["side"] == "long":
            new_stop = current_price * (1 - self.trailing_stop_pct)
            if new_stop > stop_loss:
                position["stop_loss"] = new_stop
        else:  # short position
            new_stop = current_price * (1 + self.trailing_stop_pct)
            if new_stop < stop_loss:
                position["stop_loss"] = new_stop
