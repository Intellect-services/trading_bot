"""Alpaca API client for trading operations."""

import logging
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional, TypeVar, Union, cast

try:
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.models import Bar, BarSet
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    from alpaca.trading.client import TradingClient
    from alpaca.trading.enums import (
        OrderSide,
        OrderStatus,
        OrderType,
        QueryOrderStatus,
        TimeInForce,
    )
    from alpaca.trading.models import Asset, Clock, Order, Position, TradeAccount
    from alpaca.trading.requests import (
        LimitOrderRequest,
        MarketOrderRequest,
        StopLimitOrderRequest,
        StopOrderRequest,
    )
except ImportError:
    StockHistoricalDataClient = Any
    Bar = Any
    BarSet = Any
    StockBarsRequest = Any
    TimeFrame = Any  # type: ignore[name-defined]
    TradingClient = Any
    OrderSide = Any
    OrderStatus = Any
    OrderType = Any
    QueryOrderStatus = Any
    TimeInForce = Any
    Asset = Any
    Clock = Any
    Order = Any
    Position = Any
    TradeAccount = Any
    LimitOrderRequest = Any
    MarketOrderRequest = Any
    StopLimitOrderRequest = Any
    StopOrderRequest = Any

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
    ) -> None:
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
    ) -> None:
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
    ) -> None:
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
    ) -> None:
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
    ) -> None:
        """Initialize clock info."""
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
    ) -> None:
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
    """Safely convert a value to float.

    Args:
        value: Value to convert

    Returns:
        float: Converted value

    Raises:
        ValueError: If value cannot be converted to float
    """
    if value is None:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


class AlpacaClient:
    """Alpaca API client for trading operations."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://paper-api.alpaca.markets",
    ) -> None:
        """Initialize Alpaca client.

        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            base_url: Base URL for API requests
        """
        self.trading_client = TradingClient(api_key, api_secret, paper=True)
        self.historical_client = StockHistoricalDataClient(api_key, api_secret)

    def get_account(self) -> AccountInfo:
        """Get account information.

        Returns:
            AccountInfo: Account information

        Raises:
            Exception: If API request fails
        """
        try:
            account = cast(TradeAccount, self.trading_client.get_account())
            return AccountInfo(
                id=str(account.id),
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
                status=str(account.status),
                trading_blocked=bool(account.trading_blocked),
                transfers_blocked=bool(account.transfers_blocked),
                account_blocked=bool(account.account_blocked),
                created_at=account.created_at,
                trade_suspended_by_user=bool(account.trade_suspended_by_user),
                currency=str(account.currency),
            )
        except Exception as e:
            logger.error("Error getting account: %s", str(e))
            raise

    def get_positions(self) -> List[PositionInfo]:
        """Get all positions.

        Returns:
            List[PositionInfo]: List of positions

        Raises:
            Exception: If API request fails
        """
        try:
            positions = cast(List[Position], self.trading_client.get_all_positions())
            return [self._format_position(position) for position in positions]
        except Exception as e:
            logger.error("Error getting positions: %s", str(e))
            raise

    def get_historical_data(
        self,
        symbols: List[str],
        timeframe: TimeFrame,
        start: datetime,
        end: datetime,
    ) -> HistoricalData:
        """Get historical market data.

        Args:
            symbols: List of symbols to get data for
            timeframe: Timeframe for data
            start: Start time
            end: End time

        Returns:
            HistoricalData: Historical market data

        Raises:
            Exception: If API request fails
        """
        try:
            request = StockBarsRequest(
                symbol_or_symbols=symbols,
                timeframe=timeframe,
                start=start,
                end=end,
            )
            bars = cast(BarSet, self.historical_client.get_stock_bars(request))
            return self._format_bars(bars)
        except Exception as e:
            logger.error("Error getting historical data: %s", str(e))
            raise

    def _format_bars(self, bars: BarSet) -> HistoricalData:
        """Format bars data.

        Args:
            bars: Raw bars data

        Returns:
            HistoricalData: Formatted historical data
        """
        try:
            timestamps: List[datetime] = []
            opens: List[float] = []
            highs: List[float] = []
            lows: List[float] = []
            closes: List[float] = []
            volumes: List[float] = []
            trade_counts: List[float] = []
            vwaps: List[float] = []

            # Access bars data through the dict-like interface
            for symbol in bars.data.keys():
                symbol_bars = bars.data[symbol]
                for bar in symbol_bars:
                    timestamps.append(bar.timestamp)
                    opens.append(safe_float(bar.open))
                    highs.append(safe_float(bar.high))
                    lows.append(safe_float(bar.low))
                    closes.append(safe_float(bar.close))
                    volumes.append(safe_float(bar.volume))
                    trade_counts.append(safe_float(bar.trade_count))
                    vwaps.append(safe_float(bar.vwap))

            return HistoricalData(
                timestamp=timestamps,
                open=opens,
                high=highs,
                low=lows,
                close=closes,
                volume=volumes,
                trade_count=trade_counts,
                vwap=vwaps,
            )
        except Exception as e:
            logger.error("Error formatting bars: %s", str(e))
            raise

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
            side: Order side (buy/sell)
            type: Order type
            time_in_force: Time in force
            limit_price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)

        Returns:
            OrderInfo: Order information

        Raises:
            Exception: If API request fails
        """
        try:
            # Create the appropriate order request based on the order type
            if type == OrderType.MARKET:
                order = self.trading_client.submit_order(
                    MarketOrderRequest(
                        symbol=symbol,
                        qty=qty,
                        side=side,
                        time_in_force=time_in_force,
                    )
                )
            elif type == OrderType.LIMIT:
                if limit_price is None:
                    raise ValueError("Limit price is required for limit orders")
                order = self.trading_client.submit_order(
                    LimitOrderRequest(
                        symbol=symbol,
                        qty=qty,
                        side=side,
                        time_in_force=time_in_force,
                        limit_price=limit_price,
                    )
                )
            elif type == OrderType.STOP:
                if stop_price is None:
                    raise ValueError("Stop price is required for stop orders")
                order = self.trading_client.submit_order(
                    StopOrderRequest(
                        symbol=symbol,
                        qty=qty,
                        side=side,
                        time_in_force=time_in_force,
                        stop_price=stop_price,
                    )
                )
            elif type == OrderType.STOP_LIMIT:
                if limit_price is None or stop_price is None:
                    raise ValueError(
                        "Both limit and stop prices are required for stop limit orders"
                    )
                order = self.trading_client.submit_order(
                    StopLimitOrderRequest(
                        symbol=symbol,
                        qty=qty,
                        side=side,
                        time_in_force=time_in_force,
                        limit_price=limit_price,
                        stop_price=stop_price,
                    )
                )
            else:
                raise ValueError(f"Unsupported order type: {type}")

            return self._format_order(cast(Order, order))
        except Exception as e:
            logger.error("Error placing order: %s", str(e))
            raise

    def get_orders(
        self, status: Optional[QueryOrderStatus] = None, limit: int = 100
    ) -> List[OrderInfo]:
        """Get orders.

        Args:
            status: Order status to filter by
            limit: Maximum number of orders to return

        Returns:
            List[OrderInfo]: List of orders

        Raises:
            Exception: If API request fails
        """
        try:
            orders = cast(List[Order], self.trading_client.get_orders())
            if status is not None:
                orders = [
                    order for order in orders if QueryOrderStatus(str(order.status)) == status
                ]
            if limit > 0:
                orders = orders[:limit]
            return [self._format_order(order) for order in orders]
        except Exception as e:
            logger.error("Error getting orders: %s", str(e))
            raise

    def get_market_clock(self) -> ClockInfo:
        """Get market clock information.

        Returns:
            ClockInfo: Market clock information

        Raises:
            Exception: If API request fails
        """
        try:
            clock = cast(Clock, self.trading_client.get_clock())
            return ClockInfo(
                is_open=bool(clock.is_open),
                next_open=clock.next_open,
                next_close=clock.next_close,
                timestamp=clock.timestamp,
            )
        except Exception as e:
            logger.error("Error getting market clock: %s", str(e))
            raise

    def get_position(self, symbol: str) -> Optional[PositionInfo]:
        """Get position for a symbol.

        Args:
            symbol: Symbol to get position for

        Returns:
            Optional[PositionInfo]: Position information if exists

        Raises:
            Exception: If API request fails
        """
        try:
            position = cast(Position, self.trading_client.get_open_position(symbol))
            return self._format_position(position)
        except Exception as e:
            logger.error("Error getting position: %s", str(e))
            raise

    def get_asset(self, symbol: str) -> Optional[AssetInfo]:
        """Get asset information.

        Args:
            symbol: Symbol to get asset for

        Returns:
            Optional[AssetInfo]: Asset information if exists

        Raises:
            Exception: If API request fails
        """
        try:
            asset = cast(Asset, self.trading_client.get_asset(symbol))
            return AssetInfo(
                id=str(asset.id),
                symbol=str(asset.symbol),
                name=str(asset.name),
                status=str(asset.status),
                tradable=bool(asset.tradable),
                marginable=bool(asset.marginable),
                shortable=bool(asset.shortable),
                easy_to_borrow=bool(asset.easy_to_borrow),
                fractionable=bool(asset.fractionable),
            )
        except Exception as e:
            logger.error("Error getting asset: %s", str(e))
            raise

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order.

        Args:
            order_id: ID of order to cancel

        Returns:
            bool: True if order was cancelled

        Raises:
            Exception: If API request fails
        """
        try:
            self.trading_client.cancel_order_by_id(order_id)
            return True
        except Exception as e:
            logger.error("Error cancelling order: %s", str(e))
            raise

    def get_order(self, order_id: str) -> Optional[OrderInfo]:
        """Get order by ID.

        Args:
            order_id: ID of order to get

        Returns:
            Optional[OrderInfo]: Order information if exists

        Raises:
            Exception: If API request fails
        """
        try:
            order = cast(Order, self.trading_client.get_order_by_id(order_id))
            return self._format_order(order)
        except Exception as e:
            logger.error("Error getting order: %s", str(e))
            raise

    def _format_position(self, position: Position) -> PositionInfo:
        """Format position data.

        Args:
            position: Raw position data

        Returns:
            PositionInfo: Formatted position information
        """
        try:
            return PositionInfo(
                symbol=str(position.symbol),
                qty=safe_float(position.qty),
                side=str(position.side),
                avg_entry_price=safe_float(position.avg_entry_price),
                current_price=safe_float(position.current_price),
                market_value=safe_float(position.market_value),
                cost_basis=safe_float(position.cost_basis),
                unrealized_pl=safe_float(position.unrealized_pl),
                unrealized_plpc=safe_float(position.unrealized_plpc),
                lastday_price=safe_float(position.lastday_price),
                change_today=safe_float(position.change_today),
            )
        except Exception as e:
            logger.error("Error formatting position: %s", str(e))
            raise

    def _format_order(self, order: Order) -> OrderInfo:
        """Format order data.

        Args:
            order: Raw order data

        Returns:
            OrderInfo: Formatted order information
        """
        try:
            return OrderInfo(
                id=str(order.id),
                symbol=str(order.symbol),
                qty=safe_float(order.qty),
                side=str(order.side),
                type=str(order.type),
                time_in_force=str(order.time_in_force),
                status=str(order.status),
                filled_qty=safe_float(order.filled_qty),
                filled_avg_price=safe_float(order.filled_avg_price),
                created_at=order.created_at,
                updated_at=order.updated_at,
            )
        except Exception as e:
            logger.error("Error formatting order: %s", str(e))
            raise
