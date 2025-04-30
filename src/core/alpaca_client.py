"""Alpaca API client for trading operations."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TypedDict, TypeVar, Union, cast

import alpaca_trade_api as tradeapi
import pandas as pd
from alpaca.data import StockHistoricalDataClient
from alpaca.data.models import BarSet
from alpaca.data.requests import GetAssetsRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.trading import TradingClient
from alpaca.trading.enums import (
    AssetClass,
    OrderSide,
    OrderType,
    QueryOrderStatus,
    TimeInForce,
)
from alpaca.trading.models import Asset, Clock, Order, Position
from alpaca.trading.models import TradeAccount as AlpacaTradeAccount
from alpaca.trading.requests import (
    GetOrdersRequest,
    LimitOrderRequest,
    MarketOrderRequest,
    OrderRequest,
    StopOrderRequest,
)
from alpaca_trade_api.rest import APIError

from src.core.alpaca_types import Bar
from src.types import Order, TradeAccount
from src.utils.config import get_config
from src.utils.logger import setup_logger

logger = logging.getLogger(__name__)

T = TypeVar("T")


class AccountInfo(TypedDict):
    """Type definition for account information."""

    id: str
    cash: float
    portfolio_value: float
    buying_power: float
    equity: float
    long_market_value: float
    short_market_value: float
    initial_margin: float
    maintenance_margin: float
    last_equity: float
    multiplier: float
    status: str
    trading_blocked: bool
    transfers_blocked: bool
    account_blocked: bool
    created_at: Optional[datetime]
    trade_suspended_by_user: bool
    currency: str


class PositionInfo(TypedDict):
    """Type definition for position information."""

    symbol: str
    qty: float
    market_value: float
    cost_basis: float
    unrealized_pl: float
    unrealized_plpc: float
    current_price: float
    lastday_price: float
    change_today: float
    avg_entry_price: float
    side: str


class OrderInfo(TypedDict):
    """Type definition for order information."""

    id: str
    client_order_id: str
    created_at: datetime
    updated_at: Optional[datetime]
    submitted_at: Optional[datetime]
    filled_at: Optional[datetime]
    expired_at: Optional[datetime]
    canceled_at: Optional[datetime]
    failed_at: Optional[datetime]
    asset_id: str
    symbol: str
    asset_class: str
    qty: float
    filled_qty: float
    type: str
    side: str
    time_in_force: str
    limit_price: Optional[float]
    stop_price: Optional[float]
    filled_avg_price: Optional[float]
    status: str


class HistoricalData(TypedDict):
    """Type definition for historical data."""

    bars: Dict[str, List[Dict[str, Any]]]


class ClockInfo(TypedDict):
    """Type definition for market clock information."""

    is_open: bool
    next_open: Optional[datetime]
    next_close: Optional[datetime]
    timestamp: Optional[datetime]


class AssetInfo(TypedDict):
    """Type definition for asset information."""

    id: str
    symbol: str
    name: str
    status: str
    tradable: bool
    marginable: bool
    shortable: bool
    easy_to_borrow: bool
    fractionable: bool


def safe_float(value: Union[str, float, Any, None]) -> float:
    """Safely convert a value to float, returning 0.0 if conversion fails."""
    if value is None:
        return 0.0
    try:
        return float(str(value))
    except (ValueError, TypeError):
        return 0.0


class AlpacaClient:
    """Client for interacting with Alpaca API."""

    def __init__(self, api_key: str, secret_key: str, paper: bool = True) -> None:
        """Initialize AlpacaClient with API credentials.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Whether to use paper trading (default: True)
        """
        self.trading_client = TradingClient(api_key, secret_key, paper=paper)
        self.data_client = StockHistoricalDataClient(api_key, secret_key)
        self.logger = logger

    def get_account(self) -> AccountInfo:
        """Get the account information."""
        try:
            account = self.trading_client.get_account()
            return AccountInfo(
                id=getattr(account, "id", ""),
                cash=safe_float(getattr(account, "cash", 0.0)),
                portfolio_value=safe_float(getattr(account, "portfolio_value", 0.0)),
                buying_power=safe_float(getattr(account, "buying_power", 0.0)),
                equity=safe_float(getattr(account, "equity", 0.0)),
                long_market_value=safe_float(getattr(account, "long_market_value", 0.0)),
                short_market_value=safe_float(getattr(account, "short_market_value", 0.0)),
                initial_margin=safe_float(getattr(account, "initial_margin", 0.0)),
                maintenance_margin=safe_float(getattr(account, "maintenance_margin", 0.0)),
                last_equity=safe_float(getattr(account, "last_equity", 0.0)),
                multiplier=safe_float(getattr(account, "multiplier", 1.0)),
                status=getattr(account, "status", ""),
                trading_blocked=getattr(account, "trading_blocked", False),
                transfers_blocked=getattr(account, "transfers_blocked", False),
                account_blocked=getattr(account, "account_blocked", False),
                created_at=getattr(account, "created_at", None),
                trade_suspended_by_user=getattr(account, "trade_suspended_by_user", False),
                currency=getattr(account, "currency", "USD"),
            )
        except Exception as e:
            self.logger.error(f"Error getting account information: {e}")
            return AccountInfo(
                id="",
                cash=0.0,
                portfolio_value=0.0,
                buying_power=0.0,
                equity=0.0,
                long_market_value=0.0,
                short_market_value=0.0,
                initial_margin=0.0,
                maintenance_margin=0.0,
                last_equity=0.0,
                multiplier=1.0,
                status="",
                trading_blocked=False,
                transfers_blocked=False,
                account_blocked=False,
                created_at=None,
                trade_suspended_by_user=False,
                currency="USD",
            )

    def get_positions(self) -> List[PositionInfo]:
        """Get all open positions."""
        try:
            positions = self.trading_client.get_all_positions()
            return [self._format_position(pos) for pos in positions]
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []

    def _format_position(self, position: Position) -> PositionInfo:
        """Format a position object into a dictionary."""
        return PositionInfo(
            symbol=getattr(position, "symbol", ""),
            qty=safe_float(getattr(position, "qty", 0)),
            market_value=safe_float(getattr(position, "market_value", 0.0)),
            cost_basis=safe_float(getattr(position, "cost_basis", 0.0)),
            unrealized_pl=safe_float(getattr(position, "unrealized_pl", 0.0)),
            unrealized_plpc=safe_float(getattr(position, "unrealized_plpc", 0.0)),
            current_price=safe_float(getattr(position, "current_price", 0.0)),
            lastday_price=safe_float(getattr(position, "lastday_price", 0.0)),
            change_today=safe_float(getattr(position, "change_today", 0.0)),
            avg_entry_price=safe_float(getattr(position, "avg_entry_price", 0.0)),
            side=getattr(position, "side", ""),
        )

    def get_historical_data(
        self,
        symbols: List[str],
        start: datetime,
        end: datetime,
        timeframe: str = "1Min",
    ) -> HistoricalData:
        """Get historical bar data for the given symbols."""
        try:
            bars = self.data_client.get_bars(
                symbols,
                start=start,
                end=end,
                timeframe=TimeFrame(timeframe),
                adjustment="raw",
            )
            return HistoricalData(bars=bars.data.dict() if bars else {})
        except Exception as e:
            self.logger.error(f"Error getting historical data: {e}")
            return HistoricalData(bars={})

    def place_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        type: str = "market",
        time_in_force: str = "day",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Place an order.

        Args:
            symbol: Stock symbol
            qty: Quantity to trade
            side: Buy or sell
            type: Order type (market, limit, stop, stop_limit)
            time_in_force: Time in force (day, gtc, opg, cls, ioc, fok)
            limit_price: Limit price for limit orders
            stop_price: Stop price for stop orders

        Returns:
            Dictionary containing order information
        """
        try:
            order = self.trading_client.submit_order(
                symbol=symbol,
                qty=qty,
                side=OrderSide(side),
                type=OrderType(type),
                time_in_force=TimeInForce(time_in_force),
                limit_price=limit_price,
                stop_price=stop_price,
            )

            return {
                "id": order.id,
                "symbol": order.symbol,
                "qty": float(order.qty),
                "side": order.side,
                "type": order.type,
                "time_in_force": order.time_in_force,
                "status": order.status,
                "filled_qty": float(order.filled_qty),
                "filled_avg_price": float(order.filled_avg_price),
                "created_at": order.created_at,
                "updated_at": order.updated_at,
            }
        except APIError as e:
            self.logger.error(f"Error placing order: {e}")
            return {}

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order."""
        try:
            self.trading_client.cancel_order_by_id(order_id)
            return True
        except Exception as e:
            print(f"Error canceling order: {e}")
            return False

    def get_orders(
        self, status: Optional[str] = None, limit: Optional[int] = None
    ) -> List[OrderInfo]:
        """Get a list of orders."""
        try:
            params = {}
            if status:
                params["status"] = status
            if limit:
                params["limit"] = limit

            request = GetOrdersRequest(**params)
            orders = self.trading_client.get_orders(filter=request)
            return [self._format_order(order) for order in orders]
        except Exception as e:
            self.logger.error(f"Error getting orders: {e}")
            return []

    def _format_order(self, order: Union[Order, Dict[str, Any]]) -> OrderInfo:
        """Format an order object into a dictionary."""
        return OrderInfo(
            id=getattr(order, "id", ""),
            client_order_id=getattr(order, "client_order_id", ""),
            created_at=getattr(order, "created_at", datetime.now()),
            updated_at=getattr(order, "updated_at", None),
            submitted_at=getattr(order, "submitted_at", None),
            filled_at=getattr(order, "filled_at", None),
            expired_at=getattr(order, "expired_at", None),
            canceled_at=getattr(order, "canceled_at", None),
            failed_at=getattr(order, "failed_at", None),
            asset_id=getattr(order, "asset_id", ""),
            symbol=getattr(order, "symbol", ""),
            asset_class=getattr(order, "asset_class", ""),
            qty=float(getattr(order, "qty", 0.0)),
            filled_qty=float(getattr(order, "filled_qty", 0.0)),
            type=getattr(order, "type", ""),
            side=getattr(order, "side", ""),
            time_in_force=getattr(order, "time_in_force", ""),
            limit_price=float(getattr(order, "limit_price", 0.0))
            if hasattr(order, "limit_price")
            else None,
            stop_price=float(getattr(order, "stop_price", 0.0))
            if hasattr(order, "stop_price")
            else None,
            filled_avg_price=float(getattr(order, "filled_avg_price", 0.0))
            if hasattr(order, "filled_avg_price")
            else None,
            status=getattr(order, "status", "unknown"),
        )

    def get_clock(self) -> ClockInfo:
        """Get the current market clock information."""
        try:
            clock: Clock = self.trading_client.get_clock()
            return {
                "is_open": clock.is_open,
                "next_open": clock.next_open,
                "next_close": clock.next_close,
                "timestamp": clock.timestamp,
            }
        except Exception as e:
            self.logger.error(f"Error getting clock: {e}")
            return {"is_open": False, "next_open": None, "next_close": None, "timestamp": None}

    def get_position(self, symbol: str) -> Optional[PositionInfo]:
        """Get position information for a symbol."""
        try:
            position = cast(
                Union[Position, Dict[str, Any]], self.trading_client.get_open_position(symbol)
            )
            return PositionInfo(
                symbol=str(position.symbol) if hasattr(position, "symbol") else "",
                qty=float(position.qty) if hasattr(position, "qty") else 0.0,
                market_value=float(position.market_value)
                if hasattr(position, "market_value")
                else 0.0,
                current_price=float(position.current_price)
                if hasattr(position, "current_price")
                else 0.0,
                avg_entry_price=float(position.avg_entry_price)
                if hasattr(position, "avg_entry_price")
                else 0.0,
                cost_basis=float(position.cost_basis) if hasattr(position, "cost_basis") else 0.0,
                unrealized_pl=float(position.unrealized_pl)
                if hasattr(position, "unrealized_pl")
                else 0.0,
                unrealized_plpc=float(position.unrealized_plpc)
                if hasattr(position, "unrealized_plpc")
                else 0.0,
                lastday_price=float(position.lastday_price)
                if hasattr(position, "lastday_price")
                else 0.0,
                change_today=float(position.change_today)
                if hasattr(position, "change_today")
                else 0.0,
                side=str(position.side) if hasattr(position, "side") else "",
            )
        except Exception as e:
            self.logger.error(f"Error getting position: {e}")
            return None

    def get_assets(self, status: str = "active") -> List[AssetInfo]:
        """Get all available assets."""
        try:
            assets = cast(Union[List[Asset], Dict[str, Any]], self.trading_client.get_all_assets())
            if not isinstance(assets, list):
                return []

            return [
                AssetInfo(
                    id=str(asset.id) if hasattr(asset, "id") else "",
                    symbol=str(asset.symbol) if hasattr(asset, "symbol") else "",
                    name=str(asset.name) if hasattr(asset, "name") else "",
                    status=str(asset.status) if hasattr(asset, "status") else "",
                    tradable=bool(asset.tradable) if hasattr(asset, "tradable") else False,
                    marginable=bool(asset.marginable) if hasattr(asset, "marginable") else False,
                    shortable=bool(asset.shortable) if hasattr(asset, "shortable") else False,
                    easy_to_borrow=bool(asset.easy_to_borrow)
                    if hasattr(asset, "easy_to_borrow")
                    else False,
                    fractionable=bool(asset.fractionable)
                    if hasattr(asset, "fractionable")
                    else False,
                )
                for asset in assets
            ]
        except Exception as e:
            self.logger.error(f"Error getting assets: {e}")
            return []

    def submit_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        type: str = "market",
        time_in_force: str = "day",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> OrderInfo:
        """Submit an order to Alpaca."""
        try:
            order_data: Dict[str, Any] = {
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "type": type,
                "time_in_force": time_in_force,
            }

            if limit_price is not None:
                order_data["limit_price"] = limit_price
            if stop_price is not None:
                order_data["stop_price"] = stop_price

            if type == "market":
                order = self.trading_client.submit_order(MarketOrderRequest(**order_data))
            elif type == "limit":
                order = self.trading_client.submit_order(LimitOrderRequest(**order_data))
            elif type == "stop":
                order = self.trading_client.submit_order(StopOrderRequest(**order_data))
            else:
                raise ValueError(f"Unsupported order type: {type}")

            return self._format_order(order)
        except Exception as e:
            self.logger.error(f"Error submitting order: {e}")
            return OrderInfo(
                id="",
                client_order_id="",
                created_at=datetime.now(),
                updated_at=None,
                submitted_at=None,
                filled_at=None,
                expired_at=None,
                canceled_at=None,
                failed_at=datetime.now(),
                asset_id="",
                symbol=symbol,
                asset_class="",
                qty=qty,
                filled_qty=0.0,
                type=type,
                side=side,
                time_in_force=time_in_force,
                limit_price=limit_price,
                stop_price=stop_price,
                filled_avg_price=None,
                status="failed",
            )

    def get_order(self, order_id: str) -> Optional[OrderInfo]:
        """Get an order by ID."""
        try:
            order = self.trading_client.get_order_by_id(order_id)
            return self._format_order(order)
        except Exception as e:
            self.logger.error(f"Error getting order: {e}")
            return None

    def get_asset(self, symbol: str) -> AssetInfo:
        """Get asset information for a symbol."""
        try:
            asset = self.trading_client.get_asset(symbol)
            return AssetInfo(
                id=getattr(asset, "id", ""),
                symbol=getattr(asset, "symbol", ""),
                name=getattr(asset, "name", ""),
                status=getattr(asset, "status", ""),
                tradable=bool(getattr(asset, "tradable", False)),
                marginable=bool(getattr(asset, "marginable", False)),
                shortable=bool(getattr(asset, "shortable", False)),
                easy_to_borrow=bool(getattr(asset, "easy_to_borrow", False)),
                fractionable=bool(getattr(asset, "fractionable", False)),
            )
        except Exception as e:
            self.logger.error(f"Error getting asset: {e}")
            return AssetInfo(
                id="",
                symbol=symbol,
                name="",
                status="error",
                tradable=False,
                marginable=False,
                shortable=False,
                easy_to_borrow=False,
                fractionable=False,
            )
