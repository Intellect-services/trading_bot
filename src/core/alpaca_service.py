"""Alpaca service for trading operations."""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, cast
from uuid import UUID

import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import (
    OrderSide,
    QueryOrderStatus,
    TimeInForce,
    OrderStatus,
    Sort,
    AssetStatus,
    AssetClass,
    OrderType,
)
from alpaca.trading.models import (
    Asset,
    Calendar,
    Clock,
    Order,
    Position,
    TradeAccount,
    PortfolioHistory,
)
from alpaca.trading.requests import (
    GetOrdersRequest,
    LimitOrderRequest,
    MarketOrderRequest,
    StopOrderRequest,
    GetAssetsRequest,
    GetCalendarRequest,
)
from alpaca.data.enums import Adjustment
from alpaca.data.models import BarSet

from ..utils.config import get_config
from ..utils.logger import setup_logger
from .alpaca_client import AlpacaClient
from .config import Config

logger = setup_logger(__name__)


class AlpacaService:
    def __init__(self, config: Config) -> None:
        self.client = AlpacaClient(config.alpaca_api_key, config.alpaca_api_secret)

    def get_account(self) -> Dict[str, Any]:
        return self.client.get_account()

    def get_positions(self) -> List[Dict[str, Any]]:
        return self.client.get_positions()

    def get_historical_data(
        self, symbol: str, start: datetime, end: datetime, timeframe: TimeFrame = TimeFrame.Day
    ) -> Dict[str, Any]:
        return self.client.get_historical_data(symbol, start, end, timeframe)

    def submit_order(
        self,
        symbol: str,
        qty: float,
        side: OrderSide,
        type: OrderType = OrderType.MARKET,
        time_in_force: TimeInForce = TimeInForce.DAY,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        return self.client.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=type,
            time_in_force=time_in_force,
            limit_price=limit_price,
            stop_price=stop_price,
        )

    def get_orders(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.client.get_orders(status)

    def get_market_clock(self) -> Dict[str, Any]:
        return self.client.get_market_clock()

    def get_position(self, symbol: str) -> Dict[str, Any]:
        return self.client.get_position(symbol)

    def get_asset(self, symbol: str) -> Dict[str, Any]:
        return self.client.get_asset(symbol)

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        return self.client.cancel_order(order_id)

    def submit_bracket_order(
        self,
        symbol: str,
        qty: float,
        side: OrderSide,
        take_profit_price: float,
        stop_loss_price: float,
        type: OrderType = OrderType.MARKET,
        time_in_force: TimeInForce = TimeInForce.DAY,
        limit_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        return self.client.submit_bracket_order(
            symbol=symbol,
            qty=qty,
            side=side,
            take_profit_price=take_profit_price,
            stop_loss_price=stop_loss_price,
            type=type,
            time_in_force=time_in_force,
            limit_price=limit_price,
        )

    def get_order(self, order_id: str) -> Dict[str, Any]:
        return self.client.get_order(order_id)

    def get_assets(self) -> List[Dict[str, Any]]:
        return self.client.get_assets()

    def get_portfolio_history(
        self, period: str = "1M", timeframe: str = "1D", extended_hours: bool = False
    ) -> Dict[str, Any]:
        account = self.get_account()
        current_value = float(account.get("portfolio_value", 0))

        # Calculate start date based on period
        end_date = datetime.now()
        if period == "1D":
            start_date = end_date - timedelta(days=1)
        elif period == "1W":
            start_date = end_date - timedelta(weeks=1)
        elif period == "1M":
            start_date = end_date - timedelta(days=30)
        elif period == "3M":
            start_date = end_date - timedelta(days=90)
        elif period == "1Y":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)  # Default to 1M

        # Get positions
        positions = self.get_positions()
        symbols = [pos["symbol"] for pos in positions]

        # Initialize result dictionary
        result = {"timestamp": [], "equity": [], "profit_loss": [], "profit_loss_pct": []}

        # If no positions, return empty result with current value
        if not symbols:
            return {
                "timestamp": [end_date],
                "equity": [current_value],
                "profit_loss": [0.0],
                "profit_loss_pct": [0.0],
            }

        # Get historical data for each position
        portfolio_values = []
        for symbol in symbols:
            position = next((pos for pos in positions if pos["symbol"] == symbol), None)
            if position:
                qty = float(position["qty"])
                df = self.get_historical_data(symbol, start_date, end_date)
                if not df.empty:
                    df["value"] = df["close"] * qty
                    portfolio_values.append(df["value"])

        if portfolio_values:
            # Combine all position values
            total_value = pd.concat(portfolio_values, axis=1).sum(axis=1)

            # Calculate metrics
            result["timestamp"] = total_value.index.tolist()
            result["equity"] = total_value.values.tolist()
            result["profit_loss"] = [v - result["equity"][0] for v in result["equity"]]
            result["profit_loss_pct"] = [
                (v - result["equity"][0]) / result["equity"][0] * 100
                if result["equity"][0] != 0
                else 0.0
                for v in result["equity"]
            ]

        return result

    def get_market_status(self) -> Dict[str, Any]:
        """Get market status."""
        try:
            clock = self.client.get_clock()
            return {
                "is_open": clock.is_open,
                "next_open": clock.next_open,
                "next_close": clock.next_close,
                "timestamp": clock.timestamp,
            }
        except Exception as e:
            self.logger.error(f"Error getting market status: {e}")
            return {}

    def get_calendar(
        self, start: Optional[datetime] = None, end: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get market calendar."""
        try:
            request = GetCalendarRequest(start=start, end=end)
            calendar = self.client.get_calendar(request)
            self.logger.info(f"Retrieved market calendar with {len(calendar)} entries")
            return [{"date": day.date, "open": day.open, "close": day.close} for day in calendar]
        except Exception as e:
            self.logger.error(f"Failed to get market calendar: {str(e)}")
            raise

    def get_account_activities(
        self, date: Optional[datetime] = None
    ) -> List[Dict[str, Union[str, float, datetime, UUID, None]]]:
        """Get account activities for a specific date.

        Args:
            date: Optional[datetime] - The date to get activities for. If None, gets today's activities.

        Returns:
            List[Dict[str, Union[str, float, datetime, UUID, None]]]: List of activity dictionaries containing trade information
        """
        request_params = GetOrdersRequest(
            status=QueryOrderStatus.ALL,
            nested=True,
            limit=500,
            after=date.replace(hour=0, minute=0, second=0, microsecond=0) if date else None,
            until=date.replace(hour=23, minute=59, second=59, microsecond=999999) if date else None,
        )

        orders = self.client.get_orders(filter=request_params)
        orders = cast(List[Order], orders)  # Cast the Union type to List[Order]
        logger.info(f"Retrieved {len(orders)} orders")

        # Sort orders by timestamp in descending order
        orders.sort(key=lambda x: x.created_at if x.created_at else datetime.min, reverse=True)

        activities = []
        for order in orders:
            filled_qty = float(order.filled_qty) if order.filled_qty is not None else 0.0
            if filled_qty > 0:
                activity = {
                    "timestamp": order.filled_at,
                    "symbol": order.symbol,
                    "side": order.side,
                    "qty": filled_qty,
                    "price": order.filled_avg_price if order.filled_avg_price is not None else 0.0,
                    "order_id": order.id,
                    "status": order.status,
                }
                activities.append(activity)

        logger.info(f"Converted {len(activities)} orders to activities")
        return activities

    def get_portfolio_history(
        self, period: str = "1M", timeframe: str = "1D", extended_hours: bool = False
    ) -> Dict[str, Any]:
        """Get portfolio history."""
        try:
            timeframe_obj = TimeFrame(1, timeframe.lower().replace("d", "Day").replace("m", "Min"))
            history = self.client.get_portfolio_history(
                timeframe=timeframe_obj, period=period, extended_hours=extended_hours
            )
            return {
                "timestamp": history.timestamp,
                "equity": history.equity,
                "profit_loss": history.profit_loss,
                "profit_loss_pct": history.profit_loss_pct,
                "base_value": history.base_value,
            }
        except Exception as e:
            self.logger.error(f"Error getting portfolio history: {e}")
            return {}

    def get_historical_data(
        self, symbol: str, start: datetime, end: datetime, timeframe: TimeFrame = TimeFrame.Day
    ) -> Dict[str, Any]:
        """Get historical data for a specific symbol."""
        try:
            request = StockBarsRequest(
                symbol_or_symbols=symbol, timeframe=timeframe, start=start, end=end
            )
            bars = self.client.get_stock_bars(request)
            return bars.dict() if bars else {}
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {e}")
            return {}
