"""Bot service module for managing trading bot operations."""

import logging
import time
from datetime import datetime, timedelta
from enum import Enum, auto
from threading import Event, Thread
from typing import Any, Dict, List, Optional, Union, cast

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
    """Service for managing trading bot operations."""

    def __init__(
        self,
        config: Config,
        alpaca_client: AlpacaClient,
        strategy: Optional[Strategy] = None,
    ) -> None:
        """Initialize bot service.

        Args:
            config: Configuration instance
            alpaca_client: Alpaca client instance
            strategy: Optional strategy instance
        """
        self.config = config
        self.alpaca_client = alpaca_client
        self.risk_manager = RiskManager(config)
        self.data_feed = AlpacaDataFeed(alpaca_client)

        if strategy is None:
            from ..strategies.moving_average import MovingAverageCrossover

            # Convert Config instance to dictionary
            config_dict = {
                "ALPACA_API_KEY": config.ALPACA_API_KEY,
                "ALPACA_SECRET_KEY": config.ALPACA_SECRET_KEY,
                "ALPACA_PAPER": config.ALPACA_PAPER,
                "INITIAL_CAPITAL": config.INITIAL_CAPITAL,
                "RISK_MAX_POSITION_SIZE": config.RISK_MAX_POSITION_SIZE,
                "RISK_STOP_LOSS_PCT": config.RISK_STOP_LOSS_PCT,
                "RISK_TAKE_PROFIT_PCT": config.RISK_TAKE_PROFIT_PCT,
                "RISK_MAX_DRAWDOWN": config.RISK_MAX_DRAWDOWN,
                "RISK_MAX_LEVERAGE": config.RISK_MAX_LEVERAGE,
                "RISK_PER_TRADE": config.RISK_PER_TRADE,
            }
            strategy = MovingAverageCrossover(config_dict)

        # Create AlpacaService instance
        from ..core.alpaca_service import AlpacaService

        # Convert Config instance to dictionary for AlpacaService
        config_dict = {
            "ALPACA_API_KEY": config.ALPACA_API_KEY,
            "ALPACA_SECRET_KEY": config.ALPACA_SECRET_KEY,
            "ALPACA_PAPER": config.ALPACA_PAPER,
            "INITIAL_CAPITAL": config.INITIAL_CAPITAL,
            "RISK_MAX_POSITION_SIZE": config.RISK_MAX_POSITION_SIZE,
            "RISK_STOP_LOSS_PCT": config.RISK_STOP_LOSS_PCT,
            "RISK_TAKE_PROFIT_PCT": config.RISK_TAKE_PROFIT_PCT,
            "RISK_MAX_DRAWDOWN": config.RISK_MAX_DRAWDOWN,
            "RISK_MAX_LEVERAGE": config.RISK_MAX_LEVERAGE,
            "RISK_PER_TRADE": config.RISK_PER_TRADE,
        }
        self.alpaca_service = AlpacaService(config_dict)

        # Initialize TradingBot with AlpacaService
        self.bot = TradingBot(alpaca_service=self.alpaca_service)

        logger.info("Bot service initialized")

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

    def get_positions(self) -> List[Dict[str, Union[str, float]]]:
        """Get current positions.

        Returns:
            List[Dict[str, Union[str, float]]]: List of positions

        Raises:
            Exception: If position retrieval fails
        """
        try:
            positions = self.alpaca_client.get_positions()
            return [
                {
                    "symbol": position.symbol,
                    "qty": float(position.qty),
                    "side": position.side,
                    "avg_entry_price": float(position.avg_entry_price),
                    "current_price": float(position.current_price),
                    "market_value": float(position.market_value),
                    "unrealized_pl": float(position.unrealized_pl),
                    "unrealized_plpc": float(position.unrealized_plpc),
                }
                for position in positions
            ]
        except Exception as e:
            logger.error("Error getting positions: %s", str(e))
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
