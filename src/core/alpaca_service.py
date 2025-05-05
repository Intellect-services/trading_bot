"""Alpaca service for managing trading operations."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, cast
from uuid import UUID

import alpaca_trade_api as tradeapi
import pandas as pd
from alpaca_trade_api.entity import Account, Asset, Bar, Clock, Order, Position
from alpaca_trade_api.rest import REST

from src.core.alpaca_types import (
    Asset,
    Bar,
    BarSet,
    Clock,
    LimitOrderRequest,
    MarketOrderRequest,
    Order,
    OrderSide,
    OrderType,
    Position,
    QueryOrderStatus,
    Sort,
    StopLimitOrderRequest,
    StopOrderRequest,
    TimeFrame,
    TimeInForce,
    TradeAccount,
)
from src.utils.config import Config

logger = logging.getLogger(__name__)


class AlpacaService:
    """Service for interacting with Alpaca API."""

    def __init__(self, config: Config) -> None:
        """Initialize the Alpaca service.

        Args:
            config: Configuration object containing API credentials and settings
        """
        self.api = tradeapi.REST(
            key_id=config.ALPACA_API_KEY,
            secret_key=config.ALPACA_SECRET_KEY,
            base_url="https://paper-api.alpaca.markets"
            if config.ALPACA_PAPER
            else "https://api.alpaca.markets",
        )
        self.logger = logging.getLogger(__name__)
        logger.info("AlpacaService initialized")

    def get_account(self) -> TradeAccount:
        """Get the trading account information."""
        try:
            account = self.api.get_account()
            return {
                "account_number": str(account.account_number)
                if hasattr(account, "account_number")
                else "",
                "buying_power": float(account.buying_power)
                if hasattr(account, "buying_power")
                else 0.0,
                "cash": float(account.cash) if hasattr(account, "cash") else 0.0,
                "equity": float(account.equity) if hasattr(account, "equity") else 0.0,
                "initial_margin": float(account.initial_margin)
                if hasattr(account, "initial_margin")
                else 0.0,
                "maintenance_margin": float(account.maintenance_margin)
                if hasattr(account, "maintenance_margin")
                else 0.0,
                "pattern_day_trader": bool(account.pattern_day_trader)
                if hasattr(account, "pattern_day_trader")
                else False,
                "portfolio_value": float(account.portfolio_value)
                if hasattr(account, "portfolio_value")
                else 0.0,
                "status": str(account.status) if hasattr(account, "status") else "",
                "trade_suspended_by_user": bool(account.trade_suspended_by_user)
                if hasattr(account, "trade_suspended_by_user")
                else False,
                "trading_blocked": bool(account.trading_blocked)
                if hasattr(account, "trading_blocked")
                else False,
                "transfers_blocked": bool(account.transfers_blocked)
                if hasattr(account, "transfers_blocked")
                else False,
            }
        except Exception as e:
            self.logger.error(f"Failed to get account: {str(e)}")
            raise

    def get_positions(self) -> List[Position]:
        """Get all positions."""
        try:
            positions = self.api.list_positions()
            return [
                {
                    "asset_id": UUID(str(position.asset_id))
                    if hasattr(position, "asset_id")
                    else UUID(int=0),
                    "symbol": str(position.symbol) if hasattr(position, "symbol") else "",
                    "exchange": str(position.exchange) if hasattr(position, "exchange") else "",
                    "asset_class": str(position.asset_class)
                    if hasattr(position, "asset_class")
                    else "",
                    "avg_entry_price": float(position.avg_entry_price)
                    if hasattr(position, "avg_entry_price")
                    else 0.0,
                    "qty": float(position.qty) if hasattr(position, "qty") else 0.0,
                    "side": str(position.side) if hasattr(position, "side") else "",
                    "market_value": float(position.market_value)
                    if hasattr(position, "market_value")
                    else 0.0,
                    "cost_basis": float(position.cost_basis)
                    if hasattr(position, "cost_basis")
                    else 0.0,
                    "unrealized_pl": float(position.unrealized_pl)
                    if hasattr(position, "unrealized_pl")
                    else 0.0,
                    "unrealized_plpc": float(position.unrealized_plpc)
                    if hasattr(position, "unrealized_plpc")
                    else 0.0,
                    "current_price": float(position.current_price)
                    if hasattr(position, "current_price")
                    else 0.0,
                    "lastday_price": float(position.lastday_price)
                    if hasattr(position, "lastday_price")
                    else 0.0,
                    "change_today": float(position.change_today)
                    if hasattr(position, "change_today")
                    else 0.0,
                }
                for position in positions
            ]
        except Exception as e:
            self.logger.error(f"Failed to get positions: {str(e)}")
            raise

    def get_position(self, symbol: str) -> Optional[Position]:
        """Get a specific position by symbol."""
        try:
            position = self.api.get_position(symbol)
            return {
                "asset_id": UUID(str(position.asset_id))
                if hasattr(position, "asset_id")
                else UUID(int=0),
                "symbol": str(position.symbol) if hasattr(position, "symbol") else "",
                "exchange": str(position.exchange) if hasattr(position, "exchange") else "",
                "asset_class": str(position.asset_class)
                if hasattr(position, "asset_class")
                else "",
                "avg_entry_price": float(position.avg_entry_price)
                if hasattr(position, "avg_entry_price")
                else 0.0,
                "qty": float(position.qty) if hasattr(position, "qty") else 0.0,
                "side": str(position.side) if hasattr(position, "side") else "",
                "market_value": float(position.market_value)
                if hasattr(position, "market_value")
                else 0.0,
                "cost_basis": float(position.cost_basis)
                if hasattr(position, "cost_basis")
                else 0.0,
                "unrealized_pl": float(position.unrealized_pl)
                if hasattr(position, "unrealized_pl")
                else 0.0,
                "unrealized_plpc": float(position.unrealized_plpc)
                if hasattr(position, "unrealized_plpc")
                else 0.0,
                "current_price": float(position.current_price)
                if hasattr(position, "current_price")
                else 0.0,
                "lastday_price": float(position.lastday_price)
                if hasattr(position, "lastday_price")
                else 0.0,
                "change_today": float(position.change_today)
                if hasattr(position, "change_today")
                else 0.0,
            }
        except Exception as e:
            self.logger.error(f"Failed to get position for {symbol}: {str(e)}")
            return None

    def get_asset(self, symbol: str) -> Optional[Asset]:
        """Get asset information."""
        try:
            asset = self.api.get_asset(symbol)
            return {
                "id": UUID(str(asset.id)) if hasattr(asset, "id") else UUID(int=0),
                "class_": str(asset.class_) if hasattr(asset, "class_") else "",
                "exchange": str(asset.exchange) if hasattr(asset, "exchange") else "",
                "symbol": str(asset.symbol) if hasattr(asset, "symbol") else "",
                "name": str(asset.name) if hasattr(asset, "name") else "",
                "status": str(asset.status) if hasattr(asset, "status") else "",
                "tradable": bool(asset.tradable) if hasattr(asset, "tradable") else False,
                "marginable": bool(asset.marginable) if hasattr(asset, "marginable") else False,
                "shortable": bool(asset.shortable) if hasattr(asset, "shortable") else False,
                "easy_to_borrow": bool(asset.easy_to_borrow)
                if hasattr(asset, "easy_to_borrow")
                else False,
                "fractionable": bool(asset.fractionable)
                if hasattr(asset, "fractionable")
                else False,
                "maintenance_margin_requirement": float(asset.maintenance_margin_requirement)
                if hasattr(asset, "maintenance_margin_requirement")
                else 0.0,
                "min_order_size": float(asset.min_order_size)
                if hasattr(asset, "min_order_size")
                else 0.0,
                "min_trade_increment": float(asset.min_trade_increment)
                if hasattr(asset, "min_trade_increment")
                else 0.0,
                "price_increment": float(asset.price_increment)
                if hasattr(asset, "price_increment")
                else 0.0,
            }
        except Exception as e:
            self.logger.error(f"Failed to get asset {symbol}: {str(e)}")
            return None

    def get_clock(self) -> Clock:
        """Get market clock information."""
        try:
            clock = self.api.get_clock()
            return {
                "timestamp": clock.timestamp if hasattr(clock, "timestamp") else datetime.now(),
                "is_open": bool(clock.is_open) if hasattr(clock, "is_open") else False,
                "next_open": clock.next_open if hasattr(clock, "next_open") else datetime.now(),
                "next_close": clock.next_close if hasattr(clock, "next_close") else datetime.now(),
            }
        except Exception as e:
            self.logger.error(f"Failed to get clock: {str(e)}")
            raise

    def submit_order(
        self,
        order_data: Union[
            MarketOrderRequest, LimitOrderRequest, StopOrderRequest, StopLimitOrderRequest
        ],
    ) -> Order:
        """Submit an order."""
        try:
            order = self.api.submit_order(
                symbol=order_data["symbol"],
                qty=str(order_data["qty"]),
                side=order_data["side"].value,
                type=order_data["type"],
                time_in_force=order_data["time_in_force"].value,
                limit_price=str(order_data["limit_price"]) if "limit_price" in order_data else None,
                stop_price=str(order_data["stop_price"]) if "stop_price" in order_data else None,
            )
            return self._convert_order(order)
        except Exception as e:
            self.logger.error(f"Failed to submit order: {str(e)}")
            raise

    def get_orders(
        self,
        status: Optional[QueryOrderStatus] = None,
        limit: Optional[int] = None,
        after: Optional[datetime] = None,
        until: Optional[datetime] = None,
        direction: Optional[Sort] = None,
    ) -> List[Order]:
        """Get orders with optional filters."""
        try:
            orders = self.api.list_orders(
                status=status.value if status else None,
                limit=limit,
                after=after,
                until=until,
                direction=direction.value if direction else None,
            )
            return [self._convert_order(order) for order in orders]
        except Exception as e:
            self.logger.error(f"Failed to get orders: {str(e)}")
            raise

    def get_order(self, order_id: str) -> Optional[Order]:
        """Get a specific order by ID."""
        try:
            order = self.api.get_order(order_id)
            return self._convert_order(order)
        except Exception as e:
            self.logger.error(f"Failed to get order {order_id}: {str(e)}")
            return None

    def cancel_order(self, order_id: str) -> None:
        """Cancel an order."""
        try:
            self.api.cancel_order(order_id)
        except Exception as e:
            self.logger.error(f"Failed to cancel order {order_id}: {str(e)}")
            raise

    def get_bars(
        self,
        symbols: List[str],
        timeframe: TimeFrame,
        start: datetime,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> Optional[BarSet]:
        """Get historical bars."""
        try:
            bars = self.api.get_bars(
                symbols,
                f"{timeframe.amount}{timeframe.unit[0]}",  # Convert to Alpaca timeframe format (e.g., "1m", "1h", "1d")
                start=start,
                end=end,
                limit=limit,
            )
            return {
                "bars": [
                    {
                        "timestamp": bar.timestamp if hasattr(bar, "timestamp") else datetime.now(),
                        "open": float(bar.open) if hasattr(bar, "open") else 0.0,
                        "high": float(bar.high) if hasattr(bar, "high") else 0.0,
                        "low": float(bar.low) if hasattr(bar, "low") else 0.0,
                        "close": float(bar.close) if hasattr(bar, "close") else 0.0,
                        "volume": int(bar.volume) if hasattr(bar, "volume") else 0,
                        "trade_count": int(bar.trade_count) if hasattr(bar, "trade_count") else 0,
                        "vwap": float(bar.vwap) if hasattr(bar, "vwap") else 0.0,
                    }
                    for bar in bars
                ],
                "next_page_token": None,  # Alpaca v2 API doesn't use page tokens
                "symbol": symbols[0] if len(symbols) == 1 else None,
            }
        except Exception as e:
            self.logger.error(f"Failed to get bars: {str(e)}")
            return None

    def _convert_order(self, order: Order) -> Order:
        """Convert Alpaca order to our order type."""
        return {
            "id": UUID(str(order.id)) if hasattr(order, "id") else UUID(int=0),
            "client_order_id": str(order.client_order_id)
            if hasattr(order, "client_order_id")
            else "",
            "created_at": order.created_at if hasattr(order, "created_at") else datetime.now(),
            "updated_at": order.updated_at if hasattr(order, "updated_at") else None,
            "submitted_at": order.submitted_at if hasattr(order, "submitted_at") else None,
            "filled_at": order.filled_at if hasattr(order, "filled_at") else None,
            "expired_at": order.expired_at if hasattr(order, "expired_at") else None,
            "canceled_at": order.canceled_at if hasattr(order, "canceled_at") else None,
            "failed_at": order.failed_at if hasattr(order, "failed_at") else None,
            "replaced_at": order.replaced_at if hasattr(order, "replaced_at") else None,
            "replaced_by": UUID(str(order.replaced_by))
            if hasattr(order, "replaced_by") and order.replaced_by
            else None,
            "replaces": UUID(str(order.replaces))
            if hasattr(order, "replaces") and order.replaces
            else None,
            "asset_id": UUID(str(order.asset_id))
            if hasattr(order, "asset_id") and order.asset_id
            else None,
            "symbol": str(order.symbol) if hasattr(order, "symbol") else "",
            "asset_class": str(order.asset_class) if hasattr(order, "asset_class") else "",
            "qty": float(order.qty) if hasattr(order, "qty") else 0.0,
            "filled_qty": float(order.filled_qty) if hasattr(order, "filled_qty") else 0.0,
            "type": OrderType(str(order.type).lower())
            if hasattr(order, "type")
            else OrderType.MARKET,
            "side": OrderSide(str(order.side).lower()) if hasattr(order, "side") else OrderSide.BUY,
            "time_in_force": TimeInForce(str(order.time_in_force).lower())
            if hasattr(order, "time_in_force")
            else TimeInForce.DAY,
            "limit_price": float(order.limit_price)
            if hasattr(order, "limit_price") and order.limit_price
            else None,
            "stop_price": float(order.stop_price)
            if hasattr(order, "stop_price") and order.stop_price
            else None,
            "filled_avg_price": float(order.filled_avg_price)
            if hasattr(order, "filled_avg_price") and order.filled_avg_price
            else None,
            "status": str(order.status) if hasattr(order, "status") else "",
            "extended_hours": bool(order.extended_hours)
            if hasattr(order, "extended_hours")
            else False,
            "legs": order.legs if hasattr(order, "legs") else None,
        }
