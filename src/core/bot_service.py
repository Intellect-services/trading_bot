"""Bot service module for managing trading bot operations."""

import logging
import time
from datetime import datetime, timedelta
from enum import Enum, auto
from threading import Event, Thread
from typing import Any, Dict, List, Optional, Union

from ..core.alpaca_client import AlpacaClient
from ..core.data_feed import DataFeed
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
        self.data_feed = DataFeed(config, alpaca_client)

        if strategy is None:
            from ..strategies.moving_average import MovingAverageCrossover

            strategy = MovingAverageCrossover(config)

        self.bot = TradingBot(
            config=config,
            strategy=strategy,
            data_feed=self.data_feed,
            risk_manager=self.risk_manager,
        )

        self.logger = logger
        logger.info("Bot service initialized")

    def start(self) -> None:
        """Start the trading bot."""
        try:
            self.bot.start()
            logger.info("Trading bot started")
        except Exception as e:
            logger.error("Error starting trading bot: %s", str(e))
            raise

    def stop(self) -> None:
        """Stop the trading bot."""
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
        """
        try:
            account = self.alpaca_client.get_account()
            positions = self.alpaca_client.get_positions()

            return {
                "status": "running" if self.bot.is_running else "stopped",
                "initial_capital": float(self.config.INITIAL_CAPITAL),
                "current_capital": float(account.equity),
                "active_positions": len(positions),
                "total_trades": len(self.bot.trades),
                "last_update": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error("Error getting bot status: %s", str(e))
            return {
                "status": "error",
                "error": str(e),
            }

    def get_positions(self) -> List[Dict[str, Union[str, float]]]:
        """Get current positions.

        Returns:
            List[Dict[str, Union[str, float]]]: List of positions
        """
        try:
            positions = self.alpaca_client.get_positions()
            return [
                {
                    "symbol": position.symbol,
                    "quantity": float(position.qty),
                    "avg_price": float(position.avg_entry_price),
                    "current_price": float(position.current_price),
                    "market_value": float(position.market_value),
                    "unrealized_pl": float(position.unrealized_pl),
                    "unrealized_plpc": float(position.unrealized_plpc),
                }
                for position in positions
            ]
        except Exception as e:
            logger.error("Error getting positions: %s", str(e))
            return []

    def get_trades(self) -> List[Dict[str, Union[str, float, datetime]]]:
        """Get executed trades.

        Returns:
            List[Dict[str, Union[str, float, datetime]]]: List of trades
        """
        try:
            return [
                {
                    "timestamp": trade.timestamp,
                    "symbol": trade.symbol,
                    "quantity": float(trade.quantity),
                    "price": float(trade.price),
                    "side": trade.side,
                }
                for trade in self.bot.trades
            ]
        except Exception as e:
            logger.error("Error getting trades: %s", str(e))
            return []

    def get_portfolio_history(
        self, timeframe: str = "1D"
    ) -> Dict[str, Union[List[datetime], List[float], str]]:
        """Get portfolio history.

        Args:
            timeframe: Timeframe for history (default: "1D")

        Returns:
            Dict[str, Union[List[datetime], List[float], str]]: Portfolio history
        """
        try:
            history = self.alpaca_client.get_portfolio_history(timeframe=timeframe)
            return {
                "timestamp": history.timestamp,
                "equity": history.equity,
                "profit_loss": history.profit_loss,
                "profit_loss_pct": history.profit_loss_pct,
                "base_value": float(history.base_value),
                "timeframe": timeframe,
            }
        except Exception as e:
            logger.error("Error getting portfolio history: %s", str(e))
            return {
                "timestamp": [],
                "equity": [],
                "profit_loss": [],
                "profit_loss_pct": [],
                "base_value": 0.0,
                "timeframe": timeframe,
            }
