"""Data feed for market data."""

import logging
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union

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
                timeframe=TimeFrame(timeframe),
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
                timeframe=TimeFrame.Day,
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
            symbol: Symbol to get asset info for

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
            df = self._data_cache.get(symbol)
            if df is None or df.empty:
                return {}

            latest = df.iloc[-1]
            return {
                "timestamp": latest.name,
                "open": float(latest["open"]),
                "high": float(latest["high"]),
                "low": float(latest["low"]),
                "close": float(latest["close"]),
                "volume": int(latest["volume"]),
                "sma_20": float(latest.get("sma_20", 0)),
                "sma_50": float(latest.get("sma_50", 0)),
            }
        except Exception as e:
            self.logger.error("Error getting current data for %s: %s", symbol, str(e))
            return {}

    def _calculate_indicators(self, symbol: str) -> None:
        """Calculate technical indicators for a symbol.

        Args:
            symbol: Symbol to calculate indicators for
        """
        try:
            if symbol not in self._data_cache or self._data_cache[symbol].empty:
                return

            df = self._data_cache[symbol]
            df["sma_20"] = df["close"].rolling(window=20).mean()
            df["sma_50"] = df["close"].rolling(window=50).mean()
            self._data_cache[symbol] = df

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
        self._data_cache[symbol] = data
        self._calculate_indicators(symbol)


class MockDataFeed(DataFeed):
    """Mock data feed for testing purposes."""

    def __init__(self) -> None:
        """Initialize the mock data feed."""
        self._data: Dict[str, pd.DataFrame] = {}
        self._positions: Dict[str, Dict[str, Any]] = {}

    def get_historical_data(
        self,
        symbol: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        timeframe: str = "1Day",
    ) -> pd.DataFrame:
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

    def set_historical_data(self, symbol: str, data: pd.DataFrame) -> None:
        """Set mock historical data for testing.

        Args:
            symbol: The stock symbol.
            data: DataFrame containing the historical data.
        """
        self._data[symbol] = data.copy()
