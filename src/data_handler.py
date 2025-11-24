"""Data handler for managing market data."""

import logging
from datetime import datetime
from typing import Any

from src.core.alpaca_service import AlpacaService
from src.core.alpaca_types import Bar, BarSet, OrderSide, OrderType, TimeInForce
from src.utils.config import Config

logger = logging.getLogger(__name__)


class DataHandler:
    """Handler for managing market data."""

    def __init__(self, config: Config, alpaca_service: AlpacaService):
        """Initialize the data handler."""
        self.config = config
        self.alpaca_service = alpaca_service
        self.logger = logging.getLogger(__name__)

    def get_position(self, symbol: str) -> dict[str, Any] | None:
        """Get position for a symbol."""
        try:
            positions = self.alpaca_service.get_positions()
            for pos in positions:
                if pos.get("symbol") == symbol:
                    return pos
            return None
        except Exception as e:
            self.logger.error(f"Error getting position for {symbol}: {e}")
            return None

    def get_positions(self) -> list[dict[str, Any]]:
        """Get all positions."""
        try:
            return self.alpaca_service.get_positions()
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []

    def get_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime | None = None,
        limit: int | None = None,
    ) -> BarSet | None:
        """Get historical bars for a symbol."""
        try:
            bars_dict = self.alpaca_service.get_bars(
                symbol=symbol,
                timeframe=timeframe,
                start=start,
                end=end,
                limit=limit,
            )
            if not bars_dict:
                return None
            symbol_bars = bars_dict.get(symbol, [])
            if not symbol_bars:
                return None
            bar_objects = [
                Bar(
                    timestamp=datetime.fromisoformat(str(bar["timestamp"])),
                    open=float(bar["open"]),
                    high=float(bar["high"]),
                    low=float(bar["low"]),
                    close=float(bar["close"]),
                    volume=int(float(bar["volume"])),
                )
                for bar in symbol_bars
            ]
            return BarSet(bars=bar_objects)
        except Exception as e:
            logger.error(f"Error getting bars for {symbol}: {e}")
            return None

    def submit_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        type: str,
        time_in_force: str,
        limit_price: float | None = None,
        stop_price: float | None = None,
    ) -> dict[str, Any] | None:
        """Submit an order."""
        try:
            order_kwargs: dict[str, Any] = {
                "symbol": symbol,
                "qty": int(qty),
                "side": OrderSide(side.lower()),
                "type": OrderType(type.lower()),
                "time_in_force": TimeInForce(time_in_force.lower()),
            }

            if limit_price is not None:
                order_kwargs["limit_price"] = float(limit_price)
            if stop_price is not None:
                order_kwargs["stop_price"] = float(stop_price)

            return self.alpaca_service.submit_order(**order_kwargs)
        except Exception as e:
            self.logger.error(f"Error submitting order: {e}")
            return None

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        try:
            return self.alpaca_service.cancel_order(order_id)
        except Exception as e:
            self.logger.error(f"Error canceling order {order_id}: {e}")
            return False

    def get_orders(
        self,
        status: str | None = None,
        limit: int | None = None,
        after: datetime | None = None,
        until: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Get orders with optional filters."""
        try:
            # Convert datetime to string format expected by AlpacaService
            after_str = after.isoformat() if after else None
            until_str = until.isoformat() if until else None
            return self.alpaca_service.get_orders(
                status=status,
                limit=limit,
                after=after_str,
                until=until_str,
            )
        except Exception as e:
            self.logger.error(f"Error getting orders: {e}")
            return []

    def get_order(self, order_id: str) -> dict[str, Any] | None:
        """Get a specific order by ID."""
        try:
            # AlpacaService doesn't have get_order, get all orders and filter
            orders = self.alpaca_service.get_orders(limit=1000)
            for order in orders:
                if order.get("id") == order_id or str(order.get("id")) == order_id:
                    return order
            return None
        except Exception as e:
            self.logger.error(f"Error getting order {order_id}: {e}")
            return None
