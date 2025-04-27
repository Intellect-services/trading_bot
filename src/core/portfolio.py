"""Portfolio management module."""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import logging
from datetime import datetime

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class Portfolio:
    """Portfolio management class."""

    def __init__(
        self,
        initial_capital: float = 100000.0,
        max_position_size: float = 0.1,
        commission: float = 0.001
    ) -> None:
        """Initialize portfolio.

        Args:
            initial_capital: Initial capital amount
            max_position_size: Maximum position size as fraction of portfolio
            commission: Trading commission rate
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_position_size = max_position_size
        self.commission = commission
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.trades: List[Dict[str, Any]] = []
        self.peak_value = initial_capital
        self.logger = logging.getLogger(__name__)

    def get_value(self) -> float:
        """Get current portfolio value.

        Returns:
            Current portfolio value
        """
        return self.current_capital

    def get_balance(self) -> float:
        """Get current cash balance.

        Returns:
            Current cash balance
        """
        return self.current_capital

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get position for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Position information or None if not found
        """
        return self.positions.get(symbol)

    def get_all_positions(self) -> Dict[str, Dict[str, Any]]:
        """Get all positions.

        Returns:
            Dictionary of all positions
        """
        return self.positions

    def calculate_position_size(
        self,
        symbol: str,
        price: float,
        risk_per_trade: float = 0.01
    ) -> float:
        """Calculate position size based on risk.

        Args:
            symbol: Trading symbol
            price: Current price
            risk_per_trade: Risk per trade as fraction of portfolio

        Returns:
            Calculated position size
        """
        try:
            max_risk_amount = self.current_capital * risk_per_trade
            position_size = max_risk_amount / price
            max_position = self.current_capital * self.max_position_size / price
            return min(position_size, max_position)
        except Exception as e:
            self.logger.error(f"Error calculating position size: {str(e)}")
            return 0.0

    def execute_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        price: float
    ) -> bool:
        """Execute a trading order.

        Args:
            symbol: Trading symbol
            qty: Order quantity
            side: Order side (buy/sell)
            price: Execution price

        Returns:
            True if order executed successfully, False otherwise
        """
        try:
            cost = qty * price * (1 + self.commission)
            if side == 'buy':
                if cost > self.current_capital:
                    self.logger.warning(f"Insufficient capital for {symbol} buy order")
                    return False
                self.current_capital -= cost
                self.positions[symbol] = {
                    'quantity': qty,
                    'entry_price': price,
                    'timestamp': datetime.now()
                }
            else:  # sell
                if symbol not in self.positions:
                    self.logger.warning(f"No position found for {symbol} sell order")
                    return False
                self.current_capital += qty * price * (1 - self.commission)
                del self.positions[symbol]

            self.trades.append({
                'symbol': symbol,
                'quantity': qty,
                'price': price,
                'side': side,
                'timestamp': datetime.now()
            })
            return True
        except Exception as e:
            self.logger.error(f"Error executing order: {str(e)}")
            return False

    def update_prices(self, prices: Dict[str, float]) -> None:
        """Update position prices.

        Args:
            prices: Dictionary of symbol prices
        """
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol]['current_price'] = price

    def get_summary(self) -> Dict[str, Any]:
        """Get portfolio summary.

        Returns:
            Dictionary containing portfolio summary
        """
        return {
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'positions': self.positions,
            'trades': self.trades
        }

    def update_position(
        self,
        symbol: str,
        quantity: float,
        price: float,
        action: str
    ) -> None:
        """Update position information.

        Args:
            symbol: Trading symbol
            quantity: Position quantity
            price: Execution price
            action: Trade action (buy/sell)
        """
        if action == 'buy':
            self.positions[symbol] = {
                'quantity': quantity,
                'entry_price': price,
                'timestamp': datetime.now()
            }
        elif action == 'sell' and symbol in self.positions:
            del self.positions[symbol]

    def update_portfolio(
        self,
        symbol: str,
        quantity: float,
        price: float,
        action: str
    ) -> None:
        """Update portfolio with a trade.

        Args:
            symbol: Trading symbol
            quantity: Trade quantity
            price: Execution price
            action: Trade action (buy/sell)
        """
        cost = quantity * price * (1 + self.commission)
        if action == 'buy':
            if cost > self.current_capital:
                self.logger.warning(f"Insufficient capital for {symbol} buy order")
                return
            self.current_capital -= cost
        else:  # sell
            self.current_capital += quantity * price * (1 - self.commission)

        self.update_position(symbol, quantity, price, action)
        self.trades.append({
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'action': action,
            'timestamp': datetime.now()
        })

    def calculate_position_value(self, symbol: str, current_price: float) -> float:
        """Calculate current value of a position.

        Args:
            symbol: Trading symbol
            current_price: Current price

        Returns:
            Current position value
        """
        position = self.get_position(symbol)
        if position:
            return position['quantity'] * current_price
        return 0.0

    def calculate_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value.

        Args:
            current_prices: Dictionary of current prices

        Returns:
            Total portfolio value
        """
        position_values = sum(
            self.calculate_position_value(symbol, price)
            for symbol, price in current_prices.items()
        )
        return self.current_capital + position_values

    def calculate_returns(self, current_prices: Dict[str, float]) -> float:
        """Calculate portfolio returns.

        Args:
            current_prices: Dictionary of current prices

        Returns:
            Portfolio returns
        """
        current_value = self.calculate_portfolio_value(current_prices)
        return (current_value - self.initial_capital) / self.initial_capital

    def calculate_total_returns(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio returns.

        Args:
            current_prices: Dictionary of current prices

        Returns:
            Total portfolio returns
        """
        return self.calculate_returns(current_prices)
