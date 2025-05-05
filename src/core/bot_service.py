"""Bot service for managing trading operations."""

import logging
import time
from datetime import datetime, timedelta
from enum import Enum, auto
from threading import Event, Thread
from typing import Any, Dict, List, Optional, Union, cast

from alpaca.data.timeframe import TimeFrame
from alpaca.trading.enums import OrderSide, OrderType, TimeInForce
from alpaca.trading.models import Account

from src.core.alpaca_service import AlpacaService
from src.core.alpaca_types import Asset, Clock, Order, Position, TradeAccount
from src.core.data_feed import DataFeed
from src.strategies.moving_average import MovingAverageCrossover

from ..core.alpaca_client import AlpacaClient
from ..core.data_feed import AlpacaDataFeed
from ..core.risk_manager import RiskManager
from ..core.strategy import Strategy
from ..core.trading_bot import TradingBot
from ..utils.config import Config
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class BotStatus(Enum):
    """Bot status enumeration."""

    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    ERROR = auto()


class BotService:
    """Service for managing trading operations."""

    def __init__(self, config: Config) -> None:
        """Initialize the bot service with configuration."""
        try:
            self.config = config
            self.alpaca_service = AlpacaService(config.api_key, config.api_secret)
            self.risk_manager = RiskManager(config.risk_factor, config.max_position_size)
            self.strategy = MovingAverageCrossover(
                short_window=config.short_window, long_window=config.long_window
            )
            self.positions: Dict[str, Position] = {}
            self.update_positions()
        except Exception as e:
            logger.error(f"Failed to initialize bot service: {e}")
            raise

    def start(self) -> None:
        """Start the trading bot.

        Raises:
            Exception: If bot fails to start
        """
        try:
            self.bot.start()
            logger.info("Trading bot started")
        except Exception as e:
            logger.error("Error starting trading bot: %s", str(e))
            raise

    def stop(self) -> None:
        """Stop the trading bot.

        Raises:
            Exception: If bot fails to stop
        """
        try:
            self.bot.stop()
            logger.info("Trading bot stopped")
        except Exception as e:
            logger.error("Error stopping trading bot: %s", str(e))
            raise

    def get_status(self) -> Dict[str, Union[str, float, int, bool]]:
        """Get the current status of the trading bot.

        Returns:
            Dict[str, Union[str, float, int, bool]]: Bot status information

        Raises:
            Exception: If status retrieval fails
        """
        try:
            account = self.alpaca_client.get_account()
            positions = self.alpaca_client.get_positions()

            return {
                "status": "running" if self.bot.is_running else "stopped",
                "initial_capital": float(self.config.INITIAL_CAPITAL),
                "current_capital": float(account.equity),
                "active_positions": len(positions),
                "total_trades": len(self.bot.trades) if hasattr(self.bot, "trades") else 0,
            }
        except Exception as e:
            logger.error("Error getting bot status: %s", str(e))
            raise

    def get_positions(self) -> List[Position]:
        """Get all positions."""
        try:
            return self.alpaca_service.get_all_positions()
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise

    def get_trades(self) -> List[Dict[str, Union[str, float, datetime]]]:
        """Get trade history.

        Returns:
            List[Dict[str, Union[str, float, datetime]]]: List of trades

        Raises:
            Exception: If trade history retrieval fails
        """
        try:
            if not hasattr(self.bot, "trades"):
                return []
            trades = self.bot.trades
            return [
                {
                    "symbol": trade.symbol,
                    "qty": float(trade.qty),
                    "side": trade.side,
                    "price": float(trade.price),
                    "timestamp": trade.timestamp,
                }
                for trade in trades
            ]
        except Exception as e:
            logger.error("Error getting trades: %s", str(e))
            raise

    def get_portfolio_history(
        self, timeframe: str = "1D"
    ) -> Dict[str, Union[List[datetime], List[float], str]]:
        """Get portfolio history.

        Args:
            timeframe: Timeframe for history (default: "1D")

        Returns:
            Dict[str, Union[List[datetime], List[float], str]]: Portfolio history

        Raises:
            Exception: If portfolio history retrieval fails
        """
        try:
            end = datetime.now()
            start = end - timedelta(days=30)  # Default to 30 days

            if timeframe == "1D":
                start = end - timedelta(days=30)
            elif timeframe == "1W":
                start = end - timedelta(weeks=12)
            elif timeframe == "1M":
                start = end - timedelta(days=365)

            account = self.alpaca_client.get_account()
            equity = float(account.equity)
            initial_capital = float(self.config.INITIAL_CAPITAL)

            return {
                "timestamp": [end],
                "equity": [equity],
                "timeframe": timeframe,
            }
        except Exception as e:
            logger.error("Error getting portfolio history: %s", str(e))
            raise

    def get_account(self) -> Account:
        """Get account information."""
        try:
            return self.alpaca_service.get_account()
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise

    def get_open_position(self, symbol: str) -> Optional[Position]:
        """Get open position for a symbol."""
        try:
            return self.alpaca_service.get_open_position(symbol)
        except Exception as e:
            logger.error(f"Failed to get open position: {e}")
            raise

    def get_asset(self, symbol: str) -> Asset:
        """Get asset information.

        Args:
            symbol: Symbol to get asset for

        Returns:
            Asset: Asset information
        """
        return self.alpaca_service.get_asset(symbol)

    def get_clock(self) -> Clock:
        """Get market clock."""
        try:
            return self.alpaca_service.get_clock()
        except Exception as e:
            logger.error(f"Failed to get clock: {e}")
            raise

    def submit_order(
        self,
        symbol: str,
        qty: float,
        side: OrderSide,
        type: OrderType = OrderType.MARKET,
        time_in_force: TimeInForce = TimeInForce.DAY,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Order:
        """Submit an order."""
        try:
            return self.alpaca_service.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=type,
                time_in_force=time_in_force,
                limit_price=limit_price,
                stop_price=stop_price,
            )
        except Exception as e:
            logger.error(f"Failed to submit order: {e}")
            raise

    def get_orders(self, status: Optional[str] = None) -> List[Order]:
        """Get orders.

        Args:
            status: Order status to filter by

        Returns:
            List[Order]: List of orders
        """
        return self.alpaca_service.get_orders(status=status)

    def get_order_by_id(self, order_id: str) -> Order:
        """Get order by ID.

        Args:
            order_id: ID of order to get

        Returns:
            Order: Order information
        """
        return self.alpaca_service.get_order_by_id(order_id)

    def cancel_order_by_id(self, order_id: str) -> None:
        """Cancel an order.

        Args:
            order_id: ID of order to cancel
        """
        self.alpaca_service.cancel_order_by_id(order_id)

    def update_positions(self) -> None:
        """Update positions dictionary."""
        try:
            positions = self.get_positions()
            self.positions = {p.symbol: p for p in positions}
        except Exception as e:
            logger.error(f"Failed to update positions: {e}")
            raise

    def check_market_status(self) -> bool:
        """Check if market is open."""
        try:
            clock = self.get_clock()
            return clock.is_open
        except Exception as e:
            logger.error(f"Failed to check market status: {e}")
            return False

    def run_strategy(self, symbol: str) -> None:
        """Run trading strategy for a symbol."""
        try:
            if not self.check_market_status():
                logger.info("Market is closed")
                return

            # Get historical data
            bars = self.alpaca_service.get_bars(
                symbol=symbol, timeframe=TimeFrame.Day, limit=self.config.lookback_period
            )

            if bars.empty:
                logger.warning(f"No data available for {symbol}")
                return

            # Update strategy state
            self.strategy.update_state(bars)

            # Get current position
            position = self.get_open_position(symbol)

            # Calculate position size based on risk
            close_price = bars.iloc[-1]["close"]
            position_size = self.risk_manager.calculate_position_size(close_price, symbol)

            # Check for buy signal
            if self.strategy.should_buy(symbol) and not position:
                self.submit_order(
                    symbol=symbol,
                    qty=position_size,
                    side=OrderSide.BUY,
                    type=OrderType.MARKET,
                    time_in_force=TimeInForce.DAY,
                )
                logger.info(f"Buy signal for {symbol}")

            # Check for sell signal
            elif self.strategy.should_sell(symbol) and position:
                self.submit_order(
                    symbol=symbol,
                    qty=float(position.qty),
                    side=OrderSide.SELL,
                    type=OrderType.MARKET,
                    time_in_force=TimeInForce.DAY,
                )
                logger.info(f"Sell signal for {symbol}")

        except Exception as e:
            logger.error(f"Failed to run strategy: {e}")
            raise
