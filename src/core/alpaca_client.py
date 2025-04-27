"""Alpaca API client module."""

from typing import Dict, List, Any, Optional, Union, cast
import pandas as pd
from datetime import datetime, timedelta
import pytz
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopOrderRequest
from alpaca.trading.models import TradeAccount, Position, Order
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.models import Bar

from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class AlpacaClient:
    """Client for interacting with Alpaca API."""

    def __init__(self, config: Config) -> None:
        """Initialize Alpaca client."""
        self.config = config
        self._client = TradingClient(
            config.ALPACA_API_KEY,
            config.ALPACA_SECRET_KEY,
            'https://paper-api.alpaca.markets' if config.PAPER_TRADING else 'https://api.alpaca.markets'
        )
        self._data_client = StockHistoricalDataClient(
            config.ALPACA_API_KEY,
            config.ALPACA_SECRET_KEY
        )
        self.logger = logger

    def get_account(self) -> Dict[str, Any]:
        """Get account information."""
        try:
            account = cast(TradeAccount, self._client.get_account())
            return {
                'account_number': str(account.account_number),
                'cash': float(account.cash) if account.cash is not None else 0.0,
                'buying_power': float(account.buying_power) if account.buying_power is not None else 0.0,
                'equity': float(account.equity) if account.equity is not None else 0.0,
                'last_equity': float(account.last_equity) if account.last_equity is not None else 0.0,
                'created_at': account.created_at.isoformat() if account.created_at is not None else '',
                'currency': str(account.currency),
                'daytrade_count': int(account.daytrade_count) if account.daytrade_count is not None else 0,
                'initial_margin': float(account.initial_margin) if account.initial_margin is not None else 0.0,
                'maintenance_margin': float(account.maintenance_margin) if account.maintenance_margin is not None else 0.0,
                'pattern_day_trader': bool(account.pattern_day_trader),
                'portfolio_value': float(account.portfolio_value) if account.portfolio_value is not None else 0.0,
                'regt_buying_power': float(account.regt_buying_power) if account.regt_buying_power is not None else 0.0,
                'shorting_enabled': bool(account.shorting_enabled),
                'status': str(account.status),
                'trading_blocked': bool(account.trading_blocked),
                'transfers_blocked': bool(account.transfers_blocked),
                'account_blocked': bool(account.account_blocked)
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {}

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get position for a symbol."""
        try:
            position = cast(Position, self._client.get_open_position(symbol))
            if position is None:
                return None
            return {
                'symbol': str(position.symbol),
                'qty': float(position.qty) if position.qty is not None else 0.0,
                'avg_entry_price': float(position.avg_entry_price) if position.avg_entry_price is not None else 0.0,
                'current_price': float(position.current_price) if position.current_price is not None else 0.0,
                'market_value': float(position.market_value) if position.market_value is not None else 0.0,
                'unrealized_pl': float(position.unrealized_pl) if position.unrealized_pl is not None else 0.0,
                'unrealized_plpc': float(position.unrealized_plpc) if position.unrealized_plpc is not None else 0.0,
                'side': str(position.side)
            }
        except Exception as e:
            logger.error(f"Error getting position for {symbol}: {e}")
            return None

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all positions."""
        try:
            positions = cast(List[Position], self._client.get_all_positions())
            return [{
                'symbol': str(p.symbol),
                'qty': float(p.qty) if p.qty is not None else 0.0,
                'avg_entry_price': float(p.avg_entry_price) if p.avg_entry_price is not None else 0.0,
                'current_price': float(p.current_price) if p.current_price is not None else 0.0,
                'market_value': float(p.market_value) if p.market_value is not None else 0.0,
                'unrealized_pl': float(p.unrealized_pl) if p.unrealized_pl is not None else 0.0,
                'unrealized_plpc': float(p.unrealized_plpc) if p.unrealized_plpc is not None else 0.0,
                'side': str(p.side)
            } for p in positions]
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    def get_bars(self, symbol: str, timeframe: str = '1D', limit: int = 100) -> pd.DataFrame:
        """Get historical bars for a symbol."""
        try:
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day if timeframe == '1D' else TimeFrame.Hour,
                limit=limit
            )
            bars = self._data_client.get_stock_bars(request)
            if not bars:
                return pd.DataFrame()
            
            df = pd.DataFrame([{
                'timestamp': b.timestamp,
                'open': float(b.open) if b.open is not None else 0.0,
                'high': float(b.high) if b.high is not None else 0.0,
                'low': float(b.low) if b.low is not None else 0.0,
                'close': float(b.close) if b.close is not None else 0.0,
                'volume': int(b.volume) if b.volume is not None else 0
            } for b in cast(List[Bar], bars)])
            
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            return df
        except Exception as e:
            logger.error(f"Error getting bars for {symbol}: {e}")
            return pd.DataFrame()

    def get_assets(self) -> List[Dict[str, Any]]:
        """Get list of tradable assets."""
        try:
            assets = self._client.get_all_assets()
            return [{k: getattr(asset, k) for k in dir(asset) if not k.startswith('_')} for asset in assets]
        except Exception as e:
            logger.error(f"Error getting assets: {e}")
            return []

    def submit_order(self, symbol: str, qty: float, side: str, type: str = 'market',
                    time_in_force: str = 'day', limit_price: Optional[float] = None,
                    stop_price: Optional[float] = None) -> Dict[str, Any]:
        """Submit an order."""
        try:
            order_data: Union[MarketOrderRequest, LimitOrderRequest, StopOrderRequest]
            if type == 'market':
                order_data = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    time_in_force=time_in_force
                )
            elif type == 'limit':
                if limit_price is None:
                    raise ValueError("Limit price required for limit orders")
                order_data = LimitOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    time_in_force=time_in_force,
                    limit_price=limit_price
                )
            elif type == 'stop':
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
                raise ValueError(f"Invalid order type: {type}")

            order = cast(Order, self._client.submit_order(order_data))
            return {
                'id': str(order.id),
                'symbol': str(order.symbol),
                'qty': float(order.qty) if order.qty is not None else 0.0,
                'filled_qty': float(order.filled_qty) if order.filled_qty is not None else 0.0,
                'type': str(order.type),
                'side': str(order.side),
                'time_in_force': str(order.time_in_force),
                'status': str(order.status),
                'limit_price': float(order.limit_price) if order.limit_price is not None else None,
                'stop_price': float(order.stop_price) if order.stop_price is not None else None,
                'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price is not None else None,
                'created_at': order.created_at.isoformat() if order.created_at is not None else ''
            }
        except Exception as e:
            logger.error(f"Error submitting order: {e}")
            return {}

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order."""
        try:
            self._client.cancel_order_by_id(order_id)
            return True
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order information."""
        try:
            order = cast(Order, self._client.get_order_by_id(order_id))
            if not order:
                return None
            return {
                'id': str(order.id),
                'symbol': str(order.symbol),
                'qty': float(order.qty) if order.qty is not None else 0.0,
                'filled_qty': float(order.filled_qty) if order.filled_qty is not None else 0.0,
                'type': str(order.type),
                'side': str(order.side),
                'time_in_force': str(order.time_in_force),
                'status': str(order.status),
                'limit_price': float(order.limit_price) if order.limit_price is not None else None,
                'stop_price': float(order.stop_price) if order.stop_price is not None else None,
                'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price is not None else None,
                'created_at': order.created_at.isoformat() if order.created_at is not None else ''
            }
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return None 