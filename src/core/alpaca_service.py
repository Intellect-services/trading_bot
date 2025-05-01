"""Alpaca service for trading operations."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from alpaca.data.timeframe import TimeFrame
from alpaca.trading.enums import OrderSide, OrderType, QueryOrderStatus, TimeInForce

from ..utils.logger import setup_logger
from .alpaca_client import (
    AccountInfo,
    AlpacaClient,
    AssetInfo,
    ClockInfo,
    HistoricalData,
    OrderInfo,
    PositionInfo,
)

logger = setup_logger(__name__)


class AlpacaService:
    """Service for interacting with Alpaca API."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Alpaca service.

        Args:
            config: Configuration dictionary containing API credentials
        """
        self.client = AlpacaClient(
            api_key=config["ALPACA_API_KEY"],
            api_secret=config["ALPACA_SECRET_KEY"],
            base_url="https://paper-api.alpaca.markets"
            if config["ALPACA_PAPER"]
            else "https://api.alpaca.markets",
        )
        self.logger = setup_logger(__name__)

    def get_account(self) -> AccountInfo:
        """Get account information.

        Returns:
            AccountInfo: Account information

        Raises:
            Exception: If there is an error getting account information
        """
        try:
            return self.client.get_account()
        except Exception as e:
            self.logger.error("Error getting account: %s", str(e))
            raise

    def get_positions(self) -> List[PositionInfo]:
        """Get all positions.

        Returns:
            List[PositionInfo]: List of positions

        Raises:
            Exception: If there is an error getting positions
        """
        try:
            return self.client.get_positions()
        except Exception as e:
            self.logger.error("Error getting positions: %s", str(e))
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

        Raises:
            Exception: If there is an error getting historical data
        """
        try:
            return self.client.get_historical_data(symbols, timeframe, start, end)
        except Exception as e:
            self.logger.error("Error getting historical data: %s", str(e))
            raise

    def submit_order(
        self,
        symbol: str,
        qty: float,
        side: OrderSide,
        type: OrderType = OrderType.MARKET,
        time_in_force: TimeInForce = TimeInForce.DAY,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> OrderInfo:
        """Submit an order.

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

        Raises:
            Exception: If there is an error submitting the order
        """
        try:
            return self.client.place_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=type,
                time_in_force=time_in_force,
                limit_price=limit_price,
                stop_price=stop_price,
            )
        except Exception as e:
            self.logger.error("Error submitting order: %s", str(e))
            raise

    def get_market_clock(self) -> ClockInfo:
        """Get market clock information.

        Returns:
            ClockInfo: Market clock information

        Raises:
            Exception: If there is an error getting market clock information
        """
        try:
            return self.client.get_market_clock()
        except Exception as e:
            self.logger.error("Error getting market clock: %s", str(e))
            raise

    def get_asset(self, symbol: str) -> Optional[AssetInfo]:
        """Get asset information.

        Args:
            symbol: Symbol to get asset info for

        Returns:
            Optional[AssetInfo]: Asset information if found, None if not found

        Raises:
            Exception: If there is an error getting asset information
        """
        try:
            return self.client.get_asset(symbol)
        except Exception as e:
            self.logger.error("Error getting asset %s: %s", symbol, str(e))
            return None

    def get_orders(
        self, status: Optional[QueryOrderStatus] = None, limit: int = 100
    ) -> List[OrderInfo]:
        """Get orders.

        Args:
            status: Order status to filter by (optional)
            limit: Maximum number of orders to return (default: 100)

        Returns:
            List[OrderInfo]: List of orders

        Raises:
            Exception: If there is an error getting orders
        """
        try:
            return self.client.get_orders(status=status, limit=limit)
        except Exception as e:
            self.logger.error("Error getting orders: %s", str(e))
            raise

    def get_position(self, symbol: str) -> Optional[PositionInfo]:
        """Get position for a symbol.

        Args:
            symbol: Symbol to get position for

        Returns:
            Optional[PositionInfo]: Position information if found, None if not found

        Raises:
            Exception: If there is an error getting position information
        """
        try:
            return self.client.get_position(symbol)
        except Exception as e:
            self.logger.error("Error getting position %s: %s", symbol, str(e))
            return None

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order.

        Args:
            order_id: Order ID to cancel

        Returns:
            bool: True if order was cancelled successfully, False otherwise

        Raises:
            Exception: If there is an error cancelling the order
        """
        try:
            return self.client.cancel_order(order_id)
        except Exception as e:
            self.logger.error("Error cancelling order %s: %s", order_id, str(e))
            return False

    def get_order(self, order_id: str) -> Optional[OrderInfo]:
        """Get order by ID.

        Args:
            order_id: Order ID to get

        Returns:
            Optional[OrderInfo]: Order information if found, None if not found

        Raises:
            Exception: If there is an error getting order information
        """
        try:
            return self.client.get_order(order_id)
        except Exception as e:
            self.logger.error("Error getting order %s: %s", order_id, str(e))
            return None

    def get_market_status(self) -> ClockInfo:
        """Get market status.

        Returns:
            ClockInfo: Market clock information

        Raises:
            Exception: If there is an error getting market status
        """
        try:
            return self.client.get_market_clock()
        except Exception as e:
            self.logger.error("Error getting market status: %s", str(e))
            raise

    def get_portfolio_history(
        self,
        period: str = "1M",
        timeframe: str = "1D",
        extended_hours: bool = False,
    ) -> Dict[str, Any]:
        """Get portfolio history.

        Args:
            period: Time period to get history for (default: 1M)
            timeframe: Time frame for data points (default: 1D)
            extended_hours: Whether to include extended hours (default: False)

        Returns:
            Dict[str, Any]: Portfolio history data

        Raises:
            Exception: If there is an error getting portfolio history
        """
        try:
            # Since Alpaca's Python SDK doesn't provide a direct method for portfolio history,
            # we'll calculate it from account data and position values
            account = self.get_account()
            positions = self.get_positions()
            
            # Calculate total portfolio value
            portfolio_value = float(account.portfolio_value)
            
            # For now, return a simplified version
            return {
                "timestamp": datetime.now().isoformat(),
                "equity": portfolio_value,
                "profit_loss": portfolio_value - float(account.last_equity),
                "profit_loss_pct": (portfolio_value - float(account.last_equity)) / float(account.last_equity) * 100,
                "base_value": float(account.last_equity),
                "timeframe": timeframe,
            }
        except Exception as e:
            self.logger.error("Error getting portfolio history: %s", str(e))
            raise
