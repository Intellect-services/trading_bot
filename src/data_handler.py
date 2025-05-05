"""Data handler for managing market data."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from src.core.alpaca_service import AlpacaService
from src.core.alpaca_types import OrderSide, OrderType, TimeFrame, TimeInForce
from src.utils.config import Config

logger = logging.getLogger(__name__)


class DataHandler:
    """Handler for managing market data."""

    def __init__(self, config: Config, alpaca_service: AlpacaService):
        """Initialize the data handler."""
        self.config = config
        self.alpaca_service = alpaca_service
        self.logger = logging.getLogger(__name__)

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get position for a symbol."""
        try:
            return self.alpaca_service.get_position(symbol)
        except Exception as e:
            self.logger.error(f"Error getting position for {symbol}: {e}")
            return None

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all positions."""
        try:
            return self.alpaca_service.get_positions()
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []

    def get_bars(
        self,
        symbols: List[str],
        timeframe: str,
        start: datetime,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> Optional[pd.DataFrame]:
        """Get historical bars."""
        try:
            bars = self.alpaca_service.get_bars(
                symbols=symbols,
                timeframe=TimeFrame(amount=int(timeframe[:-1]), unit=timeframe[-1]),
                start=start,
                end=end,
                limit=limit,
            )
            if bars and bars["bars"]:
                df = pd.DataFrame(bars["bars"])
                df.set_index("timestamp", inplace=True)
                return df
            return None
        except Exception as e:
            self.logger.error(f"Error getting bars: {e}")
            return None

    def submit_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        type: str,
        time_in_force: str,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """Submit an order."""
        try:
            order_data = {
                "symbol": symbol,
                "qty": str(qty),
                "side": OrderSide(side.lower()),
                "type": OrderType(type.lower()),
                "time_in_force": TimeInForce(time_in_force.lower()),
            }

            if limit_price:
                order_data["limit_price"] = str(limit_price)
            if stop_price:
                order_data["stop_price"] = str(stop_price)

            return self.alpaca_service.submit_order(order_data)
        except Exception as e:
            self.logger.error(f"Error submitting order: {e}")
            return None

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        try:
            self.alpaca_service.cancel_order(order_id)
            return True
        except Exception as e:
            self.logger.error(f"Error canceling order {order_id}: {e}")
            return False

    def get_orders(
        self,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        after: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get orders with optional filters."""
        try:
            return self.alpaca_service.get_orders(
                status=status,
                limit=limit,
                after=after,
                until=until,
            )
        except Exception as e:
            self.logger.error(f"Error getting orders: {e}")
            return []

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific order by ID."""
        try:
            return self.alpaca_service.get_order(order_id)
        except Exception as e:
            self.logger.error(f"Error getting order {order_id}: {e}")
            return None
