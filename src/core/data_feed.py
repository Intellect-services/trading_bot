"""Data feed module for fetching and processing market data."""

from typing import Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
import logging
import pandas as pd
import numpy as np
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.models import BarSet

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.utils.alpaca_client import AlpacaClient

logger = setup_logger(__name__)

class DataFeed:
    """Data feed for fetching and processing market data."""

    def __init__(self, config: Config, client: Optional[AlpacaClient] = None) -> None:
        """Initialize the data feed.

        Args:
            config: Configuration object
            client: Optional Alpaca client instance
        """
        self.config = config
        self.client = client or AlpacaClient(config)
        self.data_client = StockHistoricalDataClient(
            api_key=config.ALPACA_API_KEY,
            secret_key=config.ALPACA_SECRET_KEY
        )
        self.symbols: List[str] = []
        self.timeframe = TimeFrame.Day
        self.callbacks: List[Callable[[pd.DataFrame], None]] = []
        self.data_cache: Dict[str, pd.DataFrame] = {}
        logger.info("Data feed initialized")

    def add_symbol(self, symbol: str) -> None:
        """Add a symbol to track.

        Args:
            symbol: Stock symbol to track
        """
        if symbol not in self.data_cache:
            self.data_cache[symbol] = pd.DataFrame()
            logger.info(f"Added symbol {symbol} to track")

    def remove_symbol(self, symbol: str) -> None:
        """Remove a symbol from the data feed.

        Args:
            symbol (str): Trading symbol to remove
        """
        if symbol in self.symbols:
            self.symbols.remove(symbol)
            if symbol in self.data_cache:
                del self.data_cache[symbol]
            logger.info("Removed symbol from data feed: %s", symbol)

    def set_timeframe(self, timeframe: str) -> None:
        """Set the data timeframe.

        Args:
            timeframe (str): Timeframe string (e.g., '1D', '1H', '5Min')
        """
        timeframe_map = {
            '1D': TimeFrame.Day,
            '1H': TimeFrame.Hour,
            '5Min': TimeFrame.Minute,
            '1Min': TimeFrame.Minute
        }
        if timeframe in timeframe_map:
            self.timeframe = timeframe_map[timeframe]
            logger.info("Set timeframe to: %s", timeframe)
        else:
            raise ValueError(f"Unsupported timeframe: {timeframe}")

    def get_historical_data(
        self,
        symbol: str,
        timeframe: str = '1D',
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100
    ) -> Optional[pd.DataFrame]:
        """Get historical price data.

        Args:
            symbol: Stock symbol
            timeframe: Timeframe for the data (e.g., '1D', '1H')
            start: Start datetime (default: 100 days ago)
            end: End datetime (default: now)
            limit: Maximum number of bars to retrieve

        Returns:
            DataFrame containing historical price data
        """
        try:
            if start is None:
                start = datetime.now() - timedelta(days=100)
            if end is None:
                end = datetime.now()

            request_params = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame(timeframe, unit='min' if 'm' in timeframe else 'day'),
                start=start,
                end=end,
                limit=limit
            )
            bars = self.data_client.get_stock_bars(request_params)
            if isinstance(bars, BarSet) and hasattr(bars, 'df'):
                return bars.df
            return None
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return None

    def get_latest_data(
        self,
        symbol: str,
        timeframe: str = '1D',
        limit: int = 1
    ) -> Optional[pd.DataFrame]:
        """Get the latest price data.

        Args:
            symbol: Stock symbol
            timeframe: Timeframe for the data
            limit: Number of latest bars to retrieve

        Returns:
            DataFrame containing the latest price data
        """
        try:
            end = datetime.now()
            start = end - timedelta(days=limit)
            return self.get_historical_data(symbol, timeframe, start, end, limit)
        except Exception as e:
            logger.error(f"Error getting latest data: {e}")
            return None

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators.

        Args:
            data: DataFrame containing price data

        Returns:
            DataFrame with added technical indicators
        """
        try:
            df = data.copy()
            # Simple Moving Average
            df['SMA_20'] = df['close'].rolling(window=20).mean()
            # Relative Strength Index
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            return df
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return data

    def add_callback(self, callback: Callable[[pd.DataFrame], None]) -> None:
        """Add a callback function for real-time data updates.

        Args:
            callback: Function to call when new data is available
        """
        self.callbacks.append(callback)
        logger.info("Added data callback")

    def remove_callback(self, callback: Callable[[pd.DataFrame], None]) -> None:
        """Remove a callback function.

        Args:
            callback: Function to remove
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            logger.info("Removed data callback")

    def _notify_callbacks(self, data: pd.DataFrame) -> None:
        """Notify all callbacks with new data.

        Args:
            data (pd.DataFrame): New market data
        """
        for callback in self.callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error("Error in callback: %s", str(e)) 