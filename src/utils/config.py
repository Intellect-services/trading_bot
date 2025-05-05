"""Configuration module for the trading bot."""

import json
import logging
import os
from datetime import datetime, time
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Type, TypeVar, Union, cast

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, root_validator, validator

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
    """Configuration for the trading bot."""

    # API Configuration
    ALPACA_API_KEY: str = Field(..., description="Alpaca API key")
    ALPACA_SECRET_KEY: str = Field(..., description="Alpaca API secret key")
    ALPACA_PAPER: bool = Field(True, description="Whether to use paper trading")

    # Risk Management
    RISK_PER_TRADE: float = Field(
        0.02, description="Maximum risk per trade as percentage of portfolio"
    )
    RISK_MAX_DRAWDOWN: float = Field(0.10, description="Maximum drawdown before stopping trading")
    RISK_MAX_LEVERAGE: float = Field(1.0, description="Maximum leverage allowed")
    RISK_MAX_POSITION_SIZE: float = Field(
        0.20, description="Maximum position size as percentage of portfolio"
    )

    # Strategy Settings
    STRATEGY_SYMBOLS: List[str] = Field(["SPY"], description="List of symbols to trade")
    STRATEGY_TIMEFRAME: str = Field("1Min", description="Timeframe for strategy")
    SHORT_WINDOW: int = Field(20, description="Short moving average window")
    LONG_WINDOW: int = Field(50, description="Long moving average window")
    LOOKBACK_DAYS: int = Field(10, description="Number of days to look back for historical data")

    # Portfolio Settings
    INITIAL_CAPITAL: float = Field(100000.0, description="Initial capital for trading")
    PEAK_EQUITY: float = Field(0.0, description="Peak equity value")

    # Logging
    LOG_LEVEL: str = Field("INFO", description="Logging level")
    LOG_FILE: Optional[str] = Field(None, description="Log file path")

    @validator("RISK_PER_TRADE", "RISK_MAX_DRAWDOWN", "RISK_MAX_LEVERAGE", "RISK_MAX_POSITION_SIZE")
    def validate_percentage(cls, v: float) -> float:
        """Validate that percentage values are between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("Percentage values must be between 0 and 1")
        return v

    @root_validator(pre=True)
    def validate_windows(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that short window is less than long window."""
        short_window = values.get("SHORT_WINDOW")
        long_window = values.get("LONG_WINDOW")
        if short_window is not None and long_window is not None:
            if short_window >= long_window:
                raise ValueError("SHORT_WINDOW must be less than LONG_WINDOW")
        return values

    @classmethod
    def from_env(cls: Type[T]) -> T:
        """Create a Config instance from environment variables."""
        return cls(
            ALPACA_API_KEY=os.getenv("ALPACA_API_KEY", ""),
            ALPACA_SECRET_KEY=os.getenv("ALPACA_SECRET_KEY", ""),
            ALPACA_PAPER=os.getenv("ALPACA_PAPER", "true").lower() == "true",
            INITIAL_CAPITAL=float(os.getenv("INITIAL_CAPITAL", "100000.0")),
            RISK_PER_TRADE=float(os.getenv("RISK_PER_TRADE", "0.02")),
            RISK_MAX_DRAWDOWN=float(os.getenv("RISK_MAX_DRAWDOWN", "0.10")),
            RISK_MAX_LEVERAGE=float(os.getenv("RISK_MAX_LEVERAGE", "1.0")),
            RISK_MAX_POSITION_SIZE=float(os.getenv("RISK_MAX_POSITION_SIZE", "0.20")),
            STRATEGY_SYMBOLS=os.getenv("STRATEGY_SYMBOLS", "SPY").split(","),
            STRATEGY_TIMEFRAME=os.getenv("STRATEGY_TIMEFRAME", "1Min"),
            SHORT_WINDOW=int(os.getenv("SHORT_WINDOW", "20")),
            LONG_WINDOW=int(os.getenv("LONG_WINDOW", "50")),
            LOOKBACK_DAYS=int(os.getenv("LOOKBACK_DAYS", "10")),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
            LOG_FILE=os.getenv("LOG_FILE", None),
        )

    @classmethod
    def from_dict(cls: Type[T], config_dict: Dict[str, Any]) -> T:
        """Create a Config instance from a dictionary."""
        return cls(**config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return self.dict()

    def update(self, **kwargs: Any) -> None:
        """Update config values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Invalid config key: {key}")

    def save_to_file(self, filepath: str) -> None:
        """Save config to file."""
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=4)

    @classmethod
    def load_from_file(cls: Type[T], filepath: str) -> T:
        """Load config from file."""
        try:
            with open(filepath, "r") as f:
                config_dict = json.load(f)
            return cls.from_dict(config_dict)
        except FileNotFoundError:
            raise ValueError(f"Config file not found: {filepath}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in config file: {filepath}")
        except Exception as e:
            raise ValueError(f"Error loading config file: {e}")

    class Config:
        """Pydantic config."""

        validate_assignment = True
        extra = "forbid"


# Create a global instance
config = Config.from_env()
