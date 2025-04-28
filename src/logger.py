"""Logging configuration module."""

import logging
import sys
from datetime import datetime
import os


def setup_logger(name: str) -> logging.Logger:
    """Set up a logger with the specified name.

    Args:
        name: Name of the logger

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure handlers if they haven't been added yet
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create formatters
        fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        console_formatter = logging.Formatter(fmt)
        file_formatter = logging.Formatter(fmt)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        
        # Create file handler
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(log_dir, f'trading_bot_{timestamp}.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(file_formatter)
        
        # Add handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger

class BotLogger:
    def __init__(self):
        self.log_dir = "logs"
        self._setup_logging()

    def _setup_logging(self):
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

    def log_trade(self, symbol, action, quantity, price, status):
        """Log trade execution"""
        self.logger.info(
            f"Trade Executed - {symbol}: {action} {quantity} shares @ ${price:.2f} - Status: {status}"
        )

    def log_account_update(self, equity, cash, buying_power):
        """Log account information"""
        self.logger.info(
            f"Account Update - Equity: ${equity:.2f}, Cash: ${cash:.2f}, Buying Power: ${buying_power:.2f}"
        )

    def log_error(self, error_message):
        """Log error messages"""
        self.logger.error(error_message)

    def log_warning(self, warning_message):
        """Log warning messages"""
        self.logger.warning(warning_message)

    def log_info(self, info_message):
        """Log general information"""
        self.logger.info(info_message)
