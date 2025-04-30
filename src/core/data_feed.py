"""Data feed module for fetching and processing market data."""

import threading
import time
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

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
                self.logger.info("Added symbol %s to data feed", symbol)
                return True
            return False
        except Exception as e:
            self.logger.error("Error adding symbol %s: %s", symbol, str(e))
            return False

    def get_historical_data(self, symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
        """Get historical data for a symbol."""
        try:
            # Calculate number of days between start and end
            days = (end - start).days
            if days <= 0:
                days = 1

            # Get data from Alpaca
            df = self.client.get_historical_data(
                symbol=symbol, timeframe="1D", start=start, end=end, limit=days
            )
            if df.empty:
                self.logger.warning("No historical data found for %s", symbol)
                return pd.DataFrame()

            # Set timestamp as index
            df.index = pd.to_datetime(df.index)
            return df
        except Exception as e:
            self.logger.error("Error getting historical data for %s: %s", symbol, e)
            return pd.DataFrame()

    def get_latest_data(self, symbol: str) -> pd.DataFrame:
        """Get latest data for a symbol."""
        try:
            # Get last 100 bars
            end = datetime.now()
            start = end - timedelta(days=100)
            df = self.client.get_historical_data(
                symbol=symbol, timeframe="1D", start=start, end=end, limit=100
            )
            if df.empty:
                self.logger.warning("No data found for %s", symbol)
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
            self.logger.error("Error getting latest data for %s: %s", symbol, e)
            return pd.DataFrame()

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price for a symbol."""
        try:
            if symbol in self.data and not self.data[symbol].empty:
                return float(self.data[symbol]["close"].iloc[-1])
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


class MockDataFeed(DataFeed):
    """Mock data feed for testing purposes."""

    def __init__(self, client: Optional[AlpacaClient] = None) -> None:
        """Initialize mock data feed.

        Args:
            client: Optional Alpaca client instance (not used in mock)
        """
        super().__init__(client or AlpacaClient())
        self._mock_data: Dict[str, pd.DataFrame] = {}
        self._mock_prices: Dict[str, float] = {}
        self._mock_trends: Dict[str, str] = {}  # 'up', 'down', or 'sideways'
        self._mock_volatility: Dict[str, float] = {}  # Price volatility factor

    def add_symbol(self, symbol: str) -> bool:
        """Add a symbol to track with mock data.

        Args:
            symbol: Trading symbol to add

        Returns:
            True if symbol was added successfully, False otherwise
        """
        try:
            if symbol not in self.symbols:
                self.symbols.append(symbol)
                self._mock_prices[symbol] = 100.0  # Initial price
                self._mock_trends[symbol] = "sideways"
                self._mock_volatility[symbol] = 0.02  # 2% daily volatility
                self._generate_mock_data(symbol)
                self.logger.info("Added mock symbol %s to data feed", symbol)
                return True
            return False
        except Exception as e:
            self.logger.error("Error adding mock symbol %s: %s", symbol, str(e))
            return False

    def _generate_mock_data(self, symbol: str) -> None:
        """Generate mock historical data for a symbol."""
        try:
            # Generate 100 days of mock data
            dates = pd.date_range(end=datetime.now(), periods=100, freq="D")
            base_price = self._mock_prices[symbol]
            volatility = self._mock_volatility[symbol]

            # Generate random walk prices
            np.random.seed(hash(symbol) % 2**32)  # Consistent random data per symbol
            returns = np.random.normal(0, volatility, len(dates))
            prices = base_price * (1 + returns).cumprod()

            # Create DataFrame
            df = pd.DataFrame(
                {
                    "open": prices * (1 + np.random.normal(0, volatility / 2, len(dates))),
                    "high": prices * (1 + np.abs(np.random.normal(0, volatility, len(dates)))),
                    "low": prices * (1 - np.abs(np.random.normal(0, volatility, len(dates)))),
                    "close": prices,
                    "volume": np.random.randint(1000000, 5000000, len(dates)),
                },
                index=dates,
            )

            # Calculate indicators
            self._calculate_indicators(symbol)

            # Store mock data
            self._mock_data[symbol] = df
            self.data[symbol] = df

        except Exception as e:
            self.logger.error("Error generating mock data for %s: %s", symbol, str(e))

    def get_historical_data(self, symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
        """Get mock historical data for a symbol."""
        try:
            if symbol not in self._mock_data:
                return pd.DataFrame()

            df = self._mock_data[symbol]
            mask = (df.index >= start) & (df.index <= end)
            return df[mask]
        except Exception as e:
            self.logger.error("Error getting mock historical data for %s: %s", symbol, str(e))
            return pd.DataFrame()

    def get_latest_data(self, symbol: str) -> pd.DataFrame:
        """Get latest mock data for a symbol."""
        try:
            if symbol not in self._mock_data:
                return pd.DataFrame()

            # Update mock price based on trend
            current_price = self._mock_prices[symbol]
            volatility = self._mock_volatility[symbol]

            if self._mock_trends[symbol] == "up":
                new_price = current_price * (1 + np.random.normal(0.001, volatility))
            elif self._mock_trends[symbol] == "down":
                new_price = current_price * (1 + np.random.normal(-0.001, volatility))
            else:  # sideways
                new_price = current_price * (1 + np.random.normal(0, volatility))

            self._mock_prices[symbol] = new_price

            # Update mock data
            self._generate_mock_data(symbol)

            # Get latest data
            df = self._mock_data[symbol].iloc[-1:]

            # Notify callbacks
            for callback in self.callbacks:
                callback(symbol, df)

            return df
        except Exception as e:
            self.logger.error("Error getting latest mock data for %s: %s", symbol, str(e))
            return pd.DataFrame()

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest mock price for a symbol."""
        try:
            if symbol in self._mock_prices:
                return self._mock_prices[symbol]
            return None
        except Exception as e:
            self.logger.error("Error getting latest mock price for %s: %s", symbol, str(e))
            return None

    def set_mock_trend(self, symbol: str, trend: str) -> None:
        """Set the trend for a mock symbol.

        Args:
            symbol: Trading symbol
            trend: 'up', 'down', or 'sideways'
        """
        if trend in ["up", "down", "sideways"]:
            self._mock_trends[symbol] = trend
            self.logger.info("Set mock trend for %s to %s", symbol, trend)

    def set_mock_volatility(self, symbol: str, volatility: float) -> None:
        """Set the volatility for a mock symbol.

        Args:
            symbol: Trading symbol
            volatility: Daily volatility factor (e.g., 0.02 for 2%)
        """
        self._mock_volatility[symbol] = volatility
        self.logger.info("Set mock volatility for %s to %.2f%%", symbol, volatility * 100)
