"""Alpaca API client for trading operations."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, cast

import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.models import BarSet
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.models import Order, Position, TradeAccount
from alpaca.trading.requests import MarketOrderRequest

from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class AlpacaClient:
    """Client for interacting with Alpaca API."""

    def __init__(self, config: Config) -> None:
        """Initialize the Alpaca client.

        Args:
            config: Configuration object containing API credentials
        """
        self.config = config
        self.trading_client = TradingClient(
            api_key=config.ALPACA_API_KEY,
            secret_key=config.ALPACA_SECRET_KEY,
            paper=config.PAPER_TRADING if hasattr(config, "PAPER_TRADING") else True,
        )
        self.data_client = StockHistoricalDataClient(
            api_key=config.ALPACA_API_KEY, secret_key=config.ALPACA_SECRET_KEY
        )
        logger.info("Alpaca client initialized")

    def get_account(self) -> Dict[str, Any]:
        """Get the trading account information.

        Returns:
            Dict containing account information
        """
        try:
            account = self.trading_client.get_account()
            if isinstance(account, TradeAccount):
                return {
                    "id": account.id,
                    "status": account.status,
                    "currency": account.currency,
                    "cash": float(account.cash) if account.cash else 0.0,
                    "portfolio_value": (
                        float(account.portfolio_value)
                        if account.portfolio_value
                        else 0.0
                    ),
                    "buying_power": (
                        float(account.buying_power) if account.buying_power else 0.0
                    ),
                    "initial_margin": (
                        float(account.initial_margin) if account.initial_margin else 0.0
                    ),
                    "maintenance_margin": (
                        float(account.maintenance_margin)
                        if account.maintenance_margin
                        else 0.0
                    ),
                    "daytrading_buying_power": (
                        float(account.daytrading_buying_power)
                        if account.daytrading_buying_power
                        else 0.0
                    ),
                    "equity": float(account.equity) if account.equity else 0.0,
                    "last_equity": (
                        float(account.last_equity) if account.last_equity else 0.0
                    ),
                    "multiplier": (
                        float(account.multiplier) if account.multiplier else 0.0
                    ),
                    "shorting_enabled": account.shorting_enabled,
                    "pattern_day_trader": account.pattern_day_trader,
                    "trading_blocked": account.trading_blocked,
                    "transfers_blocked": account.transfers_blocked,
                    "account_blocked": account.account_blocked,
                    "created_at": account.created_at,
                    "trade_suspended_by_user": account.trade_suspended_by_user,
                }
            return {}
        except Exception as e:
            logger.error(f"Error getting account: {e}")
            return {}

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions.

        Returns:
            List of dictionaries containing position information
        """
        try:
            positions = self.trading_client.get_all_positions()
            return [
                {
                    "symbol": pos.symbol,
                    "qty": float(pos.qty),
                    "avg_entry_price": float(pos.avg_entry_price),
                    "market_value": (
                        float(pos.market_value) if pos.market_value else 0.0
                    ),
                    "current_price": (
                        float(pos.current_price) if pos.current_price else 0.0
                    ),
                    "unrealized_pl": (
                        float(pos.unrealized_pl) if pos.unrealized_pl else 0.0
                    ),
                    "unrealized_plpc": (
                        float(pos.unrealized_plpc) if pos.unrealized_plpc else 0.0
                    ),
                    "unrealized_intraday_pl": (
                        float(pos.unrealized_intraday_pl)
                        if pos.unrealized_intraday_pl
                        else 0.0
                    ),
                    "unrealized_intraday_plpc": (
                        float(pos.unrealized_intraday_plpc)
                        if pos.unrealized_intraday_plpc
                        else 0.0
                    ),
                    "side": pos.side,
                }
                for pos in positions
                if isinstance(pos, Position)
            ]
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    def get_historical_bars(
        self, symbol: str, timeframe: str, start: datetime, end: datetime
    ) -> Optional[pd.DataFrame]:
        """Get historical price data.

        Args:
            symbol: Stock symbol
            timeframe: Timeframe for the data (e.g., '1D', '1H')
            start: Start datetime
            end: End datetime

        Returns:
            DataFrame containing historical price data
        """
        try:
            request_params = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame(
                    timeframe, unit="min" if "m" in timeframe else "day"
                ),
                start=start,
                end=end,
            )
            bars = self.data_client.get_stock_bars(request_params)
            if isinstance(bars, BarSet) and hasattr(bars, "df"):
                return bars.df
            return None
        except Exception as e:
            logger.error(f"Error getting historical bars: {e}")
            return None

    def submit_order(
        self,
        symbol: str,
        qty: float,
        side: OrderSide,
        type: str = "market",
        time_in_force: TimeInForce = TimeInForce.DAY,
    ) -> Optional[Dict[str, Any]]:
        """Submit a trading order.

        Args:
            symbol: Stock symbol
            qty: Number of shares
            side: Order side (buy/sell)
            type: Order type
            time_in_force: Time in force for the order

        Returns:
            Dictionary containing order information
        """
        try:
            order_data = MarketOrderRequest(
                symbol=symbol, qty=qty, side=side, time_in_force=time_in_force
            )
            order = self.trading_client.submit_order(order_data)
            if isinstance(order, Order):
                return {
                    "id": order.id,
                    "symbol": order.symbol,
                    "qty": float(str(order.qty)) if order.qty else 0.0,
                    "filled_qty": (
                        float(str(order.filled_qty)) if order.filled_qty else 0.0
                    ),
                    "filled_avg_price": (
                        float(str(order.filled_avg_price))
                        if order.filled_avg_price
                        else 0.0
                    ),
                    "status": order.status,
                    "side": order.side,
                    "type": order.type,
                    "time_in_force": order.time_in_force,
                    "created_at": order.created_at,
                }
            return None
        except Exception as e:
            logger.error(f"Error submitting order: {e}")
            return None
