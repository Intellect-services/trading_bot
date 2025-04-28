"""Configuration module for the trading bot."""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from datetime import datetime, time
import json
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_config() -> Dict[str, Any]:
    """Get configuration settings."""
    load_dotenv()

    config = {
        # API Configuration
        "ALPACA_API_KEY": os.getenv("ALPACA_API_KEY"),
        "ALPACA_SECRET_KEY": os.getenv("ALPACA_SECRET_KEY"),
        # Trading Parameters
        "DEFAULT_SYMBOL": os.getenv("DEFAULT_SYMBOL", "AAPL"),
        "DEFAULT_QUANTITY": float(os.getenv("DEFAULT_QUANTITY", "1")),
        "DEFAULT_TIMEFRAME": os.getenv("DEFAULT_TIMEFRAME", "1D"),
        # Risk Management
        "MAX_POSITION_SIZE": float(os.getenv("MAX_POSITION_SIZE", "1000")),
        "STOP_LOSS_PERCENTAGE": float(os.getenv("STOP_LOSS_PERCENTAGE", "0.02")),
        "TAKE_PROFIT_PERCENTAGE": float(os.getenv("TAKE_PROFIT_PERCENTAGE", "0.05")),
        # Trading Hours
        "MARKET_OPEN": os.getenv("MARKET_OPEN", "09:30"),
        "MARKET_CLOSE": os.getenv("MARKET_CLOSE", "16:00"),
        # Data Storage
        "DATA_DIR": os.getenv("DATA_DIR", "data"),
        "HISTORICAL_DATA_FILE": os.path.join(
            os.getenv("DATA_DIR", "data"),
            os.getenv("HISTORICAL_DATA_FILE", "historical_data.csv"),
        ),
        # System Configuration
        "UPDATE_INTERVAL": int(os.getenv("UPDATE_INTERVAL", "60")),
        "ERROR_RETRY_INTERVAL": int(os.getenv("ERROR_RETRY_INTERVAL", "60")),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        # Backtesting Configuration
        "BACKTEST_START_DATE": os.getenv("BACKTEST_START_DATE", "2020-01-01"),
        "BACKTEST_END_DATE": os.getenv("BACKTEST_END_DATE", "2023-12-31"),
        "BACKTEST_INITIAL_CAPITAL": float(
            os.getenv("BACKTEST_INITIAL_CAPITAL", "100000")
        ),
        "BACKTEST_COMMISSION": float(os.getenv("BACKTEST_COMMISSION", "0.001")),
    }

    return config


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
    
    def __init__(self):
        """Initialize configuration."""
        self.config_data = {}
        self.load_config()
        
    def load_config(self):
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
        
    def get(self, key, default=None):
        """Get a configuration value."""
        return self.config_data.get(key, default)
        
    def __getattr__(self, name):
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
