"""Logging configuration for the trading bot."""

import logging
import sys
from typing import Optional, Dict, Any
from datetime import datetime
import os


def setup_logger(
    name: str, level: Optional[int] = None, log_file: Optional[str] = None
) -> logging.Logger:
    """Set up a logger with the specified name and level.

    Args:
        name: Name of the logger
        level: Logging level (default: logging.INFO)
        log_file: Path to log file (optional)

    Returns:
        Configured logger instance
    """
    if level is None:
        level = logging.INFO

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create formatters
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create and configure console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create and configure file handler if log file is specified
    if log_file:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


class BotLogger:
    """Specialized logger for the trading bot."""

    def __init__(self, name: str, log_file: Optional[str] = None) -> None:
        """Initialize the bot logger.

        Args:
            name: Name of the logger
            log_file: Path to log file (optional)
        """
        self.logger = setup_logger(name, log_file=log_file)

    def log_trade(
        self, symbol: str, side: str, quantity: float, price: float, status: str
    ) -> None:
        """Log trade execution details.

        Args:
            symbol: Trading symbol
            side: Trade side ('buy' or 'sell')
            quantity: Trade quantity
            price: Trade price
            status: Trade status
        """
        self.logger.info(
            "Trade executed - Symbol: %s, Side: %s, Qty: %.2f, Price: $%.2f, Status: %s",
            symbol,
            side,
            quantity,
            price,
            status,
        )

    def log_account_update(
        self, equity: float, cash: float, buying_power: float
    ) -> None:
        """Log account balance updates.

        Args:
            equity: Total account equity
            cash: Available cash
            buying_power: Available buying power
        """
        self.logger.info(
            "Account update - Equity: $%.2f, Cash: $%.2f, Buying Power: $%.2f",
            equity,
            cash,
            buying_power,
        )

    def log_position_update(
        self, symbol: str, quantity: float, current_price: float, market_value: float
    ) -> None:
        """Log position updates.

        Args:
            symbol: Trading symbol
            quantity: Position quantity
            current_price: Current price
            market_value: Position market value
        """
        self.logger.info(
            "Position update - Symbol: %s, Qty: %.2f, Price: $%.2f, Value: $%.2f",
            symbol,
            quantity,
            current_price,
            market_value,
        )

    def log_error(self, message: str, error: Optional[Exception] = None) -> None:
        """Log error messages.

        Args:
            message: Error message
            error: Exception object (optional)
        """
        if error:
            self.logger.error("%s: %s", message, str(error))
        else:
            self.logger.error(message)

    def log_info(self, message: str, *args: Any) -> None:
        """Log informational messages.

        Args:
            message: Log message
            *args: Additional arguments for message formatting
        """
        self.logger.info(message, *args)

    def log_warning(self, message: str, *args: Any) -> None:
        """Log warning messages.

        Args:
            message: Warning message
            *args: Additional arguments for message formatting
        """
        self.logger.warning(message, *args)

    def log_debug(self, message: str, *args: Any) -> None:
        """Log debug messages.

        Args:
            message: Debug message
            *args: Additional arguments for message formatting
        """
        self.logger.debug(message, *args)
