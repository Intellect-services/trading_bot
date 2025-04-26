"""Data feed module for fetching and processing market data."""

from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from src.core.alpaca_client import AlpacaClient
from src.utils.config import Config
from src.utils.logger import setup_logger
from src.data_handler import DataHandler

logger = setup_logger(__name__)

class DataFeed:
    """Handles market data feed and processing."""
    
    def __init__(self, config: Config):
        """Initialize data feed with configuration.
        
        Args:
            config: Configuration object containing API keys and settings
        """
        self.config = config
        self.client = AlpacaClient(
            api_key=config.ALPACA_API_KEY,
            secret_key=config.ALPACA_SECRET_KEY,
            paper=True  # Always use paper trading for safety
        )
        self.data: Dict[str, pd.DataFrame] = {}
        self.callbacks: List[Callable[[str, pd.DataFrame], None]] = []
        logger.info("Data feed initialized")
    
    def add_symbol(self, symbol: str) -> None:
        """Add a symbol to track.
        
        Args:
            symbol: Stock symbol to track
        """
        if symbol not in self.data:
            self.data[symbol] = pd.DataFrame()
            logger.info(f"Added symbol: {symbol}")
    
    def get_historical_data(
        self,
        symbol: str,
        lookback_days: int = 30,
        timeframe: str = "1D"
    ) -> pd.DataFrame:
        """Get historical market data.
        
        Args:
            symbol: Stock symbol
            lookback_days: Number of days to look back (default: 30)
            timeframe: Timeframe for data (default: "1D")
            
        Returns:
            DataFrame containing historical data
        """
        try:
            end = datetime.now()
            start = end - timedelta(days=lookback_days)
            
            data = self.client.get_historical_data(symbol, start, end, timeframe)
            if not data:
                logger.warning(f"No historical data found for {symbol}")
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            df.set_index("timestamp", inplace=True)
            
            self.data[symbol] = df
            self.calculate_indicators(symbol)
            
            logger.info(f"Retrieved historical data for {symbol}")
            return self.data[symbol]
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return pd.DataFrame()
    
    def calculate_indicators(self, symbol: str) -> None:
        """Calculate technical indicators for a symbol.
        
        Args:
            symbol: Stock symbol
        """
        try:
            if symbol not in self.data or self.data[symbol].empty:
                logger.warning(f"No data available for {symbol}")
                return
            
            df = self.data[symbol]
            
            # Calculate SMA
            df["sma_20"] = df["close"].rolling(window=20).mean()
            df["sma_50"] = df["close"].rolling(window=50).mean()
            
            # Calculate RSI
            delta = df["close"].diff()
            gain = delta.where(delta.gt(0), 0).rolling(window=14).mean()
            loss = -delta.where(delta.lt(0), 0).rolling(window=14).mean()
            rs = gain / loss
            df["rsi"] = 100 - (100 / (1 + rs))
            
            self.data[symbol] = df
            logger.info(f"Calculated indicators for {symbol}")
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
    
    def add_callback(self, callback: Callable[[str, pd.DataFrame], None]) -> None:
        """Add a callback function for data updates.
        
        Args:
            callback: Function to call when data is updated
        """
        self.callbacks.append(callback)
        logger.info("Added data callback function")
    
    def update_data(self, symbol: str, new_data: List[Dict[str, Any]]) -> None:
        """Update data for a symbol.
        
        Args:
            symbol: Stock symbol
            new_data: New data points to add
        """
        try:
            if not new_data:
                logger.warning(f"No new data to update for {symbol}")
                return
            
            df = pd.DataFrame(new_data)
            df.set_index("timestamp", inplace=True)
            
            if symbol in self.data:
                self.data[symbol] = pd.concat([self.data[symbol], df])
            else:
                self.data[symbol] = df
            
            self.calculate_indicators(symbol)
            
            for callback in self.callbacks:
                callback(symbol, self.data[symbol])
            
            logger.info(f"Updated data for {symbol}")
        except Exception as e:
            logger.error(f"Error updating data: {e}")
    
    def get_latest_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest data point for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Latest data point or None if not available
        """
        try:
            if symbol not in self.data or self.data[symbol].empty:
                logger.warning(f"No data available for {symbol}")
                return None
            
            latest = self.data[symbol].iloc[-1]
            return {
                "timestamp": latest.name,
                "open": float(latest["open"]),
                "high": float(latest["high"]),
                "low": float(latest["low"]),
                "close": float(latest["close"]),
                "volume": int(latest["volume"]),
                "sma_20": float(latest["sma_20"]) if "sma_20" in latest else None,
                "sma_50": float(latest["sma_50"]) if "sma_50" in latest else None,
                "rsi": float(latest["rsi"]) if "rsi" in latest else None
            }
        except Exception as e:
            logger.error(f"Error getting latest data: {e}")
            return None
