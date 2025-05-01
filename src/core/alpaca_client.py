"""Alpaca API client for trading operations."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.models import BarSet
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, OrderType, QueryOrderStatus, TimeInForce
from alpaca.trading.models import Asset, Clock, Order, Position
from alpaca.trading.requests import OrderRequest

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class AccountInfo:
    """Account information."""

    def __init__(
        self,
        id: str,
        cash: float,
        portfolio_value: float,
        buying_power: float,
        equity: float,
        long_market_value: float,
        short_market_value: float,
        initial_margin: float,
        maintenance_margin: float,
        last_equity: float,
        multiplier: float,
        status: str,
        trading_blocked: bool,
        transfers_blocked: bool,
        account_blocked: bool,
        created_at: Optional[datetime],
        trade_suspended_by_user: bool,
        currency: str,
    ):
        """Initialize account info."""
        self.id = id
        self.cash = cash
        self.portfolio_value = portfolio_value
        self.buying_power = buying_power
        self.equity = equity
        self.long_market_value = long_market_value
        self.short_market_value = short_market_value
        self.initial_margin = initial_margin
        self.maintenance_margin = maintenance_margin
        self.last_equity = last_equity
        self.multiplier = multiplier
        self.status = status
        self.trading_blocked = trading_blocked
        self.transfers_blocked = transfers_blocked
        self.account_blocked = account_blocked
        self.created_at = created_at
        self.trade_suspended_by_user = trade_suspended_by_user
        self.currency = currency


class PositionInfo:
    """Position information."""

    def __init__(
        self,
        symbol: str,
        qty: float,
        side: str,
        avg_entry_price: float,
        current_price: float,
        market_value: float,
        cost_basis: float,
        unrealized_pl: float,
        unrealized_plpc: float,
        lastday_price: float,
        change_today: float,
    ):
        """Initialize position info."""
        self.symbol = symbol
        self.qty = qty
        self.side = side
        self.avg_entry_price = avg_entry_price
        self.current_price = current_price
        self.market_value = market_value
        self.cost_basis = cost_basis
        self.unrealized_pl = unrealized_pl
        self.unrealized_plpc = unrealized_plpc
        self.lastday_price = lastday_price
        self.change_today = change_today


class OrderInfo:
    """Order information."""

    def __init__(
        self,
        id: str,
        symbol: str,
        qty: float,
        side: str,
        type: str,
        time_in_force: str,
        status: str,
        filled_qty: float,
        filled_avg_price: float,
        created_at: datetime,
        updated_at: datetime,
    ):
        """Initialize order info."""
        self.id = id
        self.symbol = symbol
        self.qty = qty
        self.side = side
        self.type = type
        self.time_in_force = time_in_force
        self.status = status
        self.filled_qty = filled_qty
        self.filled_avg_price = filled_avg_price
        self.created_at = created_at
        self.updated_at = updated_at


class AssetInfo:
    """Asset information."""

    def __init__(
        self,
        id: str,
        symbol: str,
        name: str,
        status: str,
        tradable: bool,
        marginable: bool,
        shortable: bool,
        easy_to_borrow: bool,
        fractionable: bool,
    ):
        """Initialize asset info."""
        self.id = id
        self.symbol = symbol
        self.name = name
        self.status = status
        self.tradable = tradable
        self.marginable = marginable
        self.shortable = shortable
        self.easy_to_borrow = easy_to_borrow
        self.fractionable = fractionable


class ClockInfo:
    """Market clock information."""

    def __init__(
        self,
        is_open: bool,
        next_open: Optional[datetime],
        next_close: Optional[datetime],
        timestamp: Optional[datetime],
    ):
        """Initialize market clock info."""
        self.is_open = is_open
        self.next_open = next_open
        self.next_close = next_close
        self.timestamp = timestamp


class HistoricalData:
    """Historical market data."""

    def __init__(
        self,
        timestamp: List[datetime],
        open: List[float],
        high: List[float],
        low: List[float],
        close: List[float],
        volume: List[float],
        trade_count: List[float],
        vwap: List[float],
    ):
        """Initialize historical data."""
        self.timestamp = timestamp
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.trade_count = trade_count
        self.vwap = vwap


def safe_float(value: Union[str, float, Any, None]) -> float:
    """Convert value to float safely.

    Args:
        value: Value to convert

    Returns:
        float: Converted value or 0.0 if conversion fails
    """
    try:
        if value is None:
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0


class AlpacaClient:
    """Client for interacting with Alpaca API."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://paper-api.alpaca.markets",
    ):
        """Initialize Alpaca client.

        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            base_url: Alpaca API base URL (default: paper trading)
        """
        self.trading_client = TradingClient(api_key, api_secret, base_url)
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
                id=account.id,
                cash=safe_float(account.cash),
                portfolio_value=safe_float(account.portfolio_value),
                buying_power=safe_float(account.buying_power),
                equity=safe_float(account.equity),
                long_market_value=safe_float(account.long_market_value),
                short_market_value=safe_float(account.short_market_value),
                initial_margin=safe_float(account.initial_margin),
                maintenance_margin=safe_float(account.maintenance_margin),
                last_equity=safe_float(account.last_equity),
                multiplier=safe_float(account.multiplier),
                status=account.status,
                trading_blocked=account.trading_blocked,
                transfers_blocked=account.transfers_blocked,
                account_blocked=account.account_blocked,
                created_at=account.created_at,
                trade_suspended_by_user=account.trade_suspended_by_user,
                currency=account.currency,
            )
        except Exception as e:
            self.logger.error(f"Error getting account: {e}")
            raise

    def get_positions(self) -> List[PositionInfo]:
        """Get all positions.

        Returns:
            List[PositionInfo]: List of positions
        """
        try:
            positions = self.trading_client.get_all_positions()
            return [self._format_position(p) for p in positions]
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            raise

    def get_historical_data(
        self,
        symbols: List[str],
        timeframe: TimeFrame,
        start: datetime,
        end: datetime,
    ) -> HistoricalData:
        """Get historical data for symbols.

        Args:
            symbols: List of symbols to get data for
            timeframe: Timeframe for the data
            start: Start date
            end: End date

        Returns:
            HistoricalData: Historical data
        """
        try:
            request = StockBarsRequest(
                symbol_or_symbols=symbols,
                timeframe=timeframe,
                start=start,
                end=end,
            )
            bars = self.data_client.get_stock_bars(request)
            return self._format_bars(bars)
        except Exception as e:
            self.logger.error(f"Error getting historical data: {e}")
            raise

    def _format_bars(self, bars: BarSet) -> HistoricalData:
        """Format bar data.

        Args:
            bars: Bar data from Alpaca

        Returns:
            HistoricalData: Formatted historical data
        """
        data = HistoricalData(
            timestamp=[],
            open=[],
            high=[],
            low=[],
            close=[],
            volume=[],
            trade_count=[],
            vwap=[],
        )
        for bar in bars:
            data.timestamp.append(bar.timestamp)
            data.open.append(safe_float(bar.open))
            data.high.append(safe_float(bar.high))
            data.low.append(safe_float(bar.low))
            data.close.append(safe_float(bar.close))
            data.volume.append(safe_float(bar.volume))
            data.trade_count.append(safe_float(bar.trade_count))
            data.vwap.append(safe_float(bar.vwap))
        return data

    def place_order(
        self,
        symbol: str,
        qty: float,
        side: OrderSide,
        type: OrderType = OrderType.MARKET,
        time_in_force: TimeInForce = TimeInForce.DAY,
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
            order_data = {
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

            order = self.trading_client.submit_order(OrderRequest(**order_data))
            return self._format_order(order)
        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            raise

    def get_orders(
        self, status: Optional[QueryOrderStatus] = None, limit: int = 100
    ) -> List[OrderInfo]:
        """Get orders.

        Args:
            status: Order status to filter by (optional)
            limit: Maximum number of orders to return (default: 100)

        Returns:
            List[OrderInfo]: List of orders
        """
        try:
            orders = self.trading_client.get_orders(status=status, limit=limit)
            return [self._format_order(o) for o in orders]
        except Exception as e:
            self.logger.error(f"Error getting orders: {e}")
            raise

    def get_market_clock(self) -> ClockInfo:
        """Get market clock information.

        Returns:
            ClockInfo: Market clock information
        """
        try:
            clock = self.trading_client.get_clock()
            return ClockInfo(
                is_open=clock.is_open,
                next_open=clock.next_open,
                next_close=clock.next_close,
                timestamp=clock.timestamp,
            )
        except Exception as e:
            self.logger.error(f"Error getting market clock: {e}")
            raise

    def get_position(self, symbol: str) -> Optional[PositionInfo]:
        """Get position for a symbol.

        Args:
            symbol: Symbol to get position for

        Returns:
            Optional[PositionInfo]: Position information if found
        """
        try:
            position = self.trading_client.get_position(symbol)
            return self._format_position(position)
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
                id=asset.id,
                symbol=asset.symbol,
                name=asset.name,
                status=asset.status,
                tradable=asset.tradable,
                marginable=asset.marginable,
                shortable=asset.shortable,
                easy_to_borrow=asset.easy_to_borrow,
                fractionable=asset.fractionable,
            )
        except Exception as e:
            self.logger.error(f"Error getting asset: {e}")
            return None

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order.

        Args:
            order_id: Order ID to cancel

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
            order_id: Order ID to get

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
        """Format position data.

        Args:
            position: Position data from Alpaca

        Returns:
            PositionInfo: Formatted position information
        """
        return PositionInfo(
            symbol=position.symbol,
            qty=safe_float(position.qty),
            side=position.side,
            avg_entry_price=safe_float(position.avg_entry_price),
            current_price=safe_float(position.current_price),
            market_value=safe_float(position.market_value),
            cost_basis=safe_float(position.cost_basis),
            unrealized_pl=safe_float(position.unrealized_pl),
            unrealized_plpc=safe_float(position.unrealized_plpc),
            lastday_price=safe_float(position.lastday_price),
            change_today=safe_float(position.change_today),
        )

    def _format_order(self, order: Order) -> OrderInfo:
        """Format order data.

        Args:
            order: Order data from Alpaca

        Returns:
            OrderInfo: Formatted order information
        """
        return OrderInfo(
            id=order.id,
            symbol=order.symbol,
            qty=safe_float(order.qty),
            side=str(order.side),
            type=str(order.type),
            time_in_force=str(order.time_in_force),
            status=order.status,
            filled_qty=safe_float(order.filled_qty),
            filled_avg_price=safe_float(order.filled_avg_price),
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
