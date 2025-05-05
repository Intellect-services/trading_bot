"""Configuration module for the trading bot."""

import json
import logging
import os
from datetime import datetime, time
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Type, TypeVar, Union, cast

from dotenv import load_dotenv
from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    ValidationInfo,
    field_validator,
    root_validator,
    validator,
)

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

T = TypeVar("T", bound="Config")


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
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    return config


def save_config_to_file(config: Dict[str, str], file_path: str) -> None:
    """
    Save configuration to a file.

    Args:
        config: Dictionary of configuration values.
        file_path: Path to save the configuration file.
    """
    with open(file_path, "w") as f:
        for key, value in config.items():
            f.write(f"{key}={value}\n")


# Default configuration
DEFAULT_CONFIG = {
    "ALPACA_API_KEY": "",
    "ALPACA_SECRET_KEY": "",
    "ALPACA_PAPER": True,
    "INITIAL_CAPITAL": 100000.0,
    "MAX_POSITION_SIZE": 0.1,
    "STOP_LOSS": 0.02,
    "MAX_DRAWDOWN": 0.20,
    "MAX_LEVERAGE": 2.00,
    "MARKET_OPEN": "09:30",
    "MARKET_CLOSE": "16:00",
    "DEFAULT_SYMBOL": "SPY",
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


class Config(BaseModel):
    """Configuration settings for the trading bot."""

    # API Configuration
    ALPACA_API_KEY: str
    ALPACA_API_SECRET: str
    ALPACA_BASE_URL: str = "https://paper-api.alpaca.markets"
    ALPACA_DATA_URL: str = "https://data.alpaca.markets"

    # Trading Configuration
    TRADING_ENABLED: bool = True
    TRADING_MODE: str = "paper"  # paper or live
    TRADING_SYMBOLS: List[str] = ["AAPL", "MSFT", "GOOGL"]
    TRADING_TIMEFRAME: str = "1D"  # 1m, 5m, 15m, 1h, 1D
    TRADING_QUANTITY: float = 1.0
    TRADING_STOP_LOSS: float = 0.02  # 2%
    TRADING_TAKE_PROFIT: float = 0.04  # 4%

    # Risk Management
    RISK_MAX_POSITION_SIZE: float = 0.1  # 10% of portfolio
    RISK_MAX_DAILY_LOSS: float = 0.05  # 5% of portfolio
    RISK_MAX_DRAWDOWN: float = 0.10  # 10% of portfolio
    RISK_MAX_LEVERAGE: float = 1.0  # No leverage

    # Strategy Configuration
    STRATEGY_SYMBOLS: List[str] = ["AAPL", "MSFT", "GOOGL"]
    STRATEGY_TIMEFRAME: str = "1D"
    SHORT_WINDOW: int = 20
    LONG_WINDOW: int = 50
    LOOKBACK_DAYS: int = 100

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "trading_bot.log"

    # Performance Tracking
    PEAK_EQUITY: float = 0.0

    @field_validator(
        "TRADING_STOP_LOSS",
        "TRADING_TAKE_PROFIT",
        "RISK_MAX_POSITION_SIZE",
        "RISK_MAX_DAILY_LOSS",
        "RISK_MAX_DRAWDOWN",
    )
    def validate_percentage(cls, v: float) -> float:
        """Validate percentage values."""
        if not 0 <= v <= 1:
            raise ValueError("Value must be between 0 and 1")
        return v

    @field_validator("SHORT_WINDOW", "LONG_WINDOW")
    def validate_windows(cls, v: int, info: ValidationInfo) -> int:
        """Validate window sizes."""
        if info.field_name == "LONG_WINDOW":
            short_window = info.data.get("SHORT_WINDOW")
            if short_window is not None and v <= short_window:
                raise ValueError("Long window must be greater than short window")
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return self.model_dump()


# Create config instance with default values
config = Config(
    ALPACA_API_KEY=os.getenv("ALPACA_API_KEY", ""),
    ALPACA_API_SECRET=os.getenv("ALPACA_API_SECRET", ""),
    TRADING_SYMBOLS=["AAPL", "MSFT", "GOOGL"],
    STRATEGY_SYMBOLS=["AAPL", "MSFT", "GOOGL"],
    STRATEGY_TIMEFRAME="1D",
    SHORT_WINDOW=20,
    LONG_WINDOW=50,
    LOOKBACK_DAYS=100,
    LOG_LEVEL="INFO",
    LOG_FILE="trading_bot.log",
    PEAK_EQUITY=0.0,
)
