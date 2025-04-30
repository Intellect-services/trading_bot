"""Alpaca API client for trading operations."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TypedDict, TypeVar, Union, cast

import alpaca_trade_api as tradeapi
import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.models import BarSet
from alpaca.data.requests import GetAssetsRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import (AssetClass, OrderSide, OrderType,
                                  QueryOrderStatus, TimeInForce)
from alpaca.trading.models import Asset, Clock, Order, Position
from alpaca.trading.models import TradeAccount as AlpacaTradeAccount
from alpaca.trading.requests import (GetOrdersRequest, LimitOrderRequest,
                                     MarketOrderRequest, OrderRequest,
                                     StopOrderRequest)
from alpaca_trade_api.rest import APIError

from src.core.alpaca_types import Bar
from src.types import Order, TradeAccount
from src.utils.config import get_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

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
    side: str
    avg_entry_price: float
    current_price: float
    market_value: float
    cost_basis: float
    unrealized_pl: float
    unrealized_plpc: float
    unrealized_intraday_pl: float
    unrealized_intraday_plpc: float
    lastday_price: float
    change_today: float


class OrderInfo(TypedDict):
    """Type definition for order information."""

    id: str
    symbol: str
    qty: float
    side: str
    type: str
    time_in_force: str
    status: str
    filled_qty: float
    filled_avg_price: float
    created_at: datetime
    updated_at: datetime


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


class ClockInfo(TypedDict):
    """Type definition for clock information."""

    is_open: bool
    next_open: Optional[datetime]
    next_close: Optional[datetime]
    timestamp: Optional[datetime]


class HistoricalData(TypedDict):
    """Type definition for historical data."""

    timestamp: List[datetime]
    open: List[float]
    high: List[float]
    low: List[float]
    close: List[float]
    volume: List[int]
    trade_count: List[int]
    vwap: List[float]


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

    def __init__(self, api_key: str, api_secret: str, base_url: str = "https://paper-api.alpaca.markets"):
        """Initialize the Alpaca client.

        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            base_url: Base URL for the API (defaults to paper trading)
        """
        self.trading_client = TradingClient(api_key, api_secret, paper=True)
        self.data_client = StockHistoricalDataClient(api_key, api_secret)
        self.logger = setup_logger(__name__)

    def get_account(self) -> AccountInfo:
        """Get account information.

        Returns:
            AccountInfo: Account information
        """
        try:
            account = self.trading_client.get_account()
            return AccountInfo(
                id=getattr(account, "id", ""),
                cash=float(getattr(account, "cash", 0.0)),
                portfolio_value=float(getattr(account, "portfolio_value", 0.0)),
                buying_power=float(getattr(account, "buying_power", 0.0)),
                equity=float(getattr(account, "equity", 0.0)),
                long_market_value=float(getattr(account, "long_market_value", 0.0)),
                short_market_value=float(getattr(account, "short_market_value", 0.0)),
                initial_margin=float(getattr(account, "initial_margin", 0.0)),
                maintenance_margin=float(getattr(account, "maintenance_margin", 0.0)),
                last_equity=float(getattr(account, "last_equity", 0.0)),
                multiplier=float(getattr(account, "multiplier", 0.0)),
                status=str(getattr(account, "status", "")),
                trading_blocked=bool(getattr(account, "trading_blocked", False)),
                transfers_blocked=bool(getattr(account, "transfers_blocked", False)),
                account_blocked=bool(getattr(account, "account_blocked", False)),
                created_at=getattr(account, "created_at", None),
                trade_suspended_by_user=bool(getattr(account, "trade_suspended_by_user", False)),
                currency=str(getattr(account, "currency", "")),
            )
        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
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
                multiplier=0.0,
                status="",
                trading_blocked=False,
                transfers_blocked=False,
                account_blocked=False,
                created_at=None,
                trade_suspended_by_user=False,
                currency="",
            )

    def get_positions(self) -> List[PositionInfo]:
        """Get all positions.

        Returns:
            List[PositionInfo]: List of positions
        """
        try:
            positions = self.trading_client.get_all_positions()
            return [self._format_position(position) for position in positions]
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []

    def get_historical_data(
        self, symbols: List[str], timeframe: str = "1D", start: Optional[datetime] = None, end: Optional[datetime] = None
    ) -> HistoricalData:
        """Get historical data for symbols.

        Args:
            symbols: List of symbols to get data for
            timeframe: Timeframe for the data (default: "1D")
            start: Start date (optional)
            end: End date (optional)

        Returns:
            HistoricalData: Historical data
        """
        try:
            bars = self.data_client.get_bars(
                symbols,
                TimeFrame.from_str(timeframe),
                start=start,
                end=end,
                adjustment="raw",
            )
            return HistoricalData(
                timestamp=bars.data.dict()["timestamp"],
                open=bars.data.dict()["open"],
                high=bars.data.dict()["high"],
                low=bars.data.dict()["low"],
                close=bars.data.dict()["close"],
                volume=bars.data.dict()["volume"],
                trade_count=bars.data.dict()["trade_count"],
                vwap=bars.data.dict()["vwap"],
            )
        except Exception as e:
            self.logger.error(f"Error getting historical data: {e}")
            return HistoricalData(
                timestamp=[],
                open=[],
                high=[],
                low=[],
                close=[],
                volume=[],
                trade_count=[],
                vwap=[],
            )

    def place_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        type: str = "market",
        time_in_force: str = "day",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> OrderInfo:
        """Place an order.

        Args:
            symbol: Symbol to trade
            qty: Quantity to trade
            side: Side of the trade (buy/sell)
            type: Type of order (default: market)
            time_in_force: Time in force (default: day)
            limit_price: Limit price (optional)
            stop_price: Stop price (optional)

        Returns:
            OrderInfo: Order information
        """
        try:
            order = self.trading_client.submit_order(
                symbol=symbol,
                qty=qty,
                side=OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL,
                type=OrderType.MARKET if type.lower() == "market" else OrderType.LIMIT,
                time_in_force=TimeInForce.DAY if time_in_force.lower() == "day" else TimeInForce.GTC,
                limit_price=limit_price,
                stop_price=stop_price,
            )
            return self._format_order(order)
        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            return OrderInfo(
                id="",
                symbol=symbol,
                qty=qty,
                side=side,
                type=type,
                time_in_force=time_in_force,
                status="failed",
                filled_qty=0.0,
                filled_avg_price=0.0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

    def get_orders(self, status: Optional[str] = None, limit: int = 100) -> List[OrderInfo]:
        """Get orders.

        Args:
            status: Order status to filter by (optional)
            limit: Maximum number of orders to return (default: 100)

        Returns:
            List[OrderInfo]: List of orders
        """
        try:
            orders = self.trading_client.get_orders(status=status, limit=limit)
            return [self._format_order(order) for order in orders]
        except Exception as e:
            self.logger.error(f"Error getting orders: {e}")
            return []

    def get_market_clock(self) -> ClockInfo:
        """Get market clock information.

        Returns:
            ClockInfo: Market clock information
        """
        try:
            clock = self.trading_client.get_clock()
            return ClockInfo(
                is_open=bool(getattr(clock, "is_open", False)),
                next_open=getattr(clock, "next_open", None),
                next_close=getattr(clock, "next_close", None),
                timestamp=getattr(clock, "timestamp", None),
            )
        except Exception as e:
            self.logger.error(f"Error getting market clock: {e}")
            return ClockInfo(
                is_open=False,
                next_open=None,
                next_close=None,
                timestamp=None,
            )

    def get_position(self, symbol: str) -> Optional[PositionInfo]:
        """Get position for a symbol.

        Args:
            symbol: Symbol to get position for

        Returns:
            Optional[PositionInfo]: Position information if found
        """
        try:
            position = cast(
                Union[Position, Dict[str, Any]],
                self.trading_client.get_open_position(symbol),
            )
            return PositionInfo(
                symbol=str(position.symbol) if hasattr(position, "symbol") else "",
                qty=float(position.qty) if hasattr(position, "qty") else 0.0,
                side=str(position.side) if hasattr(position, "side") else "",
                avg_entry_price=float(position.avg_entry_price)
                if hasattr(position, "avg_entry_price")
                else 0.0,
                current_price=float(position.current_price)
                if hasattr(position, "current_price")
                else 0.0,
                market_value=float(position.market_value)
                if hasattr(position, "market_value")
                else 0.0,
                cost_basis=float(position.cost_basis)
                if hasattr(position, "cost_basis")
                else 0.0,
                unrealized_pl=float(position.unrealized_pl)
                if hasattr(position, "unrealized_pl")
                else 0.0,
                unrealized_plpc=float(position.unrealized_plpc)
                if hasattr(position, "unrealized_plpc")
                else 0.0,
                unrealized_intraday_pl=float(position.unrealized_intraday_pl)
                if hasattr(position, "unrealized_intraday_pl")
                else 0.0,
                unrealized_intraday_plpc=float(position.unrealized_intraday_plpc)
                if hasattr(position, "unrealized_intraday_plpc")
                else 0.0,
                lastday_price=float(position.lastday_price)
                if hasattr(position, "lastday_price")
                else 0.0,
                change_today=float(position.change_today)
                if hasattr(position, "change_today")
                else 0.0,
            )
        except Exception as e:
            self.logger.error(f"Error getting position: {e}")
            return None

    def get_asset(self, symbol: str) -> Optional[AssetInfo]:
        """Get asset information.

        Args:
            symbol: Symbol to get asset info for

        Returns:
            Optional[AssetInfo]: Asset information if found
        """
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
            return None

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order.

        Args:
            order_id: ID of the order to cancel

        Returns:
            bool: True if order was cancelled successfully
        """
        try:
            self.trading_client.cancel_order(order_id)
            return True
        except Exception as e:
            self.logger.error(f"Error cancelling order: {e}")
            return False

    def get_order(self, order_id: str) -> Optional[OrderInfo]:
        """Get order by ID.

        Args:
            order_id: ID of the order to get

        Returns:
            Optional[OrderInfo]: Order information if found
        """
        try:
            order = self.trading_client.get_order(order_id)
            return self._format_order(order)
        except Exception as e:
            self.logger.error(f"Error getting order: {e}")
            return None

    def _format_position(self, position: Position) -> PositionInfo:
        """Format position information.

        Args:
            position: Position to format

        Returns:
            PositionInfo: Formatted position information
        """
        try:
            return PositionInfo(
                symbol=str(position.symbol) if hasattr(position, "symbol") else "",
                qty=float(position.qty) if hasattr(position, "qty") else 0.0,
                side=str(position.side) if hasattr(position, "side") else "",
                avg_entry_price=float(position.avg_entry_price)
                if hasattr(position, "avg_entry_price")
                else 0.0,
                current_price=float(position.current_price)
                if hasattr(position, "current_price")
                else 0.0,
                market_value=float(position.market_value)
                if hasattr(position, "market_value")
                else 0.0,
                cost_basis=float(position.cost_basis)
                if hasattr(position, "cost_basis")
                else 0.0,
                unrealized_pl=float(position.unrealized_pl)
                if hasattr(position, "unrealized_pl")
                else 0.0,
                unrealized_plpc=float(position.unrealized_plpc)
                if hasattr(position, "unrealized_plpc")
                else 0.0,
                unrealized_intraday_pl=float(position.unrealized_intraday_pl)
                if hasattr(position, "unrealized_intraday_pl")
                else 0.0,
                unrealized_intraday_plpc=float(position.unrealized_intraday_plpc)
                if hasattr(position, "unrealized_intraday_plpc")
                else 0.0,
                lastday_price=float(position.lastday_price)
                if hasattr(position, "lastday_price")
                else 0.0,
                change_today=float(position.change_today)
                if hasattr(position, "change_today")
                else 0.0,
            )
        except Exception as e:
            self.logger.error(f"Error formatting position: {e}")
            return PositionInfo(
                symbol="",
                qty=0.0,
                side="",
                avg_entry_price=0.0,
                current_price=0.0,
                market_value=0.0,
                cost_basis=0.0,
                unrealized_pl=0.0,
                unrealized_plpc=0.0,
                unrealized_intraday_pl=0.0,
                unrealized_intraday_plpc=0.0,
                lastday_price=0.0,
                change_today=0.0,
            )

    def _format_order(self, order: Order) -> OrderInfo:
        """Format order information.

        Args:
            order: Order to format

        Returns:
            OrderInfo: Formatted order information
        """
        try:
            return OrderInfo(
                id=getattr(order, "id", ""),
                symbol=getattr(order, "symbol", ""),
                qty=float(getattr(order, "qty", 0.0)),
                side=getattr(order, "side", ""),
                type=getattr(order, "type", ""),
                time_in_force=getattr(order, "time_in_force", ""),
                status=getattr(order, "status", ""),
                filled_qty=float(getattr(order, "filled_qty", 0.0)),
                filled_avg_price=float(getattr(order, "filled_avg_price", 0.0)),
                created_at=getattr(order, "created_at", datetime.now()),
                updated_at=getattr(order, "updated_at", datetime.now()),
            )
        except Exception as e:
            self.logger.error(f"Error formatting order: {e}")
            return OrderInfo(
                id="",
                symbol="",
                qty=0.0,
                side="",
                type="",
                time_in_force="",
                status="",
                filled_qty=0.0,
                filled_avg_price=0.0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
