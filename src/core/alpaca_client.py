"""Alpaca API client module."""

from typing import Dict, List, Any, Optional, Union, cast
import pandas as pd
from datetime import datetime, timedelta
import pytz
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopOrderRequest
from alpaca.trading.enums import OrderSide, OrderType, TimeInForce
from alpaca_trade_api.rest import REST
from alpaca_trade_api.entity import Bar
from alpaca_trade_api.entity_v2 import OrderRequest

from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class AlpacaClient:
    """Client for interacting with Alpaca API."""

    def __init__(self, config: Config) -> None:
        """Initialize Alpaca client."""
        self.config = config
        self._client = REST(
            config.ALPACA_API_KEY,
            config.ALPACA_SECRET_KEY,
            'https://paper-api.alpaca.markets' if config.PAPER_TRADING else 'https://api.alpaca.markets'
        )
        self.logger = logger

    def get_account(self) -> Dict[str, Any]:
        """Get account information."""
        try:
            account = self._client.get_account()
            return {k: getattr(account, k) for k in dir(account) if not k.startswith('_')}
        except Exception as e:
            logger.error(f"Error getting account information: {str(e)}")
            return {}

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get position information for a symbol."""
        try:
            position = self._client.get_position(symbol)
            if not position:
                return None
            return {k: getattr(position, k) for k in dir(position) if not k.startswith('_')}
        except Exception as e:
            logger.error(f"Error getting position for {symbol}: {str(e)}")
            return None

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all positions."""
        try:
            positions = self._client.get_positions()
            return [{k: getattr(pos, k) for k in dir(pos) if not k.startswith('_')} for pos in positions]
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return []

    def get_bars(
        self,
        symbol: str,
        timeframe: str,
        start: str,
        end: str
    ) -> pd.DataFrame:
        """Get historical bars data."""
        try:
            bars = self._client.get_bars(symbol, timeframe, start, end)
            if not bars:
                return pd.DataFrame()
            
            data = []
            for bar in bars:
                bar_dict = {
                    'timestamp': pd.Timestamp(bar.t),
                    'open': float(bar.o),
                    'high': float(bar.h),
                    'low': float(bar.l),
                    'close': float(bar.c),
                    'volume': int(bar.v)
                }
                data.append(bar_dict)
            
            df = pd.DataFrame(data)
            if not df.empty:
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)
            return df
        except Exception as e:
            logger.error(f"Error fetching bars for {symbol}: {str(e)}")
            return pd.DataFrame()

    def get_assets(self) -> List[Dict[str, Any]]:
        """Get list of tradable assets."""
        try:
            assets = self._client.get_assets()
            return [{k: getattr(asset, k) for k in dir(asset) if not k.startswith('_')} for asset in assets]
        except Exception as e:
            logger.error(f"Error getting assets: {str(e)}")
            return []

    def submit_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        type: str,
        time_in_force: str,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Submit a trading order."""
        try:
            order_data: Dict[str, Any] = {
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "type": type,
                "time_in_force": time_in_force
            }

            if type == "limit" and limit_price is not None:
                order_data["limit_price"] = limit_price
                order_request = LimitOrderRequest(**order_data)
            elif type == "stop" and stop_price is not None:
                order_data["stop_price"] = stop_price
                order_request = StopOrderRequest(**order_data)
            else:
                order_request = MarketOrderRequest(**order_data)

            order = self._client.submit_order(order_request)
            return {
                "id": order.id,
                "client_order_id": order.client_order_id,
                "status": order.status
            }
        except Exception as e:
            logger.error(f"Error submitting order: {str(e)}")
            return {}

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order."""
        try:
            self._client.cancel_order(order_id)
            return True
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {str(e)}")
            return False

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order information."""
        try:
            order = self._client.get_order(order_id)
            if not order:
                return None
            return {k: getattr(order, k) for k in dir(order) if not k.startswith('_')}
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {str(e)}")
            return None 