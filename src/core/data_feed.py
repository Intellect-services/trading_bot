"""Data feed for market data."""

import logging
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union, cast

import numpy as np
import pandas as pd
from alpaca.data import TimeFrame
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest

from ..utils.logger import setup_logger
from .alpaca_client import (
    AccountInfo,
    AlpacaClient,
    AssetInfo,
    ClockInfo,
    HistoricalData,
    PositionInfo,
)

logger = setup_logger(__name__)


def parse_timeframe(timeframe: str) -> TimeFrame:
    """Parse timeframe string into TimeFrame object.

    Args:
        timeframe: String representation of timeframe (e.g., "1Day", "1Hour", "1Min")

    Returns:
        TimeFrame: Alpaca TimeFrame object

    Raises:
        ValueError: If timeframe string is invalid
    """
    # Extract number and unit from timeframe string
    import re

    match = re.match(r"(\d+)([a-zA-Z]+)", timeframe)
    if not match:
        raise ValueError(f"Invalid timeframe format: {timeframe}")

    amount = int(match.group(1))
    unit = match.group(2).lower()

    # Map unit to TimeFrame
    if unit in ["d", "day", "days"]:
        return TimeFrame(amount, TimeFrame.Day)
    elif unit in ["h", "hour", "hours"]:
        return TimeFrame(amount, TimeFrame.Hour)
    elif unit in ["m", "min", "minute", "minutes"]:
        return TimeFrame(amount, TimeFrame.Minute)
    else:
        raise ValueError(f"Invalid timeframe unit: {unit}")


class DataFeed(ABC):
    """Abstract base class for data feeds."""

    @abstractmethod
    def get_historical_data(
        self,
        symbol: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        timeframe: str = "1Day",
    ) -> pd.DataFrame:
        """Fetch historical market data for a symbol.

        Args:
            symbol: The stock symbol to fetch data for
            start: Start datetime for the data range
            end: End datetime for the data range
            timeframe: The timeframe for the data (e.g., "1Day", "1Hour", "1Min")

        Returns:
            pd.DataFrame: DataFrame containing the historical market data
        """
        pass

    @abstractmethod
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get the latest price for a symbol.

        Args:
            symbol: The stock symbol to get the price for

        Returns:
            Optional[float]: The latest price, or None if unavailable
        """
        pass

    @abstractmethod
    def get_positions(self) -> Dict[str, Any]:
        """Get current positions.

        Returns:
            Dict[str, Any]: Dictionary of positions by symbol
        """
        pass

    @abstractmethod
    def get_market_status(self) -> ClockInfo:
        """Get market clock information.

        Returns:
            ClockInfo: Market clock information
        """
        pass


class AlpacaDataFeed(DataFeed):
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
            bool: True if symbol was added successfully
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
    ) -> pd.DataFrame:
        """Fetch historical market data for a symbol.

        Args:
            symbol: The stock symbol to fetch data for
            start: Start datetime for the data range
            end: End datetime for the data range
            timeframe: The timeframe for the data (e.g., "1Day", "1Hour", "1Min")

        Returns:
            pd.DataFrame: DataFrame containing the historical market data
        """
        try:
            if start is None:
                start = datetime.now() - timedelta(days=30)
            if end is None:
                end = datetime.now()

            data = self.client.get_historical_data(
                symbols=[symbol],
                timeframe=parse_timeframe(timeframe),
                start=start,
                end=end,
            )

            df = pd.DataFrame(
                {
                    "timestamp": data.timestamp,
                    "open": data.open,
                    "high": data.high,
                    "low": data.low,
                    "close": data.close,
                    "volume": data.volume,
                    "trade_count": data.trade_count,
                    "vwap": data.vwap,
                }
            )

            if not df.empty:
                df.set_index("timestamp", inplace=True)
                self._data_cache[symbol] = df
                self._calculate_indicators(symbol)

            return df

        except Exception as e:
            self.logger.error("Error fetching historical data for %s: %s", symbol, str(e))
            return pd.DataFrame()

    def get_latest_data(self, symbol: str) -> pd.DataFrame:
        """Get latest data for a symbol.

        Args:
            symbol: The stock symbol to get data for

        Returns:
            pd.DataFrame: DataFrame containing the latest market data
        """
        try:
            end = datetime.now()
            start = end - timedelta(days=100)
            data = self.client.get_historical_data(
                symbols=[symbol],
                timeframe=TimeFrame(1, TimeFrame.Day),
                start=start,
                end=end,
            )

            df = pd.DataFrame(
                {
                    "timestamp": data.timestamp,
                    "open": data.open,
                    "high": data.high,
                    "low": data.low,
                    "close": data.close,
                    "volume": data.volume,
                    "trade_count": data.trade_count,
                    "vwap": data.vwap,
                }
            )

            if not df.empty:
                df.set_index("timestamp", inplace=True)
                self._data_cache[symbol] = df
                self._calculate_indicators(symbol)

                for callback in self.callbacks:
                    callback(symbol, df)

            return df

        except Exception as e:
            self.logger.error("Error getting latest data for %s: %s", symbol, str(e))
            return pd.DataFrame()

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get the latest price for a symbol.

        Args:
            symbol: The stock symbol to get the price for

        Returns:
            Optional[float]: The latest price, or None if unavailable
        """
        try:
            df = self.get_historical_data(
                symbol,
                timeframe="1Min",
                start=datetime.now() - timedelta(minutes=5),
                end=datetime.now(),
            )
            if not df.empty:
                return float(df["close"].iloc[-1])
            return None
        except Exception as e:
            self.logger.error("Error getting latest price for %s: %s", symbol, str(e))
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
            self.logger.error("Error adding callback: %s", str(e))

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
        """Run the data feed update loop."""
        while self._running:
            try:
                for symbol in self.symbols:
                    self.get_latest_data(symbol)
                time.sleep(60)  # Update every minute
            except Exception as e:
                self.logger.error("Error in data feed loop: %s", str(e))
                time.sleep(5)  # Wait before retrying

    def get_market_status(self) -> ClockInfo:
        """Get market clock information.

        Returns:
            ClockInfo: Market clock information
        """
        try:
            return self.client.get_market_clock()
        except Exception as e:
            self.logger.error("Error getting market status: %s", str(e))
            raise

    def get_assets(self, status: str = "active") -> List[AssetInfo]:
        """Get list of assets.

        Args:
            status: Asset status to filter by (default: active)

        Returns:
            List[AssetInfo]: List of assets
        """
        try:
            assets = []
            for symbol in self.symbols:
                asset = self.client.get_asset(symbol)
                if asset and asset.status == status:
                    assets.append(asset)
            return assets
        except Exception as e:
            self.logger.error("Error getting assets: %s", str(e))
            raise

    def get_positions(self) -> Dict[str, PositionInfo]:
        """Get current positions.

        Returns:
            Dict[str, PositionInfo]: Dictionary of positions by symbol
        """
        try:
            positions = self.client.get_positions()
            return {p.symbol: p for p in positions}
        except Exception as e:
            self.logger.error("Error getting positions: %s", str(e))
            raise

    def get_account(self) -> AccountInfo:
        """Get account information.

        Returns:
            AccountInfo: Account information
        """
        try:
            return self.client.get_account()
        except Exception as e:
            self.logger.error("Error getting account: %s", str(e))
            raise

    def get_asset(self, symbol: str) -> Optional[AssetInfo]:
        """Get asset information.

        Args:
            symbol: Symbol to get asset information for

        Returns:
            Optional[AssetInfo]: Asset information if found
        """
        try:
            return self.client.get_asset(symbol)
        except Exception as e:
            self.logger.error("Error getting asset %s: %s", symbol, str(e))
            return None

    def get_current_data(self, symbol: str) -> Dict[str, Any]:
        """Get current market data for a symbol.

        Args:
            symbol: Symbol to get data for

        Returns:
            Dict[str, Any]: Current market data
        """
        try:
            if symbol in self._data_cache:
                df = self._data_cache[symbol]
                if not df.empty:
                    latest = df.iloc[-1]
                    return {
                        "symbol": symbol,
                        "timestamp": latest.name,
                        "open": float(latest["open"]),
                        "high": float(latest["high"]),
                        "low": float(latest["low"]),
                        "close": float(latest["close"]),
                        "volume": float(latest["volume"]),
                        "trade_count": float(latest["trade_count"]),
                        "vwap": float(latest["vwap"]),
                    }
            return {}
        except Exception as e:
            self.logger.error("Error getting current data for %s: %s", symbol, str(e))
            return {}

    def _calculate_indicators(self, symbol: str) -> None:
        """Calculate technical indicators for a symbol.

        Args:
            symbol: Symbol to calculate indicators for
        """
        try:
            if symbol in self._data_cache:
                df = self._data_cache[symbol]
                if not df.empty:
                    # Calculate SMA
                    df["sma_20"] = df["close"].rolling(window=20).mean()
                    df["sma_50"] = df["close"].rolling(window=50).mean()

                    # Calculate RSI
                    delta = df["close"].astype(float).diff()
                    # Convert to numeric and use numpy for comparisons
                    gain = (delta * np.where(delta > 0, 1, 0)).rolling(window=14).mean()
                    loss = (-delta * np.where(delta < 0, 1, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    df["rsi"] = 100 - (100 / (1 + rs))

                    # Calculate MACD
                    exp1 = df["close"].ewm(span=12, adjust=False).mean()
                    exp2 = df["close"].ewm(span=26, adjust=False).mean()
                    df["macd"] = exp1 - exp2
                    df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        except Exception as e:
            self.logger.error("Error calculating indicators for %s: %s", symbol, str(e))

    def clear_cache(self) -> None:
        """Clear the data cache."""
        self._data_cache.clear()

    def update_cache(self, symbol: str, data: pd.DataFrame) -> None:
        """Update the data cache for a symbol.

        Args:
            symbol: Symbol to update cache for
            data: New data to cache
        """
        try:
            self._data_cache[symbol] = data
            self._calculate_indicators(symbol)
        except Exception as e:
            self.logger.error("Error updating cache for %s: %s", symbol, str(e))


class MockDataFeed(DataFeed):
    """Mock data feed for testing."""

    def __init__(self) -> None:
        """Initialize mock data feed."""
        self.data: Dict[str, pd.DataFrame] = {}
        self.positions: Dict[str, Dict[str, Any]] = {}

    def get_historical_data(
        self,
        symbol: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        timeframe: str = "1Day",
    ) -> pd.DataFrame:
        """Get historical data from mock data.

        Args:
            symbol: Symbol to get data for
            start: Start datetime
            end: End datetime
            timeframe: Timeframe for data

        Returns:
            pd.DataFrame: Historical data
        """
        if symbol not in self.data:
            return pd.DataFrame()

        df = self.data[symbol].copy()

        if start is not None:
            df = df[df.index >= start]
        if end is not None:
            df = df[df.index <= end]

        return df

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price from mock data.

        Args:
            symbol: Symbol to get price for

        Returns:
            Optional[float]: Latest price if available
        """
        if symbol not in self.data:
            return None

        df = self.data[symbol]
        if df.empty:
            return None

        return float(df["close"].iloc[-1])

    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """Get positions from mock data.

        Returns:
            Dict[str, Dict[str, Any]]: Mock positions
        """
        return self.positions.copy()

    def set_positions(self, positions: Dict[str, Dict[str, Any]]) -> None:
        """Set mock positions.

        Args:
            positions: Positions to set
        """
        self.positions = positions.copy()

    def set_historical_data(self, symbol: str, data: pd.DataFrame) -> None:
        """Set historical data for testing.

        Args:
            symbol: Symbol to set data for
            data: Historical data
        """
        self.data[symbol] = data.copy()

    def get_market_status(self) -> ClockInfo:
        """Get mock market status.

        Returns:
            ClockInfo: Mock market status
        """
        return ClockInfo(
            timestamp=datetime.now(),
            is_open=True,
            next_open=datetime.now() + timedelta(days=1),
            next_close=datetime.now() + timedelta(hours=4),
        )
