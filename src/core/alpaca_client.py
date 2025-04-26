"""Alpaca API client module."""

from typing import Dict, List, Any, Optional, Union, cast
from datetime import datetime, timedelta
import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.requests import GetOrdersRequest, GetAssetsRequest, OrderRequest, MarketOrderRequest, LimitOrderRequest, StopOrderRequest
from alpaca.trading.enums import AssetClass, OrderSide, OrderType, TimeInForce
from alpaca.trading.models import TradeAccount, Position, Order

from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class AlpacaClient:
    """Client for interacting with Alpaca API."""

    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        """Initialize Alpaca client with API credentials.
        
        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Whether to use paper trading (default: True)
        """
        self.trading_client = TradingClient(api_key, secret_key, paper=paper)
        self.data_client = StockHistoricalDataClient(api_key, secret_key)
        logger.info("Alpaca client initialized")

    def get_historical_data(
        self,
        symbol: str,
        start: datetime,
        end: Optional[datetime] = None,
        timeframe: str = "1D"
    ) -> List[Dict[str, Any]]:
        """Fetch historical market data.
        
        Args:
            symbol: Stock symbol
            start: Start date
            end: End date (default: current time)
            timeframe: Timeframe for data (default: "1D")
            
        Returns:
            List of historical data points
        """
        try:
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                start=start,
                end=end or datetime.now(),
                timeframe=TimeFrame.Day if timeframe == "1D" else TimeFrame.Hour
            )
            bars = self.data_client.get_stock_bars(request)
            return [bar.dict() for bar in bars[symbol]]
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return []

    def get_account(self) -> Dict[str, Any]:
        """Get account information.
        
        Returns:
            Dictionary containing account details
        """
        try:
            account = cast(TradeAccount, self.trading_client.get_account())
            return {
                "id": str(account.id),
                "cash": float(str(account.cash)),
                "portfolio_value": float(str(account.portfolio_value)),
                "buying_power": float(str(account.buying_power)),
                "initial_margin": float(str(account.initial_margin)),
                "maintenance_margin": float(str(account.maintenance_margin)),
                "daytrading_buying_power": float(str(account.daytrading_buying_power)),
                "last_equity": float(str(account.last_equity)),
                "multiplier": float(str(account.multiplier)),
                "status": str(account.status),
                "trading_blocked": bool(account.trading_blocked),
                "transfers_blocked": bool(account.transfers_blocked),
                "account_blocked": bool(account.account_blocked),
                "created_at": str(account.created_at),
                "trade_suspended_by_user": bool(account.trade_suspended_by_user)
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {}

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions.
        
        Returns:
            List of position dictionaries
        """
        try:
            positions = [cast(Position, pos) for pos in self.trading_client.get_all_positions()]
            return [{
                "symbol": str(pos.symbol),
                "qty": float(str(pos.qty)),
                "avg_entry_price": float(str(pos.avg_entry_price)),
                "market_value": float(str(pos.market_value)),
                "unrealized_pl": float(str(pos.unrealized_pl)),
                "unrealized_plpc": float(str(pos.unrealized_plpc)),
                "current_price": float(str(pos.current_price)),
                "lastday_price": float(str(pos.lastday_price)),
                "change_today": float(str(pos.change_today))
            } for pos in positions]
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    def submit_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        type: str = "market",
        time_in_force: str = "day",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Submit a trading order.
        
        Args:
            symbol: Stock symbol
            qty: Quantity to trade
            side: Order side ("buy" or "sell")
            type: Order type ("market", "limit", or "stop") (default: "market")
            time_in_force: Time in force ("day", "gtc", "opg", "cls", "ioc", "fok") (default: "day")
            limit_price: Limit price for limit orders
            stop_price: Stop price for stop orders
            
        Returns:
            Dictionary containing order details
        """
        try:
            order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
            tif = TimeInForce.DAY
            
            if type.lower() == "market":
                order_request = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=order_side,
                    time_in_force=tif
                )
            elif type.lower() == "limit" and limit_price is not None:
                order_request = cast(MarketOrderRequest, LimitOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=order_side,
                    time_in_force=tif,
                    limit_price=limit_price
                ))
            elif type.lower() == "stop" and stop_price is not None:
                order_request = cast(MarketOrderRequest, StopOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=order_side,
                    time_in_force=tif,
                    stop_price=stop_price
                ))
            else:
                raise ValueError(f"Invalid order type: {type}")
            
            order = cast(Order, self.trading_client.submit_order(order_request))
            return {
                "id": str(order.id),
                "client_order_id": str(order.client_order_id),
                "created_at": str(order.created_at),
                "updated_at": str(order.updated_at),
                "submitted_at": str(order.submitted_at),
                "filled_at": str(order.filled_at),
                "expired_at": str(order.expired_at),
                "canceled_at": str(order.canceled_at),
                "failed_at": str(order.failed_at),
                "replaced_at": str(order.replaced_at),
                "replaced_by": str(order.replaced_by),
                "replaces": str(order.replaces),
                "asset_id": str(order.asset_id),
                "symbol": str(order.symbol),
                "asset_class": str(order.asset_class),
                "qty": float(str(order.qty)),
                "filled_qty": float(str(order.filled_qty)),
                "type": str(order.type),
                "side": str(order.side),
                "time_in_force": str(order.time_in_force),
                "limit_price": float(str(order.limit_price)) if order.limit_price else None,
                "stop_price": float(str(order.stop_price)) if order.stop_price else None,
                "filled_avg_price": float(str(order.filled_avg_price)) if order.filled_avg_price else None,
                "status": str(order.status),
                "extended_hours": bool(order.extended_hours),
                "trail_percent": float(str(order.trail_percent)) if order.trail_percent else None,
                "trail_price": float(str(order.trail_price)) if order.trail_price else None,
                "hwm": float(str(order.hwm)) if order.hwm else None
            }
        except Exception as e:
            logger.error(f"Error submitting order: {e}")
            return {} 