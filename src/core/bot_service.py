"""Bot service module for managing bot lifecycle and status."""

from enum import Enum, auto
from typing import Optional, Dict, Any
from threading import Thread, Event
import time
from datetime import datetime

from src.core.bot import TradingBot
from src.core.strategy import Strategy
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
    """Service class for managing bot lifecycle and status."""
    
    def __init__(
        self,
        strategy: Strategy,
        symbols: list[str],
        initial_capital: float = 100000.0
    ) -> None:
        """Initialize bot service.
        
        Args:
            strategy: Trading strategy
            symbols: List of trading symbols
            initial_capital: Initial capital for trading
        """
        self.strategy = strategy
        self.symbols = symbols
        self.initial_capital = initial_capital
        self.bot: Optional[TradingBot] = None
        self.status = BotStatus.STOPPED
        self.error_message: Optional[str] = None
        self._thread: Optional[Thread] = None
        self._stop_event = Event()
        self._last_update = datetime.now()
        
    def start(self) -> bool:
        """Start the bot service.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.status != BotStatus.STOPPED:
            logger.warning("Bot is not in STOPPED state")
            return False
            
        try:
            self.status = BotStatus.STARTING
            self._stop_event.clear()
            
            # Initialize bot
            self.bot = TradingBot(
                strategy=self.strategy,
                symbols=self.symbols,
                initial_capital=self.initial_capital
            )
            
            # Start bot in a separate thread
            self._thread = Thread(target=self._run_bot, daemon=True)
            self._thread.start()
            
            self.status = BotStatus.RUNNING
            self._last_update = datetime.now()
            return True
            
        except Exception as e:
            self.status = BotStatus.ERROR
            self.error_message = str(e)
            logger.error("Error starting bot: %s", e)
            return False
            
    def stop(self) -> bool:
        """Stop the bot service.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if self.status not in [BotStatus.RUNNING, BotStatus.ERROR]:
            logger.warning("Bot is not in RUNNING or ERROR state")
            return False
            
        try:
            self.status = BotStatus.STOPPING
            self._stop_event.set()
            
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=5)
                
            if self.bot:
                self.bot.stop()
                
            self.status = BotStatus.STOPPED
            self._last_update = datetime.now()
            return True
            
        except Exception as e:
            self.status = BotStatus.ERROR
            self.error_message = str(e)
            logger.error("Error stopping bot: %s", e)
            return False
            
    def _run_bot(self) -> None:
        """Run the bot in a separate thread."""
        try:
            if not self.bot:
                raise RuntimeError("Bot not initialized")
                
            while not self._stop_event.is_set():
                self.bot._run()  # Run one iteration
                self._last_update = datetime.now()
                time.sleep(1)
                
        except Exception as e:
            self.status = BotStatus.ERROR
            self.error_message = str(e)
            logger.error("Error in bot thread: %s", e)
            
    def get_status(self) -> Dict[str, Any]:
        """Get current bot status.
        
        Returns:
            Dictionary with bot status information
        """
        return {
            "status": self.status.name,
            "error_message": self.error_message,
            "last_update": self._last_update.isoformat(),
            "symbols": self.symbols,
            "initial_capital": self.initial_capital,
            "current_capital": self.bot.portfolio.current_balance if self.bot else None,
            "active_positions": len(self.bot.positions) if self.bot else 0
        } 