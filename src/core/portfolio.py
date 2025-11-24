"""Portfolio management module."""

from datetime import datetime
from typing import Any, TypedDict

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class PositionDict(TypedDict):
    """Type definition for position dictionary."""

    size: float
    cost: float
    avg_price: float
    current_price: float
    entry_price: float


class OrderDict(TypedDict):
    """Type definition for order dictionary."""

    symbol: str
    qty: float
    side: str
    price: float
    timestamp: datetime


class Portfolio:
    """Portfolio management class."""

    def __init__(self, initial_capital: float) -> None:
        """Initialize portfolio with initial capital.

        Args:
            initial_capital: Initial capital amount
        """
        self.initial_capital = float(initial_capital)
        self.current_balance = float(initial_capital)
        self.max_position_size = 0.1  # Maximum position size as fraction of portfolio
        self.commission = 0.001  # 0.1% commission
        self.positions: dict[str, PositionDict] = {}
        self.trades: list[OrderDict] = []
        # Backwards compatibility with older code paths referencing trade_history
        self.trade_history = self.trades
        self.peak_value = float(initial_capital)
        logger.info("Portfolio initialized with %.2f capital", initial_capital)

    def get_value(self) -> float:
        """Get current portfolio value.

        Returns:
            Current portfolio value
        """
        try:
            total_value = self.current_balance
            for _symbol, position in self.positions.items():
                total_value += position["size"] * position["current_price"]
            return total_value
        except Exception as e:
            logger.error(f"Error getting portfolio value: {e}")
            return self.current_balance

    def get_balance(self) -> float:
        """Get current cash balance.

        Returns:
            Current cash balance
        """
        return self.current_balance

    def get_position(self, symbol: str) -> PositionDict | None:
        """Get position for a symbol.

        Args:
            symbol: Symbol to get position for

        Returns:
            Position dictionary or None if no position exists
        """
        return self.positions.get(symbol)

    def get_all_positions(self) -> dict[str, PositionDict]:
        """Get all positions.

        Returns:
            Dictionary of all positions
        """
        return self.positions

    def calculate_position_size(self, price: float) -> float:
        """Calculate position size based on risk parameters.

        Args:
            price: Current price of the asset

        Returns:
            Position size in number of shares
        """
        try:
            risk_per_trade = 0.02  # 2% risk per trade
            portfolio_value = self.get_value()
            risk_amount = portfolio_value * risk_per_trade
            position_size = risk_amount / price
            return round(position_size, 2)
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.0

    def execute_order(self, symbol: str, qty: float, side: str, price: float) -> OrderDict:
        """Execute a trading order.

        Args:
            symbol: Symbol to trade
            qty: Quantity to trade
            side: Order side ("buy" or "sell")
            price: Execution price

        Returns:
            Order details dictionary
        """
        try:
            order: OrderDict = {
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "price": price,
                "timestamp": datetime.now(),
            }

            side_lower = side.lower()
            if side_lower == "buy":
                cost = qty * price
                if cost > self.current_balance:
                    logger.warning("Insufficient funds for buy order")
                    return order

                self.current_balance -= cost
                if symbol in self.positions:
                    position = self.positions[symbol]
                    previous_size = position["size"]
                    previous_cost = position["cost"]
                    new_size = previous_size + qty
                    new_cost = previous_cost + cost
                    position["size"] = new_size
                    position["cost"] = new_cost
                    position["avg_price"] = new_cost / new_size
                    position["current_price"] = price
                else:
                    self.positions[symbol] = {
                        "size": qty,
                        "cost": cost,
                        "avg_price": price,
                        "current_price": price,
                        "entry_price": price,
                    }

            elif side_lower == "sell":
                if symbol not in self.positions:
                    logger.warning("No position to sell")
                    return order

                position = self.positions[symbol]
                previous_size = position["size"]
                if previous_size < qty:
                    logger.warning("Insufficient shares for sell order")
                    return order

                proceeds = qty * price
                self.current_balance += proceeds

                new_size = previous_size - qty
                if new_size == 0:
                    del self.positions[symbol]
                else:
                    previous_cost = position["cost"]
                    position["size"] = new_size
                    cost_ratio = new_size / previous_size if previous_size else 0.0
                    position["cost"] = previous_cost * cost_ratio
                    position["avg_price"] = position["cost"] / new_size if new_size else 0.0
                    position["current_price"] = price

            else:
                logger.warning("Unsupported order side: %s", side)
                return order

            self.trades.append(order)
            self.peak_value = max(self.peak_value, self.get_value())
            logger.info("Executed %s order: %s", side, order)
            return order
        except Exception as e:
            logger.error(f"Error executing order: {e}")
            return order

    def update_prices(self, prices: dict[str, float]) -> None:
        """Update current prices for positions.

        Args:
            prices: Dictionary mapping symbols to current prices
        """
        try:
            for symbol, price in prices.items():
                if symbol in self.positions:
                    self.positions[symbol]["current_price"] = price
            self.peak_value = max(self.peak_value, self.get_value())
        except Exception as e:
            logger.error(f"Error updating prices: {e}")

    def get_summary(self) -> dict[str, Any]:
        """Get portfolio summary.

        Returns:
            Dictionary containing portfolio summary
        """
        try:
            current_value = self.get_value()
            return {
                "initial_capital": self.initial_capital,
                "current_balance": self.current_balance,
                "current_value": current_value,
                "peak_value": self.peak_value,
                "total_return": (current_value - self.initial_capital) / self.initial_capital,
                "positions": self.positions,
                "trades": len(self.trades),
            }
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {}

    def update_position(self, symbol: str, quantity: float, price: float, action: str) -> bool:
        """Update position for a symbol.

        Args:
            symbol: Trading symbol
            quantity: Trade quantity
            price: Trade price
            action: Trade action (buy/sell)

        Returns:
            True if position updated successfully
        """
        try:
            cost = quantity * price
            commission = cost * 0.001  # 0.1% commission

            if action == "buy":
                total_cost = cost + commission
                if total_cost > self.current_balance:
                    logger.warning("Insufficient funds for trade")
                    return False
                self.current_balance -= total_cost
                if symbol in self.positions:
                    self.positions[symbol]["size"] += quantity
                    self.positions[symbol]["cost"] = (
                        self.positions[symbol]["cost"] * self.positions[symbol]["size"] + cost
                    ) / (self.positions[symbol]["size"] + quantity)
                else:
                    self.positions[symbol] = {
                        "size": quantity,
                        "cost": cost,
                        "avg_price": price,
                        "current_price": price,
                        "entry_price": price,
                    }
            else:  # sell
                if symbol not in self.positions:
                    logger.warning("No position to sell")
                    return False
                if quantity > self.positions[symbol]["size"]:
                    logger.warning("Insufficient quantity to sell")
                    return False
                self.current_balance += cost - commission
                self.positions[symbol]["size"] -= quantity
                if self.positions[symbol]["size"] <= 0:
                    del self.positions[symbol]

            return True
        except Exception as e:
            logger.error(f"Error updating position: {e}")
            return False

    def get_returns(self) -> float:
        """Calculate total returns.

        Returns:
            Total returns as a percentage
        """
        try:
            current_value = self.get_value()
            return (current_value - self.initial_capital) / self.initial_capital
        except Exception as e:
            logger.error(f"Error calculating returns: {e}")
            return 0.0

    def update_portfolio(self, symbol: str, quantity: float, price: float, action: str) -> None:
        """Update portfolio with a new trade.

        Args:
            symbol: Trading symbol
            quantity: Trade quantity
            price: Trade price
            action: Trade action (buy/sell)
        """
        self.update_position(symbol, quantity, price, action)

    def calculate_position_value(self, symbol: str, current_price: float) -> float:
        """Calculate value of a position.

        Args:
            symbol: Trading symbol
            current_price: Current price of the asset

        Returns:
            Position value
        """
        try:
            if symbol in self.positions:
                return self.positions[symbol]["size"] * current_price
            return 0.0
        except Exception as e:
            logger.error(f"Error calculating position value: {e}")
            return 0.0

    def calculate_portfolio_value(self, current_prices: dict[str, float]) -> float:
        """Calculate total portfolio value.

        Args:
            current_prices: Dictionary mapping symbols to current prices

        Returns:
            Total portfolio value
        """
        try:
            total_value = self.current_balance
            for symbol, price in current_prices.items():
                total_value += self.calculate_position_value(symbol, price)
            return total_value
        except Exception as e:
            logger.error(f"Error calculating portfolio value: {e}")
            return self.current_balance

    def calculate_total_returns(self, current_prices: dict[str, float]) -> float:
        """Calculate total returns.

        Args:
            current_prices: Dictionary mapping symbols to current prices

        Returns:
            Total returns as a percentage
        """
        try:
            current_value = self.calculate_portfolio_value(current_prices)
            return (current_value - self.initial_capital) / self.initial_capital
        except Exception as e:
            logger.error(f"Error calculating total returns: {e}")
            return 0.0

    def get_trade_history(self) -> list[OrderDict]:
        """Return a copy of recorded trades."""
        return list(self.trades)
