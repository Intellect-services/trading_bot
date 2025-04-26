import os
import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
from config import *

class DataHandler:
    def __init__(self):
        self.client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)
        self._ensure_data_directory()

    def _ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

    def get_historical_data(self, symbol=DEFAULT_SYMBOL, timeframe=DEFAULT_TIMEFRAME, days=30):
        """Fetch historical market data"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        request_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=start_date,
            end=end_date
        )

        try:
            bars = self.client.get_stock_bars(request_params)
            df = bars.df
            
            # Save to CSV
            df.to_csv(HISTORICAL_DATA_FILE)
            return df
        except Exception as e:
            print(f"Error fetching historical data: {e}")
            return None

    def get_latest_price(self, symbol=DEFAULT_SYMBOL):
        """Get the latest price for a symbol"""
        try:
            request_params = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                limit=1
            )
            bars = self.client.get_stock_bars(request_params)
            return bars.df['close'].iloc[-1]
        except Exception as e:
            print(f"Error fetching latest price: {e}")
            return None 