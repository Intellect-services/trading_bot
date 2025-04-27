"""Data feed module for fetching and processing market data."""

from typing import Dict, List, Any, Optional, Callable
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from src.core.alpaca_client import AlpacaClient
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class DataFeed:
    """Class for fetching and processing market data."""

    def __init__(self, client: AlpacaClient) -> None:
        """Initialize data feed.

        Args:
            client: Alpaca client instance
        """
        self.client = client
        self.symbols: List[str] = []
        self.data: Dict[str, pd.DataFrame] = {}
        self.callbacks: List[Callable[[str, pd.DataFrame], None]] = []

    def add_symbol(self, symbol: str) -> bool:
        """Add a symbol to track.

        Args:
            symbol: Trading symbol to add

        Returns:
            True if symbol was added successfully, False otherwise
        """
        try:
            if symbol not in self.symbols:
                self.symbols.append(symbol)
                logger.info(f"Added symbol {symbol} to data feed")
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding symbol {symbol}: {str(e)}")
            return False

    def get_historical_data(
        self,
        symbol: str,
        timeframe: str = '1Day',
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100
    ) -> pd.DataFrame:
        """Get historical market data.

        Args:
            symbol: Trading symbol
            timeframe: Time frame for the data ('1Min', '1Hour', '1Day')
            start: Start datetime
            end: End datetime
            limit: Maximum number of bars to return

        Returns:
            DataFrame containing historical market data
        """
        try:
            df = self.client.get_bars(symbol, timeframe, start, end, limit)
            if not df.empty:
                self.data[symbol] = df
                self.calculate_indicators(symbol)
            return df
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def calculate_indicators(self, symbol: str) -> None:
        """Calculate technical indicators for a symbol.

        Args:
            symbol: Trading symbol
        """
        try:
            if symbol not in self.data:
                return

            df = self.data[symbol]
            if df.empty:
                return

            # Calculate Simple Moving Average (SMA)
            df['sma_20'] = df['close'].astype(float).rolling(window=20).mean()
            df['sma_50'] = df['close'].astype(float).rolling(window=50).mean()

            # Calculate Relative Strength Index (RSI)
            delta = df['close'].astype(float).diff()
            gain = delta.where(delta > 0, 0.0).astype(float)
            loss = -delta.where(delta < 0, 0.0).astype(float)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            df['rsi'] = 100.0 - (100.0 / (1.0 + rs))

            self.data[symbol] = df
        except Exception as e:
            logger.error(f"Error calculating indicators for {symbol}: {str(e)}")

    def get_latest_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get latest market data for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            DataFrame containing latest market data or None if not available
        """
        try:
            if symbol not in self.data:
                return None

            df = self.data[symbol]
            if df.empty:
                return None

            latest_data = df.iloc[-1:]
            for callback in self.callbacks:
                callback(symbol, latest_data)

            return latest_data
        except Exception as e:
            logger.error(f"Error getting latest data for {symbol}: {str(e)}")
            return None

    def add_callback(self, callback: Callable[[str, pd.DataFrame], None]) -> None:
        """Add a callback function for data updates.

        Args:
            callback: Function to call when new data is available
        """
        try:
            if callback not in self.callbacks:
                self.callbacks.append(callback)
                logger.info("Added callback to data feed")
        except Exception as e:
            logger.error(f"Error adding callback: {str(e)}")
