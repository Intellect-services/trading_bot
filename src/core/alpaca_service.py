import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
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
        self.logger.info("AlpacaService initialized successfully")

    def get_account(self):
        try:
            account = self.client.get_account()
            return {
                "account_id": account.account_number,
                "buying_power": float(account.buying_power),
                "equity": float(account.equity),
                "cash": float(account.cash),
                "status": account.status,
                "last_updated": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"Error fetching account info: {str(e)}")
            raise

    def get_positions(self):
        try:
            positions = self.client.get_all_positions()
            return [
                {
                    "symbol": position.symbol,
                    "quantity": float(position.qty),
                    "market_value": float(position.market_value),
                    "unrealized_pl": float(position.unrealized_pl),
                    "current_price": float(position.current_price),
                }
                for position in positions
            ]
        except Exception as e:
            self.logger.error(f"Error fetching positions: {str(e)}")
            raise

    def get_market_status(self):
        """Get current market status."""
        try:
            clock = self.client.get_clock()
            return {
                "is_open": clock.is_open,
                "next_open": clock.next_open.isoformat() if clock.next_open else None,
                "next_close": clock.next_close.isoformat() if clock.next_close else None,
            }
        except Exception as e:
            self.logger.error(f"Error getting market status: {str(e)}")
            raise

    def create_order(self, symbol, quantity, side, order_type="market"):
        try:
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
            )
            order = self.client.submit_order(order_data)
            return {
                "order_id": order.id,
                "status": order.status,
                "symbol": order.symbol,
                "quantity": float(order.qty),
                "side": order.side,
                "created_at": order.created_at.isoformat(),
            }
        except Exception as e:
            self.logger.error(f"Error creating order: {str(e)}")
            raise

    def cancel_order(self, order_id):
        try:
            self.client.cancel_order_by_id(order_id)
            return {"status": "success", "message": f"Order {order_id} canceled successfully"}
        except Exception as e:
            self.logger.error(f"Error canceling order: {str(e)}")
            raise

    def get_orders(self, status=None):
        try:
            orders = self.client.get_orders(status=status)
            return [
                {
                    "order_id": order.id,
                    "symbol": order.symbol,
                    "quantity": float(order.qty),
                    "side": order.side,
                    "status": order.status,
                    "created_at": order.created_at.isoformat(),
                    "filled_at": order.filled_at.isoformat() if order.filled_at else None,
                    "filled_quantity": float(order.filled_qty) if order.filled_qty else 0,
                    "filled_price": float(order.filled_avg_price) if order.filled_avg_price else 0,
                }
                for order in orders
            ]
        except Exception as e:
            self.logger.error(f"Error fetching orders: {str(e)}")
            raise

    def get_position(self, symbol: str) -> Dict:
        """Get position for a specific symbol."""
        try:
            position = self.client.get_position(symbol)
            self.logger.info(f"Retrieved position for {symbol}")
            return {
                "symbol": position.symbol,
                "quantity": float(position.qty),
                "market_value": float(position.market_value),
                "unrealized_pl": float(position.unrealized_pl),
                "current_price": float(position.current_price),
            }
        except Exception as e:
            self.logger.error(f"Failed to get position for {symbol}: {str(e)}")
            raise

    def get_assets(
        self, status: Optional[str] = None, asset_class: Optional[str] = None
    ) -> List[Dict]:
        """Get all assets with optional filters."""
        try:
            assets = self.client.get_all_assets(status=status, asset_class=asset_class)
            self.logger.info(f"Retrieved {len(assets)} assets")
            return [
                {
                    "symbol": asset.symbol,
                    "name": asset.name,
                    "class": asset.class_,
                    "status": asset.status,
                }
                for asset in assets
            ]
        except Exception as e:
            self.logger.error(f"Failed to get assets: {str(e)}")
            raise

    def get_asset(self, symbol: str) -> Dict:
        """Get a specific asset by symbol."""
        try:
            asset = self.client.get_asset(symbol)
            self.logger.info(f"Retrieved asset info for {symbol}")
            return {
                "symbol": asset.symbol,
                "name": asset.name,
                "class": asset.class_,
                "status": asset.status,
            }
        except Exception as e:
            self.logger.error(f"Failed to get asset info for {symbol}: {str(e)}")
            raise

    def get_calendar(self, start: Optional[str] = None, end: Optional[str] = None) -> List[Dict]:
        """Get market calendar."""
        try:
            calendar = self.client.get_calendar(start=start, end=end)
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
        self, activity_type: Optional[str] = None, date: Optional[str] = None
    ) -> List[Dict]:
        """Get account activities."""
        try:
            activities = self.client.get_account_activities(activity_type=activity_type, date=date)
            self.logger.info(f"Retrieved {len(activities)} account activities")
            return [
                {
                    "activity_type": activity.activity_type,
                    "date": activity.date.isoformat(),
                    "amount": float(activity.amount),
                    "asset_id": activity.asset_id,
                    "symbol": activity.symbol,
                }
                for activity in activities
            ]
        except Exception as e:
            self.logger.error(f"Failed to get account activities: {str(e)}")
            raise

    def get_portfolio_history(
        self,
        period: Optional[str] = None,
        timeframe: Optional[str] = None,
        date_end: Optional[str] = None,
    ) -> Dict:
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
