"""Alpaca API client wrapper."""
from typing import Dict, Any, Optional
import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class AlpacaClient:
    """Wrapper for Alpaca API client."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize Alpaca API client.

        Args:
            config (Optional[Config]): Configuration object. If None, will be loaded from environment.
        """
        if config is None:
            config = Config()

        self.config = config
        self.trading_client = TradingClient(
            api_key=config.ALPACA_API_KEY,
            secret_key=config.ALPACA_SECRET_KEY,
            paper=True
        )

        self.data_client = StockHistoricalDataClient(
            api_key=config.ALPACA_API_KEY,
            secret_key=config.ALPACA_SECRET_KEY
        )

        logger.info("Initialized Alpaca client")

    def get_account(self) -> Dict[str, Any]:
        """Get account information.

        Returns:
            Dict[str, Any]: Account information
        """
        try:
            account = self.trading_client.get_account()
            return {
                'id': account.id,
                'status': account.status,
                'currency': account.currency,
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value),
                'buying_power': float(account.buying_power),
                'initial_margin': float(account.initial_margin),
                'maintenance_margin': float(account.maintenance_margin),
                'daytrading_buying_power': float(account.daytrading_buying_power),
                'equity': float(account.equity),
                'last_equity': float(account.last_equity),
                'multiplier': float(account.multiplier),
                'shorting_enabled': account.shorting_enabled,
                'pattern_day_trader': account.pattern_day_trader,
                'trading_blocked': account.trading_blocked,
                'transfers_blocked': account.transfers_blocked,
                'account_blocked': account.account_blocked,
                'created_at': account.created_at,
                'trade_suspended_by_user': account.trade_suspended_by_user
            }
        except Exception as e:
            logger.error("Error getting account info: %s", str(e))
            raise

    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """Get current positions.

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of positions by symbol
        """
        try:
            positions = self.trading_client.get_all_positions()
            return {
                position.symbol: {
                    'qty': float(position.qty),
                    'avg_entry_price': float(position.avg_entry_price),
                    'market_value': float(position.market_value),
                    'current_price': float(position.current_price),
                    'unrealized_pl': float(position.unrealized_pl),
                    'unrealized_plpc': float(position.unrealized_plpc),
                    'unrealized_intraday_pl': float(position.unrealized_intraday_pl),
                    'unrealized_intraday_plpc': float(position.unrealized_intraday_plpc),
                    'side': position.side
                }
                for position in positions
            }
        except Exception as e:
            logger.error("Error getting positions: %s", str(e))
            raise

    def get_bars(
        self,
        symbol: str,
        timeframe: str = '1D',
        limit: int = 100
    ) -> Optional[pd.DataFrame]:
        """Get historical bars data.

        Args:
            symbol (str): Trading symbol
            timeframe (str): Time frame for the data (default: '1D')
            limit (int): Number of bars to retrieve (default: 100)

        Returns:
            Optional[pd.DataFrame]: DataFrame with OHLCV data or None if error occurs
        """
        try:
            request_params = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                limit=limit
            )
            bars = self.data_client.get_stock_bars(request_params)
            return bars.df
        except Exception as e:
            logger.error("Error getting bars data: %s", str(e))
            return None 