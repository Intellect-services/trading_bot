"""Portfolio management module."""
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd

from src.utils.logger import setup_logger
from src.utils.helpers import calculate_position_size, format_price

logger = setup_logger(__name__)


class Portfolio:
    """Portfolio management class for tracking positions and performance."""

    def __init__(self, initial_capital: float = 100000.0):
        """Initialize portfolio with initial capital.

        Args:
            initial_capital (float): Initial capital amount
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.trades: List[Dict[str, Any]] = []
        self.cash = initial_capital
        self.equity = initial_capital
        self.unrealized_pnl = 0.0
        self.realized_pnl = 0.0
        logger.info("Initialized portfolio with capital: %s", format_price(initial_capital))

    def update_position(
        self,
        symbol: str,
        quantity: float,
        price: float,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Update position for a symbol.

        Args:
            symbol (str): Trading symbol
            quantity (float): Position quantity (negative for short)
            price (float): Current price
            timestamp (Optional[datetime]): Transaction timestamp
        """
        if timestamp is None:
            timestamp = datetime.now()

        if symbol not in self.positions:
            self.positions[symbol] = {
                'quantity': 0,
                'avg_price': 0,
                'cost_basis': 0,
                'market_value': 0,
                'unrealized_pnl': 0
            }

        position = self.positions[symbol]
        old_quantity = position['quantity']
        old_cost = position['cost_basis']

        # Calculate the cost of the new trade
        trade_cost = quantity * price
        self.cash -= trade_cost

        # Update position
        new_quantity = old_quantity + quantity
        if new_quantity == 0:
            # Position closed
            del self.positions[symbol]
            realized_pnl = -old_cost + (old_quantity * price)
            self.realized_pnl += realized_pnl
            logger.info(
                "Closed position in %s - Realized PnL: %s",
                symbol, format_price(realized_pnl)
            )
        else:
            # Update position details
            position['quantity'] = new_quantity
            position['cost_basis'] = old_cost + trade_cost
            position['avg_price'] = abs(position['cost_basis'] / position['quantity'])
            position['market_value'] = position['quantity'] * price
            position['unrealized_pnl'] = (
                position['market_value'] - position['cost_basis']
            )
            logger.info(
                "Updated position in %s - Qty: %.2f, Avg Price: %s",
                symbol, position['quantity'], format_price(position['avg_price'])
            )

        # Record the trade
        trade = {
            'timestamp': timestamp,
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'value': trade_cost,
            'type': 'buy' if quantity > 0 else 'sell'
        }
        self.trades.append(trade)

        # Update portfolio metrics
        self._update_portfolio_metrics()

    def update_prices(self, prices: Dict[str, float]) -> None:
        """Update position market values with new prices.

        Args:
            prices (Dict[str, float]): Dictionary of symbol -> price mappings
        """
        for symbol, price in prices.items():
            if symbol in self.positions:
                position = self.positions[symbol]
                old_value = position['market_value']
                position['market_value'] = position['quantity'] * price
                position['unrealized_pnl'] = (
                    position['market_value'] - position['cost_basis']
                )
                logger.info(
                    "Updated %s price to %s - PnL: %s",
                    symbol,
                    format_price(price),
                    format_price(position['unrealized_pnl'])
                )

        self._update_portfolio_metrics()

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get position details for a symbol.

        Args:
            symbol (str): Trading symbol

        Returns:
            Optional[Dict[str, Any]]: Position details or None if not found
        """
        return self.positions.get(symbol)

    def get_portfolio_value(self) -> float:
        """Get total portfolio value.

        Returns:
            float: Total portfolio value (cash + positions)
        """
        return self.equity

    def get_returns(self) -> pd.Series:
        """Calculate portfolio returns.

        Returns:
            pd.Series: Portfolio returns
        """
        if not self.trades:
            return pd.Series()

        # Create DataFrame of trades
        trades_df = pd.DataFrame(self.trades)
        trades_df.set_index('timestamp', inplace=True)

        # Calculate portfolio value at each trade
        portfolio_values = []
        current_value = self.initial_capital

        for _, trade in trades_df.iterrows():
            current_value -= trade['value']  # Subtract trade cost
            portfolio_values.append(current_value)

        trades_df['portfolio_value'] = portfolio_values

        # Calculate returns
        returns = trades_df['portfolio_value'].pct_change()
        returns.iloc[0] = (
            trades_df['portfolio_value'].iloc[0] - self.initial_capital
        ) / self.initial_capital

        return returns

    def _update_portfolio_metrics(self) -> None:
        """Update portfolio-wide metrics."""
        total_market_value = sum(
            p['market_value'] for p in self.positions.values()
        )
        self.unrealized_pnl = sum(
            p['unrealized_pnl'] for p in self.positions.values()
        )
        self.equity = self.cash + total_market_value
        logger.info(
            "Portfolio metrics - Equity: %s, Cash: %s, Unrealized PnL: %s",
            format_price(self.equity),
            format_price(self.cash),
            format_price(self.unrealized_pnl)
        ) 