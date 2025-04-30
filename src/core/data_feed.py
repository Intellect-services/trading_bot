"""Data feed module for fetching and processing market data."""

import os
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from alpaca.data.timeframe import TimeFrame
from pandas import DataFrame
from alpaca.data.models import Bar
from alpaca.trading.models import Position

from src.core.alpaca_client import AlpacaClient
from src.utils.logger import setup_logger
from .alpaca_service import AlpacaService
from src.core.alpaca_types import Bar

logger = setup_logger(__name__)


class AlpacaDataFeed:
    """Class for fetching and managing market data from Alpaca."""

    def __init__(self, client: AlpacaClient) -> None:
        """Initialize the data feed with an Alpaca client.

        Args:
            client: An instance of AlpacaClient for making API calls.
        """
        self.client = client
        self.symbols: List[str] = []
        self._data_cache: Dict[str, pd.DataFrame] = {}
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
                self.logger.info("Added symbol %s to data feed", symbol)
                return True
            return False
        except Exception as e:
            self.logger.error("Error adding symbol %s: %s", symbol, str(e))
            return False

    def get_historical_data(
        self,
        symbol: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        timeframe: str = "1Day",
    ) -> DataFrame:
        """Fetch historical market data for a symbol.

        Args:
            symbol: The stock symbol to fetch data for.
            start: Start datetime for the data range.
            end: End datetime for the data range.
            timeframe: The timeframe for the data (e.g., "1Day", "1Hour", "1Min").

        Returns:
            DataFrame containing the historical market data.
        """
        try:
            data = self.client.get_historical_data(symbol, start, end, timeframe)
            if not data or symbol not in data:
                return pd.DataFrame()

            bars = data[symbol]
            df_data = []
            for bar in bars:
                df_data.append(
                    {
                        "timestamp": bar.timestamp,
                        "open": float(bar.open),
                        "high": float(bar.high),
                        "low": float(bar.low),
                        "close": float(bar.close),
                        "volume": int(bar.volume),
                        "trade_count": int(bar.trade_count),
                        "vwap": float(bar.vwap),
                    }
                )

            if not df_data:
                return pd.DataFrame()

            df = pd.DataFrame(df_data)
            df.set_index("timestamp", inplace=True)
            return df

        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def get_latest_data(self, symbol: str) -> pd.DataFrame:
        """Get latest data for a symbol."""
        try:
            # Get last 100 bars
            end = datetime.now()
            start = end - timedelta(days=100)
            data = self.client.get_historical_data(
                symbol=symbol, timeframe="1D", start=start, end=end
            )
            if not data or not data.get("bars"):
                self.logger.warning("No data found for %s", symbol)
                return pd.DataFrame()

            # Convert to DataFrame
            df = pd.DataFrame(data["bars"])
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df.set_index("timestamp", inplace=True)

            # Update stored data
            self._data_cache[symbol] = df

            # Calculate indicators
            self._calculate_indicators(symbol)

            # Notify callbacks
            for callback in self.callbacks:
                callback(symbol, df)

            return df
        except Exception as e:
            self.logger.error("Error getting latest data for %s: %s", symbol, e)
            return pd.DataFrame()

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get the latest price for a symbol.

        Args:
            symbol: The stock symbol to get the price for.

        Returns:
            The latest price as a float, or None if the price cannot be retrieved.
        """
        try:
            df = self.get_historical_data(symbol, timeframe="1Min", start=None, end=None)
            if not df.empty:
                return float(df["close"].iloc[-1])
            return None
        except Exception as e:
            print(f"Error getting latest price for {symbol}: {str(e)}")
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
            if symbol not in self._data_cache or self._data_cache[symbol].empty:
                return

            df = self._data_cache[symbol]

            # Calculate SMA
            df["sma_20"] = df["close"].rolling(window=20).mean()
            df["sma_50"] = df["close"].rolling(window=50).mean()

            # Calculate RSI using pandas clip
            delta = df["close"].diff()
            gain = delta.clip(lower=0).rolling(window=14).mean()
            loss = (-delta.clip(upper=0)).rolling(window=14).mean()
            rs = gain / loss
            df["rsi"] = 100 - (100 / (1 + rs))

            # Ensure RSI values are numeric and handle NaN values
            df["rsi"] = pd.to_numeric(df["rsi"], errors="coerce").fillna(50)

            # Update stored data
            self._data_cache[symbol] = df
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

    def get_market_status(self) -> Dict[str, Any]:
        """Get the current market status."""
        try:
            return self.client.get_clock()
        except Exception as e:
            print(f"Error getting market status: {e}")
            return {"is_open": False, "next_open": None, "next_close": None, "timestamp": None}

    def get_assets(self, status: str = "active") -> List[Dict[str, Any]]:
        """Get all available assets."""
        try:
            return self.client.get_assets(status)
        except Exception as e:
            print(f"Error getting assets: {e}")
            return []

    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """Get current positions.

        Returns:
            A dictionary mapping symbols to position information.
        """
        try:
            positions = self.client.get_positions()
            return {
                position.symbol: {
                    "symbol": position.symbol,
                    "qty": float(position.qty),
                    "market_value": float(position.market_value),
                    "current_price": float(position.current_price),
                    "lastday_price": float(position.lastday_price),
                    "change_today": float(position.change_today),
                    "unrealized_pl": float(position.unrealized_pl),
                    "unrealized_plpc": float(position.unrealized_plpc),
                    "unrealized_intraday_pl": float(position.unrealized_intraday_pl),
                    "unrealized_intraday_plpc": float(position.unrealized_intraday_plpc),
                    "avg_entry_price": float(position.avg_entry_price),
                    "side": position.side,
                    "exchange": position.exchange,
                }
                for position in positions
            }
        except Exception as e:
            print(f"Error getting positions: {str(e)}")
            return {}

    def get_account(self) -> Dict[str, Any]:
        """Get the trading account information."""
        try:
            return self.client.get_account()
        except Exception as e:
            print(f"Error getting account: {e}")
            return {}

    def get_asset(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific asset."""
        try:
            return self.client.get_asset(symbol)
        except Exception as e:
            print(f"Error getting asset: {e}")
            return None

    def get_current_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get current market data for a symbol.

        Args:
            symbol: The stock symbol

        Returns:
            Dictionary containing current market data
        """
        try:
            latest_price = self.get_latest_price(symbol)
            if latest_price is None:
                return {}

            position = self.client.get_position(symbol)

            return {
                "symbol": symbol,
                "price": latest_price,
                "position": position if position else {},
                "timestamp": datetime.now(),
            }
        except Exception as e:
            print(f"Error getting current data for {symbol}: {e}")
            return {}

    def clear_cache(self) -> None:
        """Clear the data cache."""
        self._data_cache.clear()

    def update_cache(self, symbol: str, data: pd.DataFrame) -> None:
        """
        Update the cache with new data for a symbol.

        Args:
            symbol: The stock symbol
            data: DataFrame containing the new data
        """
        if not data.empty:
            self._data_cache[symbol] = data


class MockDataFeed:
    """Mock data feed for testing purposes."""

    def __init__(self) -> None:
        """Initialize the mock data feed."""
        self._data: Dict[str, DataFrame] = {}
        self._positions: Dict[str, Dict[str, Any]] = {}

    def get_historical_data(
        self,
        symbol: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        timeframe: str = "1Day",
    ) -> DataFrame:
        """Get mock historical data.

        Args:
            symbol: The stock symbol.
            start: Start datetime (optional).
            end: End datetime (optional).
            timeframe: The timeframe for the data (ignored in mock).

        Returns:
            DataFrame with mock data.
        """
        if symbol not in self._data:
            # Generate mock data
            dates = pd.date_range(start="2020-01-01", end="2023-12-31", freq="D")
            n = len(dates)
            price = 100.0
            data = []
            for i in range(n):
                price *= 1 + np.random.normal(0, 0.02)
                data.append(
                    {
                        "timestamp": dates[i],
                        "open": price * (1 + np.random.normal(0, 0.005)),
                        "high": price * (1 + np.random.normal(0, 0.01)),
                        "low": price * (1 - np.random.normal(0, 0.01)),
                        "close": price,
                        "volume": int(np.random.normal(1000000, 200000)),
                        "trade_count": int(np.random.normal(5000, 1000)),
                        "vwap": price * (1 + np.random.normal(0, 0.002)),
                    }
                )
            df = pd.DataFrame(data)
            df.set_index("timestamp", inplace=True)
            self._data[symbol] = df

        df = self._data[symbol].copy()
        if start:
            df = df[df.index >= start]
        if end:
            df = df[df.index <= end]
        return df

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get mock latest price.

        Args:
            symbol: The stock symbol.

        Returns:
            The latest mock price.
        """
        df = self.get_historical_data(symbol)
        if not df.empty:
            return float(df["close"].iloc[-1])
        return None

    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """Get mock positions.

        Returns:
            Dictionary of mock positions.
        """
        return self._positions.copy()

    def set_positions(self, positions: Dict[str, Dict[str, Any]]) -> None:
        """Set mock positions for testing.

        Args:
            positions: Dictionary of positions to set.
        """
        self._positions = positions.copy()

    def set_historical_data(self, symbol: str, data: DataFrame) -> None:
        """Set mock historical data for testing.

        Args:
            symbol: The stock symbol.
            data: DataFrame containing the historical data.
        """
        self._data[symbol] = data.copy()
