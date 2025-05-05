"""Data handler for trading operations."""

from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from src.core.alpaca_client import AlpacaClient
from src.core.alpaca_types import Asset as AssetProtocol
from src.core.alpaca_types import BarSet as BarSetProtocol
from src.core.alpaca_types import Clock as ClockProtocol
from src.core.alpaca_types import Order as OrderProtocol
from src.core.alpaca_types import OrderSideEnum, OrderTypeEnum
from src.core.alpaca_types import Position as PositionProtocol
from src.core.alpaca_types import TimeInForceEnum
from src.core.alpaca_types import TradeAccount as TradeAccountProtocol
from src.core.data_feed import DataFeed
from src.core.risk_manager import RiskManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class DataHandler:
    """Data handler for trading operations."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        symbols: List[str],
        risk_manager: RiskManager,
    ) -> None:
        """Initialize data handler.

        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            symbols: List of symbols to trade
            risk_manager: Risk manager instance
        """
        self.alpaca_client = AlpacaClient(api_key, api_secret, paper=True)
        self.data_feed = DataFeed(api_key, api_secret, symbols)
        self.risk_manager = risk_manager
        self.symbols = symbols

    def get_account(self) -> TradeAccountProtocol:
        """Get account information.

        Returns:
            TradeAccountProtocol: Account information
        """
        return self.alpaca_client.get_account()

    def get_positions(self) -> List[PositionProtocol]:
        """Get all positions.

        Returns:
            List[PositionProtocol]: List of positions
        """
        return self.alpaca_client.get_all_positions()

    def get_open_position(self, symbol: str) -> PositionProtocol:
        """Get open position.

        Args:
            symbol: Symbol to get position for

        Returns:
            PositionProtocol: Position information
        """
        return self.alpaca_client.get_open_position(symbol)

    def get_asset(self, symbol: str) -> AssetProtocol:
        """Get asset information.

        Args:
            symbol: Symbol to get asset for

        Returns:
            AssetProtocol: Asset information
        """
        return self.alpaca_client.get_asset(symbol)

    def get_clock(self) -> ClockProtocol:
        """Get market clock information.

        Returns:
            ClockProtocol: Market clock information
        """
        return self.alpaca_client.get_clock()

    def get_bars(
        self,
        symbols: List[str],
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> BarSetProtocol:
        """Get historical market data.

        Args:
            symbols: List of symbols to get data for
            timeframe: Timeframe for data
            start: Start time
            end: End time

        Returns:
            BarSetProtocol: Historical market data
        """
        return self.alpaca_client.get_bars(symbols, timeframe, start, end)

    def place_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        type: str = "market",
        time_in_force: str = "day",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> OrderProtocol:
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
            OrderProtocol: Order information
        """
        return self.alpaca_client.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=type,
            time_in_force=time_in_force,
            limit_price=limit_price,
            stop_price=stop_price,
        )

    def get_orders(self, status: Optional[str] = None) -> List[OrderProtocol]:
        """Get orders.

        Args:
            status: Order status to filter by

        Returns:
            List[OrderProtocol]: List of orders
        """
        return self.alpaca_client.get_orders(status=status)

    def get_order_by_id(self, order_id: str) -> OrderProtocol:
        """Get order by ID.

        Args:
            order_id: ID of order to get

        Returns:
            OrderProtocol: Order information
        """
        return self.alpaca_client.get_order_by_id(order_id)

    def cancel_order_by_id(self, order_id: str) -> None:
        """Cancel an order.

        Args:
            order_id: ID of order to cancel
        """
        self.alpaca_client.cancel_order_by_id(order_id)
