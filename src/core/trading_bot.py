import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from .alpaca_service import AlpacaService


class TradingBot:
    def __init__(self, alpaca_service: AlpacaService) -> None:
        self.alpaca_service = alpaca_service
        self.logger = logging.getLogger(__name__)
        self.is_running: bool = False
        self.start_time: Optional[datetime] = None
        self.total_trades: int = 0
        self.winning_trades: int = 0
        self.initial_capital: float = 0.0
        self.current_capital: float = 0.0
        self.logger.info("TradingBot initialized")

    def start(self) -> bool:
        """Start the trading bot."""
        try:
            if self.is_running:
                self.logger.warning("Bot is already running")
                return False

            # Get initial account information
            account = self.alpaca_service.get_account()
            self.initial_capital = float(account.get("equity", 0))
            self.current_capital = self.initial_capital

            # Check market status
            market_status = self.alpaca_service.get_market_status()
            if not market_status.get("is_open", False):
                self.logger.error("Cannot start bot: Market is closed")
                return False

            self.is_running = True
            self.start_time = datetime.now()
            self.logger.info("Trading bot started successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error starting bot: {str(e)}")
            self.is_running = False
            return False

    def stop(self) -> bool:
        """Stop the trading bot."""
        try:
            if not self.is_running:
                self.logger.warning("Bot is not running")
                return False

            self.is_running = False
            self.logger.info("Trading bot stopped successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error stopping bot: {str(e)}")
            return False

    def get_runtime(self) -> str:
        """Get the bot's runtime in HH:MM:SS format."""
        if not self.start_time:
            return "00:00:00"

        runtime = datetime.now() - self.start_time
        hours = runtime.seconds // 3600
        minutes = (runtime.seconds % 3600) // 60
        seconds = runtime.seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def get_total_trades(self) -> int:
        """Get the total number of trades."""
        return self.total_trades

    def get_win_rate(self) -> float:
        """Get the win rate as a percentage."""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100

    def get_average_return(self) -> float:
        """Get the average return per trade as a percentage."""
        if self.total_trades == 0:
            return 0.0
        return ((self.current_capital - self.initial_capital) / self.initial_capital) * 100

    def update_metrics(self) -> Dict[str, Any]:
        """Update and return current metrics."""
        try:
            account = self.alpaca_service.get_account()
            self.current_capital = float(account.get("equity", 0))

            return {
                "initial_capital": self.initial_capital,
                "current_capital": self.current_capital,
                "active_positions": len(self.alpaca_service.get_positions()),
                "total_trades": self.total_trades,
                "win_rate": self.get_win_rate(),
                "avg_return": self.get_average_return(),
            }
        except Exception as e:
            self.logger.error(f"Error updating metrics: {str(e)}")
            return {}
