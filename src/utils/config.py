"""Configuration module for the trading bot."""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from datetime import datetime, time
import json
import logging
from pathlib import Path

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def get_config(key: Optional[str] = None, default: Any = None) -> Any:
    """
    Get configuration value from environment variables.

    Args:
        key: Configuration key to retrieve. If None, returns all config.
        default: Default value if key is not found.

    Returns:
        Configuration value or all config if key is None.
    """
    if key is None:
        return dict(os.environ)
    return os.environ.get(key, default)

def set_config(key: str, value: Any) -> None:
    """
    Set configuration value in environment variables.

    Args:
        key: Configuration key to set.
        value: Value to set.
    """
    os.environ[key] = str(value)

def load_config_from_file(file_path: str) -> Dict[str, str]:
    """
    Load configuration from a file.

    Args:
        file_path: Path to the configuration file.

    Returns:
        Dictionary of configuration values.
    """
    config = {}
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
    return config

def save_config_to_file(config: Dict[str, str], file_path: str) -> None:
    """
    Save configuration to a file.

    Args:
        config: Dictionary of configuration values.
        file_path: Path to save the configuration file.
    """
    with open(file_path, 'w') as f:
        for key, value in config.items():
            f.write(f"{key}={value}\n")

# Default configuration
DEFAULT_CONFIG = {
    'API_KEY': '',
    'SECRET_KEY': '',
    'PAPER': True,
    'INITIAL_BALANCE': 100000.0,
    'MAX_POSITION_SIZE': 0.1,
    'STOP_LOSS': 0.02,
    'MAX_DRAWDOWN': 0.20,
    'MAX_LEVERAGE': 2.00,
    'MARKET_OPEN': '09:30',
    'MARKET_CLOSE': '16:00',
    'DEFAULT_SYMBOL': 'SPY'
}

# Initialize configuration if not exists
for key, value in DEFAULT_CONFIG.items():
    if get_config(key) is None:
        set_config(key, value)

def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration settings."""
    required_keys = [
        "ALPACA_API_KEY",
        "ALPACA_SECRET_KEY",
        "DEFAULT_SYMBOL",
        "MARKET_OPEN",
        "MARKET_CLOSE",
    ]

    for key in required_keys:
        if not config.get(key):
            raise ValueError(f"Missing required configuration: {key}")

    return True

class Config:
    """Configuration class for the trading bot."""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        logger.info("Configuration initialized")
        
        # Alpaca API Configuration
        self.ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
        self.ALPACA_API_SECRET = os.getenv('ALPACA_API_SECRET')
        self.ALPACA_PAPER = os.getenv('ALPACA_PAPER', 'true').lower() == 'true'
        
        # Trading Parameters
        self.INITIAL_BALANCE = float(os.getenv('INITIAL_BALANCE', '100000.0'))
        self.MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', '0.1'))
        self.STOP_LOSS = float(os.getenv('STOP_LOSS', '0.02'))
        self.MAX_DRAWDOWN = float(os.getenv('MAX_DRAWDOWN', '0.20'))
        self.MAX_LEVERAGE = float(os.getenv('MAX_LEVERAGE', '2.00'))
        
        # Default Trading Symbol
        self.DEFAULT_SYMBOL = os.getenv('DEFAULT_SYMBOL', 'SPY')
        
        # Market Hours (EST)
        self.MARKET_OPEN = os.getenv('MARKET_OPEN', '09:30')
        self.MARKET_CLOSE = os.getenv('MARKET_CLOSE', '16:00')
        
        # System Configuration
        self.UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', '60'))
        self.ERROR_RETRY_INTERVAL = int(os.getenv('ERROR_RETRY_INTERVAL', '60'))
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        
        # Flask Configuration
        self.FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
        self.FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')

    @property
    def is_valid(self) -> bool:
        """Check if the configuration is valid."""
        return bool(self.ALPACA_API_KEY and self.ALPACA_API_SECRET)

    def __str__(self) -> str:
        """Return a string representation of the configuration."""
        return f"Config(paper={self.ALPACA_PAPER}, debug={self.FLASK_DEBUG})"

# Create a global instance
config = Config()
