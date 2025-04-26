"""Market data feed module."""
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class DataFeed:
    """Market data feed class for handling real-time and historical data."""

    def __init__(self, config: Config):
        """Initialize data feed with configuration.

        Args:
            config (Config): Configuration object containing API keys and settings
        """
        self.config = config
        self.data_client = StockHistoricalDataClient(
            api_key=config.ALPACA_API_KEY,
            secret_key=config.ALPACA_SECRET_KEY
        )
        self.symbols: List[str] = []
        self.timeframe = TimeFrame.Day
        self.callbacks: List[Callable[[pd.DataFrame], None]] = []
        self.data_cache: Dict[str, pd.DataFrame] = {}
        logger.info("Initialized data feed")

    def add_symbol(self, symbol: str) -> None:
        """Add a symbol to the data feed.

        Args:
            symbol (str): Trading symbol to add
        """
        if symbol not in self.symbols:
            self.symbols.append(symbol)
            logger.info("Added symbol to data feed: %s", symbol)

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
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100
    ) -> Optional[pd.DataFrame]:
        """Get historical market data.

        Args:
            symbol (str): Trading symbol
            start (Optional[datetime]): Start date
            end (Optional[datetime]): End date
            limit (int): Number of bars to retrieve

        Returns:
            Optional[pd.DataFrame]: Historical market data or None if error occurs
        """
        try:
            if start is None:
                start = datetime.now() - timedelta(days=limit)
            if end is None:
                end = datetime.now()

            request_params = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=self.timeframe,
                start=start,
                end=end
            )

            bars = self.data_client.get_stock_bars(request_params)
            if bars is not None:
                df = bars.df
                if not df.empty:
                    self.data_cache[symbol] = df
                    logger.info(
                        "Retrieved %d bars for %s from %s to %s",
                        len(df),
                        symbol,
                        df.index[0],
                        df.index[-1]
                    )
                    return df
            return None
        except Exception as e:
            logger.error("Error getting historical data: %s", str(e))
            return None

    def get_latest_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get latest market data for a symbol.

        Args:
            symbol (str): Trading symbol

        Returns:
            Optional[pd.DataFrame]: Latest market data or None if error occurs
        """
        try:
            request_params = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=self.timeframe,
                limit=1
            )
            bars = self.data_client.get_stock_bars(request_params)
            if bars is not None:
                df = bars.df
                if not df.empty:
                    if symbol in self.data_cache:
                        self.data_cache[symbol] = pd.concat(
                            [self.data_cache[symbol], df]
                        ).drop_duplicates()
                    else:
                        self.data_cache[symbol] = df
                    logger.info(
                        "Retrieved latest bar for %s at %s",
                        symbol,
                        df.index[-1]
                    )
                    return df
            return None
        except Exception as e:
            logger.error("Error getting latest data: %s", str(e))
            return None

    def add_callback(self, callback: Callable[[pd.DataFrame], None]) -> None:
        """Add a callback function for real-time data updates.

        Args:
            callback (Callable[[pd.DataFrame], None]): Callback function
        """
        self.callbacks.append(callback)
        logger.info("Added callback function")

    def remove_callback(self, callback: Callable[[pd.DataFrame], None]) -> None:
        """Remove a callback function.

        Args:
            callback (Callable[[pd.DataFrame], None]): Callback function to remove
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            logger.info("Removed callback function")

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