"""Data feed for retrieving market data."""

import json
import os
from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from src.core.alpaca_service import AlpacaService
from src.core.alpaca_types import Asset as AssetProtocol
from src.core.alpaca_types import Bar, BarSet
from src.core.alpaca_types import Clock as ClockProtocol
from src.core.alpaca_types import Position as PositionProtocol
from src.core.alpaca_types import TradeAccount as TradeAccountProtocol
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class DataFeed:
    """Data feed for retrieving market data."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        symbols: list[str],
        cache_dir: str = "data/cache",
    ) -> None:
        """Initialize data feed.

        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            symbols: List of symbols to get data for
            cache_dir: Directory to store cache files
        """
        self.client = AlpacaService(api_key=api_key, secret_key=api_secret, trading_mode="paper")
        self.symbols = symbols
        self.timeframe = "1Min"
        self._data: dict[str, dict[str, list[dict[str, Any]]]] = {}
        self._cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def _get_cache_path(self, symbol: str, timeframe: str) -> str:
        """Get cache file path for a symbol and timeframe.

        Args:
            symbol: Trading symbol
            timeframe: Data timeframe

        Returns:
            Cache file path
        """
        return os.path.join(self._cache_dir, f"{symbol}_{timeframe}.json")

    def _load_cache(self, symbol: str, timeframe: str) -> list[dict[str, Any]] | None:
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
                with open(cache_path) as f:
                    data = json.load(f)
                    return [dict(item) for item in data]  # Ensure we return a list of dicts
            return None
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            return None

    def _save_cache(
        self,
        symbol: str,
        timeframe: str,
        data: list[dict[str, Any]],
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
                    str(k): str(v) if isinstance(v, pd.Timestamp | datetime) else v
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
        end: datetime | None = None,
        limit: int | None = None,
    ) -> BarSet | None:
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
                cached_bars = [
                    Bar(
                        timestamp=datetime.fromisoformat(str(bar["timestamp"])),
                        open=float(bar["open"]),
                        high=float(bar["high"]),
                        low=float(bar["low"]),
                        close=float(bar["close"]),
                        volume=int(float(bar["volume"])),
                    )
                    for bar in cached_data
                ]
                return BarSet(bars=cached_bars)

            # If not in cache, get from API
            raw_bars = self.client.get_bars(
                symbol=symbol,
                timeframe=self.timeframe,
                start=start,
                end=end,
                limit=limit,
            )
            if raw_bars:
                symbol_bars = raw_bars.get(symbol, [])
                bar_data = [
                    {
                        "timestamp": bar["timestamp"],
                        "open": float(bar["open"]),
                        "high": float(bar["high"]),
                        "low": float(bar["low"]),
                        "close": float(bar["close"]),
                        "volume": float(bar["volume"]),
                    }
                    for bar in symbol_bars
                ]
                self._save_cache(symbol, self.timeframe, bar_data)
                return BarSet(
                    bars=[
                        Bar(
                            timestamp=datetime.fromisoformat(str(bar["timestamp"])),
                            open=float(bar["open"]),
                            high=float(bar["high"]),
                            low=float(bar["low"]),
                            close=float(bar["close"]),
                            volume=int(float(bar["volume"])),
                        )
                        for bar in bar_data
                    ]
                )
            return None
        except Exception as e:
            logger.error(f"Error getting bars for {symbol}: {e}")
            return None

    def get_historical_data(
        self,
        symbol: str,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int | None = None,
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
            raw_bars = self.client.get_bars(
                symbol=symbol,
                timeframe=self.timeframe,
                start=start,
                end=end,
                limit=limit,
            )

            # Convert bars to DataFrame
            symbol_bars = raw_bars.get(symbol, []) if raw_bars else []
            df = pd.DataFrame(
                [
                    {
                        "timestamp": bar["timestamp"],
                        "open": float(bar["open"]),
                        "high": float(bar["high"]),
                        "low": float(bar["low"]),
                        "close": float(bar["close"]),
                        "volume": float(bar["volume"]),
                    }
                    for bar in symbol_bars
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
        limit: int | None = None,
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
                        "timestamp": bar["timestamp"],
                        "open": bar["open"],
                        "high": bar["high"],
                        "low": bar["low"],
                        "close": bar["close"],
                        "volume": bar["volume"],
                    }
                    for bar in bars[symbol]
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
        """Get account information."""
        account_dict = self.client.get_account()
        # Convert dict to TradeAccountProtocol-like object
        from src.core.alpaca_types import TradeAccount

        return TradeAccount(
            account_number=str(account_dict.get("account_number", "")),
            status=str(account_dict.get("status", "")),
            currency=str(account_dict.get("currency", "USD")),
            cash=float(account_dict.get("cash", 0.0)),
            portfolio_value=float(account_dict.get("portfolio_value", 0.0)),
            buying_power=float(account_dict.get("buying_power", 0.0)),
            equity=float(account_dict.get("equity", 0.0)),
        )

    def get_positions(self) -> list[PositionProtocol]:
        """Get all positions."""
        try:
            positions = self.client.get_all_positions()
            return [
                PositionProtocol(
                    symbol=pos.get("symbol", ""),
                    size=float(pos.get("qty", 0.0)),
                    avg_price=float(pos.get("avg_entry_price", 0.0)),
                    current_price=float(pos.get("current_price", 0.0)),
                    side=pos.get("side", ""),
                    stop_loss=0.0,
                    take_profit=0.0,
                )
                for pos in positions
            ]
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise

    def get_open_position(self, symbol: str) -> PositionProtocol | None:
        """Get open position for a symbol."""
        try:
            position = self.client.get_open_position(symbol)
            if not position:
                return None
            return PositionProtocol(
                symbol=position.get("symbol", ""),
                size=float(position.get("qty", 0.0)),
                avg_price=float(position.get("avg_entry_price", 0.0)),
                current_price=float(position.get("current_price", 0.0)),
                side=position.get("side", ""),
                stop_loss=0.0,
                take_profit=0.0,
            )
        except Exception as e:
            logger.error(f"Failed to get open position: {e}")
            raise

    def get_asset(self, symbol: str) -> AssetProtocol:
        """Get asset information."""
        asset_dict = self.client.get_asset(symbol)
        from src.core.alpaca_types import Asset

        return Asset(
            symbol=asset_dict.get("symbol", ""),
            name=asset_dict.get("name", ""),
            exchange=asset_dict.get("exchange", ""),
            class_=asset_dict.get("class", ""),
            status=asset_dict.get("status", ""),
            tradable=asset_dict.get("tradable", False),
        )

    def get_clock(self) -> ClockProtocol:
        """Get market clock."""
        clock_dict = self.client.get_clock()
        from src.core.alpaca_types import Clock

        return Clock(
            timestamp=pd.to_datetime(clock_dict.get("timestamp", datetime.utcnow())),
            is_open=bool(clock_dict.get("is_open", False)),
            next_open=pd.to_datetime(clock_dict.get("next_open", datetime.utcnow())),
            next_close=pd.to_datetime(clock_dict.get("next_close", datetime.utcnow())),
        )
