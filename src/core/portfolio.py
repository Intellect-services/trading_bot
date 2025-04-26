"""Portfolio management module."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from src.utils.config import Config
from src.utils.logger import setup_logger
import pandas as pd

logger = setup_logger(__name__)


class Portfolio:
    """Portfolio management for tracking positions and performance."""

    def __init__(self, initial_capital: float):
        """Initialize portfolio with initial capital.

        Args:
            initial_capital: Initial capital amount
        """
        self.initial_capital = initial_capital
        self.current_balance = initial_capital
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.trades: List[Dict[str, Any]] = []
        self.peak_value = initial_capital
        logger.info("Portfolio initialized with capital: %.2f", initial_capital)

    def get_value(self) -> float:
        """Get current portfolio value.

        Returns:
            Current portfolio value
        """
        try:
            total_value = self.current_balance
            for symbol, position in self.positions.items():
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

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get position for a symbol.

        Args:
            symbol: Symbol to get position for

        Returns:
            Position dictionary or None if no position exists
        """
        return self.positions.get(symbol)

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

    def execute_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        price: float
    ) -> Dict[str, Any]:
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
            order = {
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "price": price,
                "timestamp": datetime.now()
            }
            
            if side.lower() == "buy":
                cost = qty * price
                if cost > self.current_balance:
                    logger.warning("Insufficient funds for buy order")
                    return {}
                
                self.current_balance -= cost
                if symbol in self.positions:
                    position = self.positions[symbol]
                    new_size = position["size"] + qty
                    new_cost = position["cost"] + cost
                    position["size"] = new_size
                    position["cost"] = new_cost
                    position["avg_price"] = new_cost / new_size
                    position["current_price"] = price
                else:
                    self.positions[symbol] = {
                        "size": qty,
                        "cost": cost,
                        "avg_price": price,
                        "current_price": price
                    }
            
            elif side.lower() == "sell":
                if symbol not in self.positions:
                    logger.warning("No position to sell")
                    return {}
                
                position = self.positions[symbol]
                if position["size"] < qty:
                    logger.warning("Insufficient shares for sell order")
                    return {}
                
                proceeds = qty * price
                self.current_balance += proceeds
                
                new_size = position["size"] - qty
                if new_size == 0:
                    del self.positions[symbol]
                else:
                    position["size"] = new_size
                    position["cost"] = position["cost"] * (new_size / position["size"])
                    position["avg_price"] = position["cost"] / new_size
                    position["current_price"] = price
            
            self.trades.append(order)
            self.peak_value = max(self.peak_value, self.get_value())
            logger.info(f"Executed {side} order: {order}")
            return order
        except Exception as e:
            logger.error(f"Error executing order: {e}")
            return {}

    def update_prices(self, prices: Dict[str, float]) -> None:
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

    def get_summary(self) -> Dict[str, Any]:
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
                "trades": len(self.trades)
            }
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {}
