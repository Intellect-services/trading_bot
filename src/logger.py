"""Logging configuration module."""

import logging
import os
from datetime import datetime
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("trading_bot.log")],
)

logger = logging.getLogger(__name__)


def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """Set up a logger with the given name.

    Args:
        name: Optional name for the logger. If None, uses the root logger.

    Returns:
        A configured logger instance.
    """
    if name:
        return logging.getLogger(name)
    return logger


def log_error(message: str, error: Optional[Exception] = None) -> None:
    """Log an error message with optional exception details.

    Args:
        message: The error message to log.
        error: Optional exception object to include in the log.
    """
    if error:
        logger.error(f"{message}: {str(error)}")
    else:
        logger.error(message)


def log_info(message: str) -> None:
    """Log an info message.

    Args:
        message: The info message to log.
    """
    logger.info(message)


def log_warning(message: str) -> None:
    """Log a warning message.

    Args:
        message: The warning message to log.
    """
    logger.warning(message)


def log_debug(message: str) -> None:
    """Log a debug message.

    Args:
        message: The debug message to log.
    """
    logger.debug(message)


class BotLogger:
    def __init__(self) -> None:
        self.log_dir = "logs"
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # Create a new log file for each day
        log_file = os.path.join(
            self.log_dir, f'trading_bot_{datetime.now().strftime("%Y-%m-%d")}.log'
        )

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )

        self.logger = logging.getLogger("TradingBot")

    def log_trade(
        self, symbol: str, action: str, quantity: float, price: float, status: str
    ) -> None:
        """Log trade execution"""
        self.logger.info(
            f"Trade Executed - {symbol}: {action} {quantity} shares @ ${price:.2f} - Status: {status}"
        )

    def log_account_update(self, equity: float, cash: float, buying_power: float) -> None:
        """Log account information"""
        self.logger.info(
            f"Account Update - Equity: ${equity:.2f}, Cash: ${cash:.2f}, Buying Power: ${buying_power:.2f}"
        )

    def log_error(self, error_message: str) -> None:
        """Log error messages"""
        self.logger.error(error_message)

    def log_warning(self, warning_message: str) -> None:
        """Log warning messages"""
        self.logger.warning(warning_message)

    def log_info(self, info_message: str) -> None:
        """Log general information"""
        self.logger.info(info_message)
