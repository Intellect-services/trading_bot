"""Configuration module for the trading bot."""

import logging
import os
from typing import Any, TypeVar, cast

from dotenv import load_dotenv
from pydantic import (
    BaseModel,
    Field,
    ValidationInfo,
    field_validator,
)

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

T = TypeVar("T", bound="Config")


def get_config(key: str | None = None, default: Any = None) -> Any:
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


def load_config_from_file(file_path: str) -> dict[str, str]:
    """
    Load configuration from a file.

    Args:
        file_path: Path to the configuration file.

    Returns:
        Dictionary of configuration values.
    """
    config = {}
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    return config


def save_config_to_file(config: dict[str, str], file_path: str) -> None:
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
    "ALPACA_API_SECRET": "",
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


def validate_config(config: dict[str, Any]) -> bool:
    """Validate configuration settings."""
    required_keys = [
        "ALPACA_API_KEY",
        "ALPACA_API_SECRET",
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
    alpaca_api_key_id: str = Field(default="")
    alpaca_api_secret_key: str = Field(default="")
    alpaca_base_url: str = "https://paper-api.alpaca.markets"
    alpaca_data_url: str = "https://data.alpaca.markets"

    # Trading Configuration
    trading_enabled: bool = True
    trading_mode: str = "paper"  # paper or live
    trading_symbols: list[str] = Field(
        default_factory=lambda: os.getenv("DEFAULT_TRADING_SYMBOLS", "AAPL,MSFT,GOOGL").split(",")
    )
    trading_timeframe: str = "1D"  # 1m, 5m, 15m, 1h, 1D
    trading_quantity: float = 1.0
    trading_stop_loss: float = 0.02  # 2%
    trading_take_profit: float = 0.04  # 4%

    # Risk Management
    risk_max_position_size: float = 0.1  # 10% of portfolio
    risk_max_daily_loss: float = 0.05  # 5% of portfolio
    risk_max_drawdown: float = 0.10  # 10% of portfolio
    risk_max_leverage: float = 1.0  # No leverage

    # Strategy Configuration
    strategy_symbols: list[str] = Field(
        default_factory=lambda: os.getenv("DEFAULT_STRATEGY_SYMBOLS", "AAPL,MSFT,GOOGL").split(",")
    )
    strategy_timeframe: str = "1D"
    short_window: int = 20
    long_window: int = 50
    lookback_days: int = 100

    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "trading_bot.log"

    # Performance Tracking
    peak_equity: float = 0.0

    @field_validator(
        "trading_stop_loss",
        "trading_take_profit",
        "risk_max_position_size",
        "risk_max_daily_loss",
        "risk_max_drawdown",
    )
    def validate_percentage(cls, v: float) -> float:
        """Validate percentage values."""
        if not 0 <= v <= 1:
            raise ValueError("Value must be between 0 and 1")
        return v

    @field_validator("short_window", "long_window")
    def validate_windows(cls, v: int, info: ValidationInfo) -> int:
        """Validate window sizes."""
        if info.field_name == "long_window":
            short_window = info.data.get("short_window")
            if short_window is not None and v <= short_window:
                raise ValueError("Long window must be greater than short window")
        return v

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        data: Any = self.model_dump()
        return cast("dict[str, Any]", data)


# Create config instance with default values
_default_trading_symbols = os.getenv("DEFAULT_TRADING_SYMBOLS", "AAPL,MSFT,GOOGL").split(",")
_default_strategy_symbols = os.getenv("DEFAULT_STRATEGY_SYMBOLS", "AAPL,MSFT,GOOGL").split(",")

config = Config(
    alpaca_api_key_id=os.getenv("ALPACA_API_KEY", ""),
    alpaca_api_secret_key=os.getenv("ALPACA_API_SECRET", ""),
    trading_symbols=_default_trading_symbols,
    strategy_symbols=_default_strategy_symbols,
    strategy_timeframe="1D",
    short_window=20,
    long_window=50,
    lookback_days=100,
    log_level="INFO",
    log_file="trading_bot.log",
    peak_equity=0.0,
)
