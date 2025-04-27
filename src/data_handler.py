"""Data handler module for fetching and caching market data."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
import json
import os

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.core.alpaca_client import AlpacaClient

logger = setup_logger(__name__)


class DataHandler:
    """Data handler for fetching and caching market data."""

    def __init__(self, config: Config):
        """Initialize data handler.

        Args:
            config: Configuration instance
        """
        self.config = config
        self._client = AlpacaClient(config)
        self._data: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        self._cache_dir = "data/cache"
        os.makedirs(self._cache_dir, exist_ok=True)
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
            cache_data = [{str(k): str(v) if isinstance(v, (pd.Timestamp, datetime)) else v for k, v in d.items()} for d in data]
            with open(cache_path, "w") as f:
                json.dump(cache_data, f)
            logger.info(f"Saved data to cache: {cache_path}")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def get_historical_data(
        self,
        symbol: str,
        days: int = 30,
        timeframe: str = "1Day"
    ) -> pd.DataFrame:
        """Get historical market data.

        Args:
            symbol: Trading symbol
            days: Number of days of historical data
            timeframe: Time frame for the data

        Returns:
            DataFrame containing historical data
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            data = self._client.get_bars(
                symbol=symbol,
                timeframe=timeframe,
                start=start_date,
                end=end_date
            )
            
            if data.empty:
                logger.warning(f"No historical data found for {symbol}")
                return pd.DataFrame()
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def get_latest_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest market data.

        Args:
            symbol: Trading symbol

        Returns:
            Dictionary containing latest data or None if not available
        """
        try:
            data = self._client.get_bars(
                symbol=symbol,
                timeframe="1Min",
                limit=1
            )
            
            if data.empty:
                logger.warning(f"No latest data found for {symbol}")
                return None
            
            return {
                'symbol': symbol,
                'timestamp': data.index[-1],
                'open': data['open'].iloc[-1],
                'high': data['high'].iloc[-1],
                'low': data['low'].iloc[-1],
                'close': data['close'].iloc[-1],
                'volume': data['volume'].iloc[-1]
            }
            
        except Exception as e:
            logger.error(f"Error getting latest data for {symbol}: {str(e)}")
            return None

    def get_account_info(self) -> Dict[str, Any]:
        """Get account information.

        Returns:
            Dictionary containing account information
        """
        try:
            return self._client.get_account()
        except Exception as e:
            logger.error(f"Error getting account information: {str(e)}")
            return {}

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions.

        Returns:
            List of dictionaries containing position information
        """
        try:
            return self._client.get_positions()
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
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
    ) -> Optional[Dict[str, Any]]:
        """Submit a trading order.

        Args:
            symbol: Trading symbol
            qty: Order quantity
            side: Order side ('buy' or 'sell')
            type: Order type ('market', 'limit', or 'stop')
            time_in_force: Time in force ('day' or 'gtc')
            limit_price: Limit price for limit orders
            stop_price: Stop price for stop orders

        Returns:
            Dictionary containing order information or None if failed
        """
        try:
            return self._client.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=type,
                time_in_force=time_in_force,
                limit_price=limit_price,
                stop_price=stop_price
            )
        except Exception as e:
            logger.error(f"Error submitting order for {symbol}: {str(e)}")
            return None
