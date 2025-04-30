"""Trading bot module for executing trading strategies."""

import logging
import secrets  # For secure random number generation
import time
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional, cast

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.models import Bar
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.models import Order
from alpaca.trading.models import Position as AlpacaPosition
from alpaca.trading.requests import MarketOrderRequest

from src.core.portfolio import Portfolio
from src.core.position import Position
from src.core.strategy import Strategy
from src.strategies.base import BaseStrategy
from src.utils.config import Config
from src.utils.helpers import calculate_position_size
from src.utils.logger import setup_logger

logger = logging.getLogger(__name__)


class TradingBot:
    """Main trading bot class that manages trading operations."""

    def __init__(self, config: Config, strategy: BaseStrategy) -> None:
        """Initialize the trading bot.

        Args:
            config: Configuration object
            strategy: Trading strategy to use
        """
        self.config = config
        self.strategy = strategy
        self.trading_client = TradingClient(
            api_key=config.ALPACA_API_KEY,
            secret_key=config.ALPACA_SECRET_KEY,
            paper=config.ALPACA_PAPER,
        )
        self.data_client = StockHistoricalDataClient(
            api_key=config.ALPACA_API_KEY, secret_key=config.ALPACA_SECRET_KEY
        )
        self.positions: Dict[str, AlpacaPosition] = {}
        self.is_running: bool = False
        logger.info("Trading bot initialized")

    def start(self) -> None:
        """Start the trading bot."""
        if not self.config.is_valid:
            raise ValueError("Invalid configuration")

        self.is_running = True
        logger.info("Trading bot started")

        # Initialize positions
        self._update_positions()

    def stop(self) -> None:
        """Stop the trading bot."""
        self.is_running = False
        logger.info("Trading bot stopped")

    def _update_positions(self) -> None:
        """Update the current positions."""
        try:
            positions = self.trading_client.get_all_positions()
            self.positions = {
                cast(AlpacaPosition, position).symbol: position for position in positions
            }
        except Exception as e:
            logger.error(f"Error updating positions: {e}")
            self.positions = {}

    def get_position(self, symbol: str) -> Optional[AlpacaPosition]:
        """Get position for a specific symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Position object if exists, None otherwise
        """
        return self.positions.get(symbol)

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the trading bot.

        Returns:
            Dictionary containing bot status information
        """
        return {
            "running": self.is_running,
            "positions": len(self.positions),
            "strategy": self.strategy.__class__.__name__,
            "timestamp": datetime.now().isoformat(),
        }

    def execute_trade(self, symbol: str, side: OrderSide, quantity: float) -> Optional[Order]:
        """Execute a trade.

        Args:
            symbol: Trading symbol
            side: Order side (buy/sell)
            quantity: Number of shares

        Returns:
            Order object if successful, None otherwise
        """
        try:
            order_data = MarketOrderRequest(
                symbol=symbol, qty=quantity, side=side, time_in_force=TimeInForce.DAY
            )
            order = cast(Order, self.trading_client.submit_order(order_data))
            logger.info(f"Order submitted: {order}")
            return order
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return None

    def get_historical_data(
        self, symbol: str, timeframe: TimeFrame, limit: int = 100
    ) -> Optional[List[Bar]]:
        """Get historical price data.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe for the data
            limit: Number of bars to retrieve

        Returns:
            List of historical bars if successful, None otherwise
        """
        try:
            request_params = StockBarsRequest(
                symbol_or_symbols=symbol, timeframe=timeframe, limit=limit
            )
            bars = self.data_client.get_stock_bars(request_params)
            return list(bars[symbol]) if bars else None
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return None
