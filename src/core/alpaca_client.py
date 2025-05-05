"""Alpaca API client implementation."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, cast

import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import REST
from alpaca_trade_api.stream import Stream

from src.core.alpaca_types import (
    Asset,
    BarSet,
    Clock,
    Order,
    OrderSide,
    OrderType,
    Position,
    Sort,
    TimeInForce,
    TradeAccount,
)
from src.utils.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlpacaClient:
    """Client for interacting with the Alpaca API."""

    def __init__(self, config: Config) -> None:
        """Initialize the Alpaca client."""
        self.api = tradeapi.REST(
            key_id=config.alpaca_api_key,
            secret_key=config.alpaca_secret_key,
            base_url="https://paper-api.alpaca.markets"
            if config.alpaca_paper
            else "https://api.alpaca.markets",
        )
        logger.info("Initialized Alpaca client")

    def get_account(self) -> TradeAccount:
        """Get account information."""
        try:
            account = self.api.get_account()
            return cast(TradeAccount, account)
        except Exception as e:
            logger.error(f"Failed to get account: {e}")
            raise

    def get_all_positions(self) -> List[Position]:
        """Get all open positions."""
        try:
            positions = self.api.list_positions()
            return [cast(Position, pos) for pos in positions]
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise

    def get_open_position(self, symbol: str) -> Optional[Position]:
        """Get open position for a symbol."""
        try:
            position = self.api.get_position(symbol)
            return cast(Position, position) if position else None
        except Exception as e:
            logger.error(f"Failed to get position for {symbol}: {e}")
            raise

    def get_asset(self, symbol: str) -> Asset:
        """Get asset information."""
        try:
            asset = self.api.get_asset(symbol)
            return cast(Asset, asset)
        except Exception as e:
            logger.error(f"Failed to get asset for {symbol}: {e}")
            raise

    def get_clock(self) -> Clock:
        """Get market clock."""
        try:
            clock = self.api.get_clock()
            return cast(Clock, clock)
        except Exception as e:
            logger.error(f"Failed to get clock: {e}")
            raise

    def submit_order(
        self,
        symbol: str,
        qty: str,
        side: OrderSide,
        type: OrderType,
        time_in_force: TimeInForce,
        limit_price: Optional[str] = None,
        stop_price: Optional[str] = None,
    ) -> Order:
        """Submit an order."""
        try:
            order_data = {
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "type": type,
                "time_in_force": time_in_force,
            }

            if limit_price:
                order_data["limit_price"] = limit_price
            if stop_price:
                order_data["stop_price"] = stop_price

            order = self.api.submit_order(**order_data)
            return cast(Order, order)
        except Exception as e:
            logger.error(f"Failed to submit order: {e}")
            raise

    def get_orders(
        self,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        after: Optional[datetime] = None,
        until: Optional[datetime] = None,
        direction: Optional[Sort] = None,
        nested: bool = False,
    ) -> List[Order]:
        """Get orders."""
        try:
            orders = self.api.list_orders(
                status=status,
                limit=limit,
                after=after,
                until=until,
                direction=direction,
                nested=nested,
            )
            return [cast(Order, order) for order in orders]
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            raise

    def get_order_by_id(self, order_id: str) -> Order:
        """Get order by ID."""
        try:
            order = self.api.get_order(order_id)
            return cast(Order, order)
        except Exception as e:
            logger.error(f"Failed to get order {order_id}: {e}")
            raise

    def cancel_order(self, order_id: str) -> None:
        """Cancel an order."""
        try:
            self.api.cancel_order(order_id)
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise

    def get_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> BarSet:
        """Get historical bars."""
        try:
            bars = self.api.get_bars(symbol, timeframe, start=start, end=end, limit=limit)
            return cast(BarSet, bars)
        except Exception as e:
            logger.error(f"Failed to get bars for {symbol}: {e}")
            raise
