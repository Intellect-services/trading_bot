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
        self._client: Optional[AlpacaClient] = None
        self._data: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        self._cache_dir = "data/cache"
        os.makedirs(self._cache_dir, exist_ok=True)
        logger.info("Data handler initialized")

    @property
    def client(self) -> AlpacaClient:
        """Get the Alpaca client instance.

        Returns:
            AlpacaClient instance
        """
        if self._client is None:
            self._client = AlpacaClient(
                api_key=self.config.ALPACA_API_KEY,
                secret_key=self.config.ALPACA_SECRET_KEY
            )
        return self._client

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
        symbol: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        timeframe: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get historical market data.

        Args:
            symbol: Trading symbol
            start: Start date
            end: End date
            timeframe: Timeframe for data

        Returns:
            List of market data dictionaries
        """
        try:
            symbol = symbol or self.config.DEFAULT_SYMBOL
            timeframe = timeframe or self.config.DEFAULT_TIMEFRAME
            end = end or datetime.now()
            start = start or (end - timedelta(days=30))
            
            cache_file = os.path.join(self._cache_dir, f"{symbol}_{timeframe}_{start.date()}_{end.date()}.json")
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} records from cache for {symbol}")
                    return data
                    
            data = self.client.get_historical_data(symbol, start, end, timeframe)
            self._save_cache(symbol, timeframe, data)
            logger.info(f"Fetched {len(data)} records for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error getting historical data: {str(e)}")
            return []

    def get_latest_data(
        self,
        symbol: str,
        timeframe: str = "1Min",
    ) -> Optional[pd.DataFrame]:
        """Get latest market data.

        Args:
            symbol: Trading symbol
            timeframe: Data timeframe

        Returns:
            DataFrame with latest data if successful, None otherwise
        """
        try:
            end = datetime.now()
            start = end - timedelta(minutes=1)
            data = self.get_historical_data(
                symbol=symbol,
                start=start,
                end=end,
                timeframe=timeframe,
            )
            if data is not None and not data:
                return pd.DataFrame(data)
            return None

        except Exception as e:
            logger.error(f"Error getting latest data: {e}")
            return None
