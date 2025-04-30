"""Bot service module for managing bot lifecycle and status."""

import logging
import time
from datetime import datetime
from enum import Enum, auto
from threading import Event, Thread
from typing import Any, Dict, List, Optional

from src.core.alpaca_client import AlpacaClient
from src.core.bot import TradingBot
from src.core.data_feed import DataFeed
from src.core.portfolio import Portfolio
from src.core.risk_manager import RiskManager
from src.core.strategy import Strategy
from src.strategies.moving_average import MovingAverageCrossover
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class BotStatus(Enum):
    """Bot status enumeration."""

    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    ERROR = auto()


class BotService:
    """Service class for managing trading bot operations."""

    def __init__(self, config: Config, alpaca_client: AlpacaClient) -> None:
        """Initialize bot service.

        Args:
            config: Configuration object
            alpaca_client: AlpacaClient instance
        """
        self.config = config
        self.portfolio = Portfolio(config.INITIAL_CAPITAL)
        self.strategy = MovingAverageCrossover()
        self.alpaca_client = alpaca_client
        self.data_feed = DataFeed(self.alpaca_client)
        self.risk_manager = RiskManager(config)
        self.bot = TradingBot(
            config=config,
            strategy=self.strategy,
            portfolio=self.portfolio,
            data_feed=self.data_feed,
            risk_manager=self.risk_manager,
        )
        self._error_count = 0
        self.current_balance: float = float(config.INITIAL_CAPITAL)
        self.status = BotStatus.STOPPED
        self.error_message: Optional[str] = None
        self._thread: Optional[Thread] = None
        self._stop_event = Event()
        self._last_update = datetime.now()
        self._is_running = False
        self._start_time: Optional[datetime] = None
        self._runtime = 0
        self._last_error_time: Optional[datetime] = None
        self._max_errors = 5
        self._error_reset_time = 300  # 5 minutes in seconds
        self.logger = logging.getLogger(__name__)
        self.initial_value: float = 0.0
        self.last_value: float = 0.0
        self.total_return: float = 0.0
        self.daily_return: float = 0.0
        self.total_trades: int = 0
        self.active_positions: int = 0
        logger.info("Bot service initialized")

    def start(self) -> bool:
        """Start the bot service.

        Returns:
            True if started successfully, False otherwise
        """
        if self.status != BotStatus.STOPPED:
            logger.warning(f"Bot is not in STOPPED state (current state: {self.status.name})")
            return False

        try:
            logger.info("Starting bot service...")
            self.status = BotStatus.STARTING
            self._stop_event.clear()
            self._is_running = True
            self._start_time = datetime.now()
            self._runtime = 0
            self._error_count = 0
            self._last_error_time = None

            # Initialize bot
            logger.info("Initializing bot...")
            self.bot = TradingBot(
                config=self.config,
                strategy=self.strategy,
                portfolio=self.portfolio,
                data_feed=self.data_feed,
                risk_manager=self.risk_manager,
            )

            # Start bot in a separate thread
            logger.info("Starting bot thread...")
            self._thread = Thread(target=self._run_bot, daemon=True)
            self._thread.start()

            # Wait for thread to start
            time.sleep(1)
            if not self._thread.is_alive():
                raise RuntimeError("Bot thread failed to start")

            self.status = BotStatus.RUNNING
            self._last_update = datetime.now()
            logger.info("Bot service started successfully")
            return True

        except Exception as e:
            self.status = BotStatus.ERROR
            self.error_message = str(e)
            self._is_running = False
            self._last_error_time = datetime.now()
            self._error_count += 1
            logger.error(f"Error starting bot: {e}")
            return False

    def stop(self) -> bool:
        """Stop the bot service.

        Returns:
            True if stopped successfully, False otherwise
        """
        if self.status not in [BotStatus.RUNNING, BotStatus.ERROR]:
            logger.warning(
                f"Bot is not in RUNNING or ERROR state (current state: {self.status.name})"
            )
            return False

        try:
            logger.info("Stopping bot service...")
            self.status = BotStatus.STOPPING
            self._is_running = False
            self._stop_event.set()

            if self._thread and self._thread.is_alive():
                logger.info("Waiting for bot thread to stop...")
                self._thread.join(timeout=5)

            if self.bot:
                logger.info("Stopping bot...")
                self.bot.stop()

            self.status = BotStatus.STOPPED
            self._last_update = datetime.now()
            self._start_time = None
            self._runtime = 0
            logger.info("Bot service stopped successfully")
            return True

        except Exception as e:
            self.status = BotStatus.ERROR
            self.error_message = str(e)
            self._last_error_time = datetime.now()
            self._error_count += 1
            logger.error(f"Error stopping bot: {e}")
            return False

    def _run_bot(self) -> None:
        """Run the bot in a separate thread."""
        try:
            if not self.bot:
                raise RuntimeError("Bot not initialized")

            while self._is_running and not self._stop_event.is_set():
                try:
                    # Check error count and reset if needed
                    if (
                        self._last_error_time
                        and (datetime.now() - self._last_error_time).total_seconds()
                        > self._error_reset_time
                    ):
                        self._error_count = 0
                        self._last_error_time = None

                    # Update runtime
                    if self._start_time:
                        self._runtime = (datetime.now() - self._start_time).total_seconds()

                    # Run one iteration
                    self.bot._run()
                    self._last_update = datetime.now()
                    time.sleep(1)

                except Exception as e:
                    self._last_error_time = datetime.now()
                    self._error_count += 1
                    logger.error(f"Error in bot iteration: {e}")

                    # Stop bot if too many errors
                    if self._error_count >= self._max_errors:
                        logger.error("Too many errors, stopping bot")
                        self.status = BotStatus.ERROR
                        self.error_message = f"Too many errors ({self._error_count})"
                        self._is_running = False
                        break

                    time.sleep(1)
                    continue

        except Exception as e:
            self.status = BotStatus.ERROR
            self.error_message = str(e)
            self._is_running = False
            self._last_error_time = datetime.now()
            self._error_count += 1
            logger.error("Error in bot thread: %s", e)

    def get_status(self) -> Dict[str, Any]:
        """Get current bot status.

        Returns:
            Dictionary containing bot status information
        """
        runtime_str = "00:00:00"
        if self._start_time:
            total_seconds = int(self._runtime)
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            runtime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        return {
            "status": self.status.name,
            "error_message": self.error_message,
            "last_update": self._last_update.isoformat(),
            "runtime": runtime_str,
            "symbols": self.bot.symbols if self.bot else [],
            "initial_capital": self.config.INITIAL_CAPITAL,
            "current_capital": self.current_balance,
            "active_positions": len(self.bot.positions) if self.bot else 0,
            "error_count": self._error_count,
            "last_error_time": self._last_error_time.isoformat() if self._last_error_time else None,
            "start_time": self._start_time.isoformat() if self._start_time else None,
        }

    def get_current_balance(self) -> float:
        """Get current portfolio balance.

        Returns:
            Current balance
        """
        return self.current_balance

    def update_metrics(self) -> None:
        """Update bot metrics."""
        try:
            # Get current account value
            account = self.alpaca_client.get_account()
            current_value = float(account.get("equity", 0))

            # Calculate returns
            if self.initial_value > 0:
                self.total_return = (current_value - self.initial_value) / self.initial_value
                self.daily_return = (
                    (current_value - self.last_value) / self.last_value
                    if self.last_value > 0
                    else 0.0
                )

            # Update values
            self.last_value = current_value
            self.total_trades = int(len(self.alpaca_client.get_orders()))
            self.active_positions = int(len(self.alpaca_client.get_all_positions()))

            # Log metrics
            self.logger.info(
                f"Bot metrics - Total Return: {self.total_return:.2%}, "
                f"Daily Return: {self.daily_return:.2%}, "
                f"Total Trades: {self.total_trades}, "
                f"Active Positions: {self.active_positions}"
            )
        except Exception as e:
            self.logger.error(f"Error updating metrics: {str(e)}")
