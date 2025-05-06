"""Data feed for retrieving market data."""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, cast

import pandas as pd

from src.core.alpaca_client import AlpacaClient
from src.core.alpaca_types import Asset as AssetProtocol
from src.core.alpaca_types import Bar
from src.core.alpaca_types import BarSet
from src.core.alpaca_types import Clock as ClockProtocol
from src.core.alpaca_types import Position as PositionProtocol
from src.core.alpaca_types import TimeFrame
from src.core.alpaca_types import TradeAccount as TradeAccountProtocol
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class DataFeed:
    """Data feed for retrieving market data."""

    def __init__(
        self, api_key: str, api_secret: str, symbols: List[str], cache_dir: str = "data/cache"
    ) -> None:
        """Initialize data feed.

        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            symbols: List of symbols to get data for
            cache_dir: Directory to store cache files
        """
        self.client = AlpacaClient(api_key, api_secret)
        self.symbols = symbols
        self.timeframe = TimeFrame(amount=1, unit="minute")
        self._data: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        self._cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def _get_cache_path(self, symbol: str, timeframe: TimeFrame) -> str:
        """Get cache file path for a symbol and timeframe.

        Args:
            symbol: Trading symbol
            timeframe: Data timeframe

        Returns:
            Cache file path
        """
        return os.path.join(self._cache_dir, f"{symbol}_{timeframe.value}.json")

    def _load_cache(self, symbol: str, timeframe: TimeFrame) -> Optional[List[Dict[str, Any]]]:
        """Load data from cache.

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
                    data = json.load(f)
                    return [dict(item) for item in data]  # Ensure we return a list of dicts
            return None
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            return None

    def _save_cache(
        self,
        symbol: str,
        timeframe: TimeFrame,
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

    def get_bars(
        self,
        symbol: str,
        start: datetime,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> Optional[BarSet]:
        """Get historical bars for a symbol.

        Args:
            symbol: Symbol to get data for
            start: Start time
            end: End time (optional)
            limit: Maximum number of bars to return (optional)

        Returns:
            BarSet if successful, None otherwise
        """
        try:
            # Try to get from cache first
            cached_data = self._load_cache(symbol, self.timeframe)
            if cached_data:
                bars = [Bar(**bar) for bar in cached_data]
                return BarSet(bars=bars)

            # If not in cache, get from API
            bars = self.client.get_bars(
                symbol=symbol,
                timeframe=self.timeframe.value,
                start=start,
                end=end,
                limit=limit,
            )
            if bars:
                bar_data = [
                    {
                        "timestamp": bar.t,
                        "open": float(bar.o),
                        "high": float(bar.h),
                        "low": float(bar.l),
                        "close": float(bar.c),
                        "volume": int(bar.v),
                    }
                    for bar in bars
                ]
                self._save_cache(symbol, self.timeframe, bar_data)
                return BarSet(bars=[Bar(**bar) for bar in bar_data])
            return None
        except Exception as e:
            logger.error(f"Error getting bars for {symbol}: {e}")
            return None

    def get_historical_data(
        self,
        symbol: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """Get historical market data.

        Args:
            symbol: Symbol to get data for
            start: Start time (default: 1 day ago)
            end: End time (default: now)
            limit: Maximum number of bars to return

        Returns:
            pd.DataFrame: Historical market data
        """
        try:
            # Set default time range if not provided
            if end is None:
                end = datetime.now()
            if start is None:
                start = end - timedelta(days=1)

            # Get bars from Alpaca
            bars = self.client.get_bars(
                symbol=symbol,
                timeframe=self.timeframe,
                start=start,
                end=end,
                limit=limit,
            )

            # Convert bars to DataFrame
            df = pd.DataFrame(
                [
                    {
                        "timestamp": bar.timestamp,
                        "open": bar.open,
                        "high": bar.high,
                        "low": bar.low,
                        "close": bar.close,
                        "volume": bar.volume,
                        "trade_count": bar.trade_count,
                        "vwap": bar.vwap,
                    }
                    for bar in bars.bars[symbol]
                ]
            )

            # Set timestamp as index
            if not df.empty:
                df.set_index("timestamp", inplace=True)

            return df

        except Exception as e:
            logger.error("Error getting historical data: %s", str(e))
            return pd.DataFrame()

    def get_latest_data(
        self,
        symbol: str,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """Get latest market data.

        Args:
            symbol: Symbol to get data for
            limit: Maximum number of bars to return

        Returns:
            pd.DataFrame: Latest market data
        """
        try:
            # Get bars from Alpaca
            end = datetime.now()
            start = end - timedelta(minutes=limit if limit else 100)

            bars = self.client.get_bars(
                symbol=symbol,
                timeframe=self.timeframe,
                start=start,
                end=end,
                limit=limit,
            )

            # Convert bars to DataFrame
            df = pd.DataFrame(
                [
                    {
                        "timestamp": bar.timestamp,
                        "open": bar.open,
                        "high": bar.high,
                        "low": bar.low,
                        "close": bar.close,
                        "volume": bar.volume,
                        "trade_count": bar.trade_count,
                        "vwap": bar.vwap,
                    }
                    for bar in bars.bars[symbol]
                ]
            )

            # Set timestamp as index
            if not df.empty:
                df.set_index("timestamp", inplace=True)

            return df

        except Exception as e:
            logger.error("Error getting latest data: %s", str(e))
            return pd.DataFrame()

    def get_account(self) -> TradeAccountProtocol:
        """Get account information.

        Returns:
            TradeAccountProtocol: Account information
        """
        return self.client.get_account()

    def get_positions(self) -> List[PositionProtocol]:
        """Get current positions.

        Returns:
            List[PositionProtocol]: List of positions
        """
        return self.client.get_all_positions()

    def get_open_position(self, symbol: str) -> PositionProtocol:
        """Get open position.

        Args:
            symbol: Symbol to get position for

        Returns:
            PositionProtocol: Position information
        """
        return self.client.get_open_position(symbol)

    def get_asset(self, symbol: str) -> AssetProtocol:
        """Get asset information.

        Args:
            symbol: Symbol to get asset for

        Returns:
            AssetProtocol: Asset information
        """
        return self.client.get_asset(symbol)

    def get_clock(self) -> ClockProtocol:
        """Get market clock information.

        Returns:
            ClockProtocol: Market clock information
        """
        return self.client.get_clock()
