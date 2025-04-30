import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, cast
from uuid import UUID

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, QueryOrderStatus, TimeInForce
from alpaca.trading.models import Asset, Calendar, Clock, Order, Position, TradeAccount
from alpaca.trading.requests import GetOrdersRequest, MarketOrderRequest

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class AlpacaService:
    def __init__(self) -> None:
        """Initialize Alpaca service with API credentials from environment variables."""
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("ALPACA_API_SECRET")

        if not self.api_key or not self.secret_key:
            raise ValueError("Alpaca API credentials not found in environment variables")

        self.client = TradingClient(self.api_key, self.secret_key, paper=True)
        self.data_client = StockHistoricalDataClient(self.api_key, self.secret_key)
        self.logger = logger
        self.logger.info("AlpacaService initialized successfully")

    def get_account(self) -> Dict[str, Any]:
        try:
            account = cast(TradeAccount, self.client.get_account())
            return {
                "account_id": account.account_number,
                "buying_power": float(account.buying_power or 0),
                "equity": float(account.equity or 0),
                "cash": float(account.cash or 0),
                "status": account.status,
                "last_updated": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"Error fetching account info: {str(e)}")
            raise

    def get_positions(self) -> List[Dict[str, Any]]:
        try:
            positions = cast(List[Position], self.client.get_all_positions())
            return [
                {
                    "symbol": position.symbol,
                    "quantity": float(position.qty or 0),
                    "market_value": float(position.market_value or 0),
                    "unrealized_pl": float(position.unrealized_pl or 0),
                    "current_price": float(position.current_price or 0),
                }
                for position in positions
            ]
        except Exception as e:
            self.logger.error(f"Error fetching positions: {str(e)}")
            raise

    def get_market_status(self) -> Dict[str, Any]:
        """Get current market status."""
        try:
            clock = cast(Clock, self.client.get_clock())
            return {
                "is_open": clock.is_open,
                "next_open": clock.next_open.isoformat() if clock.next_open else None,
                "next_close": clock.next_close.isoformat() if clock.next_close else None,
            }
        except Exception as e:
            self.logger.error(f"Error getting market status: {str(e)}")
            raise

    def create_order(
        self, symbol: str, quantity: float, side: str, order_type: str = "market"
    ) -> Dict[str, Any]:
        try:
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
            )
            order = cast(Order, self.client.submit_order(order_data))
            return {
                "order_id": order.id,
                "status": order.status,
                "symbol": order.symbol,
                "quantity": float(order.qty or 0),
                "side": order.side,
                "created_at": order.created_at.isoformat(),
            }
        except Exception as e:
            self.logger.error(f"Error creating order: {str(e)}")
            raise

    def cancel_order(self, order_id: str) -> Dict[str, str]:
        try:
            self.client.cancel_order_by_id(order_id)
            return {"status": "success", "message": f"Order {order_id} canceled successfully"}
        except Exception as e:
            self.logger.error(f"Error canceling order: {str(e)}")
            raise

    def get_orders(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            orders = cast(List[Order], self.client.get_orders())
            if status:
                orders = [order for order in orders if order.status == status]
            return [
                {
                    "order_id": order.id,
                    "symbol": order.symbol,
                    "quantity": float(order.qty or 0),
                    "side": order.side,
                    "status": order.status,
                    "created_at": order.created_at.isoformat(),
                    "filled_at": order.filled_at.isoformat() if order.filled_at else None,
                    "filled_quantity": float(order.filled_qty or 0),
                    "filled_price": float(order.filled_avg_price or 0),
                }
                for order in orders
            ]
        except Exception as e:
            self.logger.error(f"Error fetching orders: {str(e)}")
            raise

    def get_position(self, symbol: str) -> Dict[str, Any]:
        """Get position for a specific symbol."""
        try:
            position = cast(Position, self.client.get_open_position(symbol))
            self.logger.info(f"Retrieved position for {symbol}")
            return {
                "symbol": position.symbol,
                "quantity": float(position.qty or 0),
                "market_value": float(position.market_value or 0),
                "unrealized_pl": float(position.unrealized_pl or 0),
                "current_price": float(position.current_price or 0),
            }
        except Exception as e:
            self.logger.error(f"Failed to get position for {symbol}: {str(e)}")
            raise

    def get_assets(
        self, status: Optional[str] = None, asset_class: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all assets with optional filters."""
        try:
            assets = cast(List[Asset], self.client.get_all_assets())
            if status:
                assets = [asset for asset in assets if asset.status == status]
            if asset_class:
                assets = [asset for asset in assets if asset.asset_class == asset_class]
            self.logger.info(f"Retrieved {len(assets)} assets")
            return [
                {
                    "symbol": asset.symbol,
                    "name": asset.name,
                    "class": asset.asset_class,
                    "status": asset.status,
                }
                for asset in assets
            ]
        except Exception as e:
            self.logger.error(f"Failed to get assets: {str(e)}")
            raise

    def get_asset(self, symbol: str) -> Dict[str, Any]:
        """Get a specific asset by symbol."""
        try:
            asset = cast(Asset, self.client.get_asset(symbol))
            self.logger.info(f"Retrieved asset info for {symbol}")
            return {
                "symbol": asset.symbol,
                "name": asset.name,
                "class": asset.asset_class,
                "status": asset.status,
            }
        except Exception as e:
            self.logger.error(f"Failed to get asset info for {symbol}: {str(e)}")
            raise

    def get_calendar(
        self, start: Optional[str] = None, end: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get market calendar."""
        try:
            calendar = cast(List[Calendar], self.client.get_calendar())
            if start:
                start_date = datetime.fromisoformat(start)
                calendar = [entry for entry in calendar if entry.date >= start_date]
            if end:
                end_date = datetime.fromisoformat(end)
                calendar = [entry for entry in calendar if entry.date <= end_date]
            self.logger.info(f"Retrieved market calendar with {len(calendar)} entries")
            return [
                {
                    "date": entry.date.isoformat(),
                    "open": entry.open.isoformat(),
                    "close": entry.close.isoformat(),
                }
                for entry in calendar
            ]
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
        self,
        period: Optional[str] = None,
        timeframe: Optional[str] = None,
        date_end: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get portfolio history."""
        try:
            # Get current account info for base value
            account = self.get_account()
            base_value = float(account["equity"])

            # Get positions for current value
            positions = self.get_positions()
            current_value = sum(float(pos["market_value"]) for pos in positions)

            # Create a simple history with just current values
            now = datetime.now().isoformat()
            return {
                "equity": [base_value, current_value],
                "timestamp": [now, now],
                "profit_loss": [0, current_value - base_value],
                "profit_loss_pct": [
                    0,
                    ((current_value - base_value) / base_value * 100) if base_value > 0 else 0,
                ],
                "base_value": base_value,
            }
        except Exception as e:
            self.logger.error(f"Failed to get portfolio history: {str(e)}")
            raise
