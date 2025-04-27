"""Data feed module for fetching and processing market data."""

from typing import Dict, List, Any, Optional, Callable
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import threading
import time
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
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.logger = logger

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
                self.logger.info(f"Added symbol {symbol} to data feed")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error adding symbol {symbol}: {str(e)}")
            return False

    def get_historical_data(self, symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
        """Get historical data for a symbol."""
        try:
            # Convert datetime to string format expected by Alpaca
            start_str = start.strftime('%Y-%m-%d')
            end_str = end.strftime('%Y-%m-%d')
            
            # Calculate number of days between start and end
            days = (end - start).days
            if days <= 0:
                days = 1
            
            # Get data from Alpaca
            df = self.client.get_bars(symbol, '1D', limit=days)
            if df.empty:
                self.logger.warning(f"No historical data found for {symbol}")
                return pd.DataFrame()
            
            # Set timestamp as index
            df.index = pd.to_datetime(df.index)
            return df
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {e}")
            return pd.DataFrame()

    def get_latest_data(self, symbol: str) -> pd.DataFrame:
        """Get latest data for a symbol."""
        try:
            # Get last 100 bars
            df = self.client.get_bars(symbol, '1D', limit=100)
            if df.empty:
                self.logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()
            
            # Update stored data
            self.data[symbol] = df
            
            # Calculate indicators
            self._calculate_indicators(symbol)
            
            # Notify callbacks
            for callback in self.callbacks:
                callback(symbol, df)
            
            return df
        except Exception as e:
            self.logger.error(f"Error getting latest data for {symbol}: {e}")
            return pd.DataFrame()

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price for a symbol."""
        try:
            if symbol in self.data and not self.data[symbol].empty:
                return float(self.data[symbol]['close'].iloc[-1])
            return None
        except Exception as e:
            self.logger.error(f"Error getting latest price for {symbol}: {e}")
            return None

    def add_callback(self, callback: Callable[[str, pd.DataFrame], None]) -> None:
        """Add a callback function for data updates.

        Args:
            callback: Function to call when new data is available
        """
        try:
            if callback not in self.callbacks:
                self.callbacks.append(callback)
                self.logger.info("Added callback to data feed")
        except Exception as e:
            self.logger.error(f"Error adding callback: {str(e)}")

    def _calculate_indicators(self, symbol: str) -> None:
        """Calculate technical indicators for a symbol."""
        try:
            if symbol not in self.data or self.data[symbol].empty:
                return
            
            df = self.data[symbol]
            
            # Calculate SMA
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            
            # Calculate RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Ensure RSI values are numeric and handle NaN values
            df['rsi'] = pd.to_numeric(df['rsi'], errors='coerce').fillna(50)
            
            # Convert Series to float for comparison
            df['rsi'] = df['rsi'].astype(float)
            
            # Update stored data
            self.data[symbol] = df
        except Exception as e:
            self.logger.error(f"Error calculating indicators for {symbol}: {e}")

    def start(self) -> None:
        """Start the data feed."""
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._run)
            self._thread.daemon = True
            self._thread.start()
            self.logger.info("Started data feed")

    def stop(self) -> None:
        """Stop the data feed."""
        if self._running:
            self._running = False
            if self._thread:
                self._thread.join()
            self.logger.info("Stopped data feed")

    def _run(self) -> None:
        """Run the data feed loop."""
        while self._running:
            try:
                for symbol in self.symbols:
                    self.get_latest_data(symbol)
                time.sleep(60)  # Update every minute
            except Exception as e:
                self.logger.error(f"Error in data feed loop: {e}")
                time.sleep(60)  # Wait before retrying
