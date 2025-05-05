"""Alpaca service for managing trading operations."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, cast
from uuid import UUID

import alpaca_trade_api as tradeapi
import pandas as pd
from alpaca_trade_api.entity import Account, Asset, Bar, Clock, Order, Position
from alpaca_trade_api.rest import REST

from src.core.alpaca_types import Asset as AlpacaAsset
from src.core.alpaca_types import Bar as AlpacaBar
from src.core.alpaca_types import BarSet
from src.core.alpaca_types import Clock as AlpacaClock
from src.core.alpaca_types import LimitOrderRequest, MarketOrderRequest
from src.core.alpaca_types import Order as AlpacaOrder
from src.core.alpaca_types import OrderSide, OrderType
from src.core.alpaca_types import Position as AlpacaPosition
from src.core.alpaca_types import (
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
        self.config = config
        self.client = tradeapi.REST(
            key_id=config.ALPACA_API_KEY,
            secret_key=config.ALPACA_API_SECRET,
            base_url="https://paper-api.alpaca.markets"
            if config.TRADING_MODE == "paper"
            else "https://api.alpaca.markets",
        )
        self.logger = logging.getLogger(__name__)
        logger.info("AlpacaService initialized")

    def get_account(self) -> TradeAccount:
        """Get the trading account information."""
        try:
            account = self.client.get_account()
            return cast(
                TradeAccount,
                {
                    "account_number": str(account.account_number),
                    "cash": str(account.cash),
                    "portfolio_value": str(account.portfolio_value),
                    "pattern_day_trader": bool(account.pattern_day_trader),
                    "trading_blocked": bool(account.trading_blocked),
                    "transfers_blocked": bool(account.transfers_blocked),
                    "account_blocked": bool(account.account_blocked),
                    "created_at": account.created_at,
                    "trade_suspended_by_user": bool(account.trade_suspended_by_user),
                    "multiplier": str(account.multiplier),
                    "shorting_enabled": bool(account.shorting_enabled),
                    "equity": str(account.equity),
                    "last_equity": str(account.last_equity),
                    "initial_margin": str(account.initial_margin),
                    "maintenance_margin": str(account.maintenance_margin),
                    "last_maintenance_margin": str(account.last_maintenance_margin),
                    "long_market_value": str(account.long_market_value),
                    "short_market_value": str(account.short_market_value),
                    "buying_power": str(account.buying_power),
                    "regt_buying_power": str(account.regt_buying_power),
                    "daytrading_buying_power": str(account.daytrading_buying_power),
                    "effective_buying_power": str(account.effective_buying_power),
                    "crypto_status": str(account.crypto_status),
                    "currency": str(account.currency),
                    "accrued_fees": str(account.accrued_fees),
                },
            )
        except Exception as e:
            self.logger.error(f"Failed to get account: {e}")
            raise

    def get_positions(self) -> List[AlpacaPosition]:
        """Get all positions."""
        try:
            positions = self.client.list_positions()
            return [
                {
                    "asset_id": UUID(str(pos.asset_id)),
                    "symbol": str(pos.symbol),
                    "exchange": str(pos.exchange),
                    "asset_class": str(pos.asset_class),
                    "asset_marginable": bool(pos.asset_marginable),
                    "qty": str(pos.qty),
                    "avg_entry_price": str(pos.avg_entry_price),
                    "side": str(pos.side),
                    "market_value": str(pos.market_value),
                    "cost_basis": str(pos.cost_basis),
                    "unrealized_pl": str(pos.unrealized_pl),
                    "unrealized_plpc": str(pos.unrealized_plpc),
                    "unrealized_intraday_pl": str(pos.unrealized_intraday_pl),
                    "unrealized_intraday_plpc": str(pos.unrealized_intraday_plpc),
                    "current_price": str(pos.current_price),
                    "lastday_price": str(pos.lastday_price),
                    "change_today": str(pos.change_today),
                }
                for pos in positions
            ]
        except Exception as e:
            self.logger.error(f"Failed to get positions: {e}")
            return []

    def get_position(self, symbol: str) -> Optional[AlpacaPosition]:
        """Get a specific position by symbol."""
        try:
            position = self.client.get_position(symbol)
            return {
                "asset_id": UUID(str(position.asset_id)),
                "symbol": str(position.symbol),
                "exchange": str(position.exchange),
                "asset_class": str(position.asset_class),
                "asset_marginable": bool(position.asset_marginable),
                "qty": str(position.qty),
                "avg_entry_price": str(position.avg_entry_price),
                "side": str(position.side),
                "market_value": str(position.market_value),
                "cost_basis": str(position.cost_basis),
                "unrealized_pl": str(position.unrealized_pl),
                "unrealized_plpc": str(position.unrealized_plpc),
                "unrealized_intraday_pl": str(position.unrealized_intraday_pl),
                "unrealized_intraday_plpc": str(position.unrealized_intraday_plpc),
                "current_price": str(position.current_price),
                "lastday_price": str(position.lastday_price),
                "change_today": str(position.change_today),
            }
        except Exception as e:
            self.logger.error(f"Failed to get position for {symbol}: {e}")
            return None

    def get_asset(self, symbol: str) -> Optional[AlpacaAsset]:
        """Get asset information."""
        try:
            asset = self.client.get_asset(symbol)
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
            }
        except Exception as e:
            self.logger.error(f"Failed to get asset {symbol}: {e}")
            return None

    def get_clock(self) -> AlpacaClock:
        """Get market clock information."""
        try:
            clock = self.client.get_clock()
            return {
                "timestamp": clock.timestamp if hasattr(clock, "timestamp") else datetime.now(),
                "is_open": bool(clock.is_open) if hasattr(clock, "is_open") else False,
                "next_open": clock.next_open if hasattr(clock, "next_open") else datetime.now(),
                "next_close": clock.next_close if hasattr(clock, "next_close") else datetime.now(),
            }
        except Exception as e:
            self.logger.error(f"Failed to get clock: {e}")
            raise

    def submit_order(self, order_data: Dict[str, Any]) -> AlpacaOrder:
        """Submit a new order."""
        try:
            order_params = {
                "symbol": order_data["symbol"],
                "qty": order_data["qty"],
                "side": order_data["side"],
                "type": order_data["type"],
                "time_in_force": order_data["time_in_force"],
            }

            if "limit_price" in order_data:
                order_params["limit_price"] = order_data["limit_price"]
            if "stop_price" in order_data:
                order_params["stop_price"] = order_data["stop_price"]

            order = self.client.submit_order(**order_params)
            return self._convert_order(order)
        except Exception as e:
            self.logger.error(f"Failed to submit order: {e}")
            raise

    def get_orders(
        self,
        status: Optional[QueryOrderStatus] = None,
        limit: Optional[int] = None,
        after: Optional[datetime] = None,
        until: Optional[datetime] = None,
        direction: Optional[Sort] = None,
        nested: bool = False,
    ) -> List[AlpacaOrder]:
        """Get orders with optional filters."""
        try:
            orders = self.client.list_orders(
                status=status.value if status else None,
                limit=limit,
                after=after,
                until=until,
                direction=direction.value if direction else None,
                nested=nested,
            )
            return [self._convert_order(order) for order in orders]
        except Exception as e:
            self.logger.error(f"Failed to get orders: {e}")
            return []

    def get_order(self, order_id: str) -> Optional[AlpacaOrder]:
        """Get a specific order by ID."""
        try:
            order = self.client.get_order(order_id)
            return self._convert_order(order)
        except Exception as e:
            self.logger.error(f"Failed to get order {order_id}: {e}")
            return None

    def cancel_order(self, order_id: str) -> None:
        """Cancel an order."""
        try:
            self.client.cancel_order(order_id)
        except Exception as e:
            self.logger.error(f"Failed to cancel order {order_id}: {e}")
            raise

    def get_bars(
        self,
        symbols: List[str],
        timeframe: TimeFrame,
        start: datetime,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> BarSet:
        """Get historical bars."""
        try:
            bars = self.client.get_bars(
                symbols,
                f"{timeframe.amount}{timeframe.unit[0]}",
                start=start,
                end=end,
                limit=limit,
            )
            return cast(
                BarSet,
                {
                    "bars": [
                        {
                            "timestamp": bar.t,
                            "open": float(bar.o),
                            "high": float(bar.h),
                            "low": float(bar.l),
                            "close": float(bar.c),
                            "volume": int(bar.v),
                        }
                        for bar in bars
                    ]
                },
            )
        except Exception as e:
            self.logger.error(f"Failed to get bars: {e}")
            raise

    def _convert_order(self, order: Order) -> AlpacaOrder:
        """Convert Alpaca order to our order type."""
        return {
            "id": UUID(str(order.id)),
            "client_order_id": str(order.client_order_id),
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "submitted_at": order.submitted_at,
            "filled_at": order.filled_at,
            "expired_at": order.expired_at,
            "canceled_at": order.canceled_at,
            "failed_at": order.failed_at,
            "replaced_at": order.replaced_at,
            "replaced_by": UUID(str(order.replaced_by)) if order.replaced_by else None,
            "replaces": UUID(str(order.replaces)) if order.replaces else None,
            "asset_id": UUID(str(order.asset_id)) if order.asset_id else None,
            "symbol": str(order.symbol),
            "asset_class": str(order.asset_class),
            "qty": float(order.qty),
            "filled_qty": float(order.filled_qty),
            "type": OrderType(order.type),
            "side": OrderSide(order.side),
            "time_in_force": TimeInForce(order.time_in_force),
            "limit_price": float(order.limit_price) if order.limit_price else None,
            "stop_price": float(order.stop_price) if order.stop_price else None,
            "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else None,
            "status": str(order.status),
            "extended_hours": bool(order.extended_hours),
            "legs": None,  # We don't handle legs in this implementation
        }
