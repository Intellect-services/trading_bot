"""Alpaca API client for trading operations."""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.models import Order, Position

from src.utils.config import get_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class AlpacaClient:
    """Client for interacting with Alpaca API."""

    def __init__(self) -> None:
        """Initialize Alpaca client with API credentials."""
        self.api_key = get_config('API_KEY')
        self.secret_key = get_config('SECRET_KEY')
        self.paper = get_config('PAPER', True)
        
        self.trading_client: Optional[TradingClient] = None
        self.historical_client: Optional[StockHistoricalDataClient] = None
        
        self._initialize_clients()

    def _initialize_clients(self) -> None:
        """Initialize Alpaca API clients."""
        try:
            self.trading_client = TradingClient(
                self.api_key,
                self.secret_key,
                paper=self.paper
            )
            self.historical_client = StockHistoricalDataClient(
                self.api_key,
                self.secret_key
            )
            logger.info("Alpaca clients initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Alpaca clients: {e}")
            raise

    def get_account(self) -> Dict[str, Any]:
        """
        Get account information.

        Returns:
            Dictionary containing account information.
        """
        if self.trading_client is None:
            raise RuntimeError("Trading client not initialized")
        return self.trading_client.get_account().dict()

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get position information for a symbol.

        Args:
            symbol: Trading symbol.

        Returns:
            Dictionary containing position information or None if no position.
        """
        if self.trading_client is None:
            raise RuntimeError("Trading client not initialized")
        try:
            position = self.trading_client.get_open_position(symbol)
            return position.dict()
        except Exception:
            return None

    def get_all_positions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all open positions.

        Returns:
            Dictionary of positions keyed by symbol.
        """
        if self.trading_client is None:
            raise RuntimeError("Trading client not initialized")
        positions = self.trading_client.get_all_positions()
        return {pos.symbol: pos.dict() for pos in positions}

    def get_historical_data(
        self,
        symbol: str,
        timeframe: str = "1D",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Get historical price data.

        Args:
            symbol: Trading symbol.
            timeframe: Timeframe for the data.
            start: Start date.
            end: End date.
            limit: Maximum number of bars to return.

        Returns:
            DataFrame containing historical data.
        """
        if self.historical_client is None:
            raise RuntimeError("Historical client not initialized")

        if start is None:
            start = datetime.now() - timedelta(days=30)
        if end is None:
            end = datetime.now()

        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame(timeframe),
            start=start,
            end=end,
            limit=limit
        )

        bars = self.historical_client.get_stock_bars(request)
        if isinstance(bars, dict):
            return bars[symbol].df
        return bars.df

    def get_assets(self) -> List[Dict[str, Any]]:
        """
        Get all available assets.

        Returns:
            List of asset dictionaries.
        """
        if self.trading_client is None:
            raise RuntimeError("Trading client not initialized")
        assets = self.trading_client.get_all_assets()
        return [asset.dict() for asset in assets]

    def submit_order(
        self,
        symbol: str,
        qty: float,
        side: OrderSide,
        order_type: str = "market",
        time_in_force: TimeInForce = TimeInForce.DAY,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Submit an order.

        Args:
            symbol: Trading symbol.
            qty: Quantity to trade.
            side: Order side (buy/sell).
            order_type: Type of order (market/limit/stop).
            time_in_force: Time in force for the order.
            limit_price: Limit price for limit orders.
            stop_price: Stop price for stop orders.

        Returns:
            Dictionary containing order information.
        """
        if self.trading_client is None:
            raise RuntimeError("Trading client not initialized")

        order_data: Union[MarketOrderRequest, LimitOrderRequest, StopOrderRequest]
        
        if order_type == "market":
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=side,
                time_in_force=time_in_force
            )
        elif order_type == "limit":
            if limit_price is None:
                raise ValueError("Limit price required for limit orders")
            order_data = LimitOrderRequest(
                symbol=symbol,
                qty=qty,
                side=side,
                time_in_force=time_in_force,
                limit_price=limit_price
            )
        elif order_type == "stop":
            if stop_price is None:
                raise ValueError("Stop price required for stop orders")
            order_data = StopOrderRequest(
                symbol=symbol,
                qty=qty,
                side=side,
                time_in_force=time_in_force,
                stop_price=stop_price
            )
        else:
            raise ValueError(f"Invalid order type: {order_type}")

        order = self.trading_client.submit_order(order_data)
        return {
            "id": order.id,
            "symbol": order.symbol,
            "qty": order.qty,
            "side": order.side,
            "type": order.type,
            "time_in_force": order.time_in_force,
            "status": order.status,
            "filled_at": order.filled_at,
            "filled_qty": order.filled_qty,
            "filled_avg_price": order.filled_avg_price
        }

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: ID of the order to cancel.

        Returns:
            True if order was cancelled successfully.
        """
        if self.trading_client is None:
            raise RuntimeError("Trading client not initialized")
        try:
            self.trading_client.cancel_order_by_id(order_id)
            return True
        except Exception:
            return False

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get order information.

        Args:
            order_id: ID of the order.

        Returns:
            Dictionary containing order information or None if not found.
        """
        if self.trading_client is None:
            raise RuntimeError("Trading client not initialized")
        try:
            order = self.trading_client.get_order_by_id(order_id)
            return order.dict()
        except Exception:
            return None 