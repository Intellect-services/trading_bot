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
    """Configuration manager for the trading bot."""
    
    def __init__(self) -> None:
        """Initialize configuration."""
        self.config_data: Dict[str, Any] = {}
        self.load_config()
        
    def load_config(self) -> None:
        """Load configuration from environment variables and .env file."""
        # Load .env file
        load_dotenv()
        
        # Set default values
        self.config_data = {
            # API Configuration
            'alpaca_api_key': os.getenv('ALPACA_API_KEY', ''),
            'alpaca_secret_key': os.getenv('ALPACA_SECRET_KEY', ''),
            'ALPACA_API_KEY': os.getenv('ALPACA_API_KEY', ''),
            'ALPACA_SECRET_KEY': os.getenv('ALPACA_SECRET_KEY', ''),
            'API_KEY': os.getenv('ALPACA_API_KEY', ''),
            'SECRET_KEY': os.getenv('ALPACA_SECRET_KEY', ''),
            
            # Trading Mode
            'paper_trading': os.getenv('PAPER_TRADING', 'True').lower() == 'true',
            'PAPER_TRADING': os.getenv('PAPER_TRADING', 'True').lower() == 'true',
            'PAPER': os.getenv('PAPER_TRADING', 'True').lower() == 'true',
            
            # Account Settings
            'initial_balance': float(os.getenv('INITIAL_BALANCE', '10000.0')),
            'INITIAL_BALANCE': float(os.getenv('INITIAL_BALANCE', '10000.0')),
            
            # Risk Management
            'max_position_size': float(os.getenv('MAX_POSITION_SIZE', '0.1')),
            'stop_loss': float(os.getenv('STOP_LOSS', '0.02')),
            'max_drawdown': float(os.getenv('MAX_DRAWDOWN', '0.20')),
            'max_leverage': float(os.getenv('MAX_LEVERAGE', '2.00')),
            'RISK_MAX_POSITION_SIZE': float(os.getenv('MAX_POSITION_SIZE', '0.1')),
            'RISK_STOP_LOSS_PCT': float(os.getenv('STOP_LOSS', '0.02')),
            'RISK_MAX_DRAWDOWN': float(os.getenv('MAX_DRAWDOWN', '0.20')),
            'RISK_MAX_LEVERAGE': float(os.getenv('MAX_LEVERAGE', '2.00')),
            
            # Trading Parameters
            'DEFAULT_SYMBOL': os.getenv('DEFAULT_SYMBOL', 'AAPL'),
            'DEFAULT_TIMEFRAME': os.getenv('DEFAULT_TIMEFRAME', '1D'),
            
            # Market Hours
            'MARKET_OPEN': os.getenv('MARKET_OPEN', '09:30'),
            'MARKET_CLOSE': os.getenv('MARKET_CLOSE', '16:00'),
            
            # System Configuration
            'UPDATE_INTERVAL': int(os.getenv('UPDATE_INTERVAL', '60')),
            'ERROR_RETRY_INTERVAL': int(os.getenv('ERROR_RETRY_INTERVAL', '60')),
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
        }
        
        logger.info("Configuration initialized")
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config_data.get(key, default)
        
    def __getattr__(self, name: str) -> Any:
        """Allow attribute access to config values."""
        if name in self.config_data:
            return self.config_data[name]
        # Try uppercase version
        if name.upper() in self.config_data:
            return self.config_data[name.upper()]
        raise AttributeError(f"'Config' object has no attribute '{name}'")

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary format."""
        return self.config_data.copy()

    @classmethod
    def get_trading_params(cls) -> Dict[str, float]:
        """Get trading parameters."""
        config = cls()
        return {
            "max_position_size": config.get('RISK_MAX_POSITION_SIZE', 0.1),
            "risk_per_trade": config.get('RISK_PER_TRADE', 0.01),
            "stop_loss_percent": config.get('RISK_STOP_LOSS_PCT', 0.02),
        }

    @classmethod
    def get_backtest_params(cls) -> Dict[str, Any]:
        """Get backtesting parameters."""
        config = cls()
        return {
            "start_date": config.get('BACKTEST_START_DATE', '2020-01-01'),
            "end_date": config.get('BACKTEST_END_DATE', '2023-12-31'),
            "initial_capital": str(config.get('INITIAL_BALANCE', 10000.0)),
        }

    @classmethod
    def get_risk_params(cls) -> Dict[str, float]:
        """Get risk management parameters."""
        config = cls()
        return {
            "max_drawdown": config.get('RISK_MAX_DRAWDOWN', 0.2),
            "risk_per_trade": config.get('RISK_PER_TRADE', 0.01),
        }
