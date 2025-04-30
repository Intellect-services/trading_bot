"""Data handler module for fetching and caching market data."""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.models import Position

from src.core.alpaca_client import AlpacaClient
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class DataHandler:
    """Data handler for fetching and caching market data."""

    def __init__(self, config: Config):
        """Initialize data handler.

        Args:
            config: Configuration instance
        """
        self.config = config
        self.client = AlpacaClient(
            api_key=config.ALPACA_API_KEY,
            secret_key=config.ALPACA_SECRET_KEY,
            paper=config.ALPACA_PAPER,
        )
        self._data: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        self._cache_dir = "data/cache"
        os.makedirs(self._cache_dir, exist_ok=True)
        self.logger = logger
        logger.info("Data handler initialized")

    def _get_cache_path(self, symbol: str, timeframe: str) -> str:
        """Get cache file path for a symbol and timeframe.

        Args:
            symbol: Trading symbol
            timeframe: Data timeframe

        Returns:
            Cache file path
        """
        return os.path.join(self._cache_dir, f"{symbol}_{timeframe}.json")

    def _load_cache(self, symbol: str, timeframe: str) -> Optional[List[Dict[str, Any]]]:
        """Load cached data for a symbol and timeframe.

        Args:
            symbol: Trading symbol
            timeframe: Data timeframe

        Returns:
            List of cached data points if available, None otherwise
        """
        try:
            cache_path = self._get_cache_path(symbol, timeframe)
            if os.path.exists(cache_path):
                with open(cache_path, "r") as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            return None

    def _save_cache(
        self,
        symbol: str,
        timeframe: str,
        data: List[Dict[str, Any]],
    ) -> None:
        """Save data to cache.

        Args:
            symbol: Trading symbol
            timeframe: Data timeframe
            data: Data to cache
        """
        try:
            cache_path = self._get_cache_path(symbol, timeframe)
            cache_data = [
                {
                    str(k): str(v) if isinstance(v, (pd.Timestamp, datetime)) else v
                    for k, v in d.items()
                }
                for d in data
            ]
            with open(cache_path, "w") as f:
                json.dump(cache_data, f)
            logger.info(f"Saved data to cache: {cache_path}")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def get_historical_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        timeframe: str = "1D",
    ) -> pd.DataFrame:
        """Get historical data for a symbol.

        Args:
            symbol: Trading symbol
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            timeframe: Data timeframe (e.g., "1D" for daily)

        Returns:
            DataFrame with historical data
        """
        try:
            # Convert datetime objects to ISO format strings
            start = (
                (datetime.now() - timedelta(days=30)).isoformat() if not start_date else start_date
            )
            end = datetime.now().isoformat() if not end_date else end_date

            # Get data from Alpaca
            data = self.client.get_historical_data(symbol, start, end, timeframe)
            return data
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {e}")
            return pd.DataFrame()

    def get_latest_data(self, symbol: str) -> pd.DataFrame:
        """Get latest market data.

        Args:
            symbol: Trading symbol

        Returns:
            DataFrame containing latest data
        """
        try:
            end = datetime.now().isoformat()
            start = (datetime.now() - timedelta(minutes=1)).isoformat()
            data = self.client.get_historical_data(symbol, start, end)
            if isinstance(data, pd.DataFrame):
                return data
            return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Error getting latest data: {e}")
            return pd.DataFrame()

    def get_account_info(self) -> Dict[str, Any]:
        """Get account information.

        Returns:
            Dictionary containing account information
        """
        try:
            return self.client.get_account()
        except Exception as e:
            logger.error(f"Error getting account information: {str(e)}")
            return {}

    def get_positions(self) -> List[Position]:
        """Get current positions.

        Returns:
            List of positions
        """
        try:
            positions = self.client.get_all_positions()
            return positions if isinstance(positions, list) else []
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    def submit_order(
        self,
        symbol: str,
        qty: float,
        side: OrderSide,
        time_in_force: TimeInForce = TimeInForce.DAY,
    ) -> Optional[Dict[str, Any]]:
        """Submit a trading order.

        Args:
            symbol: Trading symbol
            qty: Order quantity
            side: Order side (buy/sell)
            time_in_force: Time in force for the order

        Returns:
            Order information if successful, None otherwise
        """
        try:
            order = self.client.submit_order(
                symbol=symbol, qty=qty, side=side, time_in_force=time_in_force
            )
            return order
        except Exception as e:
            logger.error(f"Error submitting order: {e}")
            return None
