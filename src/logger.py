import logging
import os
from datetime import datetime

class BotLogger:
    def __init__(self):
        self.log_dir = 'logs'
        self._setup_logging()

    def _setup_logging(self):
        """Setup logging configuration"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # Create a new log file for each day
        log_file = os.path.join(self.log_dir, f'trading_bot_{datetime.now().strftime("%Y-%m-%d")}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('TradingBot')

    def log_trade(self, symbol, action, quantity, price, status):
        """Log trade execution"""
        self.logger.info(f"Trade Executed - {symbol}: {action} {quantity} shares @ ${price:.2f} - Status: {status}")

    def log_account_update(self, equity, cash, buying_power):
        """Log account information"""
        self.logger.info(f"Account Update - Equity: ${equity:.2f}, Cash: ${cash:.2f}, Buying Power: ${buying_power:.2f}")

    def log_error(self, error_message):
        """Log error messages"""
        self.logger.error(error_message)

    def log_warning(self, warning_message):
        """Log warning messages"""
        self.logger.warning(warning_message)

    def log_info(self, info_message):
        """Log general information"""
        self.logger.info(info_message) 