"""Configuration module for the trading bot."""

import json
import logging
import os
from datetime import datetime, time
from pathlib import Path
from typing import Any, Dict, Optional, Union

from dotenv import load_dotenv

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
    "API_KEY": "",
    "SECRET_KEY": "",
    "PAPER": True,
    "INITIAL_BALANCE": 100000.0,
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


class Config:
    """Configuration class for the trading bot."""

    def __init__(self, config_data: Dict[str, Any]) -> None:
        """Initialize configuration.

        Args:
            config_data: Configuration data dictionary
        """
        self.ALPACA_API_KEY = config_data.get("ALPACA_API_KEY", "")
        self.ALPACA_SECRET_KEY = config_data.get("ALPACA_SECRET_KEY", "")
        self.ALPACA_PAPER = config_data.get("ALPACA_PAPER", True)
        self.INITIAL_CAPITAL = float(config_data.get("INITIAL_CAPITAL", 100000.0))
        self.RISK_MAX_POSITION_SIZE = float(
            config_data.get("RISK_MAX_POSITION_SIZE", 0.1)
        )
        self.RISK_STOP_LOSS_PCT = float(config_data.get("RISK_STOP_LOSS_PCT", 0.02))
        self.RISK_MAX_DRAWDOWN = float(config_data.get("RISK_MAX_DRAWDOWN", 0.1))
        self.RISK_MAX_LEVERAGE = float(config_data.get("RISK_MAX_LEVERAGE", 1.0))
        self.RISK_PER_TRADE = float(config_data.get("RISK_PER_TRADE", 0.01))

    @classmethod
    def from_file(cls, config_file: str) -> "Config":
        """Create Config instance from file.

        Args:
            config_file: Path to configuration file

        Returns:
            Config instance
        """
        with open(config_file, "r") as f:
            config_data = json.load(f)
        return cls(config_data)

    @classmethod
    def from_dict(cls, config_data: Dict[str, Any]) -> "Config":
        """Create Config instance from dictionary.

        Args:
            config_data: Configuration data dictionary

        Returns:
            Config instance
        """
        return cls(config_data)

    @property
    def is_valid(self) -> bool:
        """Check if configuration is valid.

        Returns:
            True if configuration is valid, False otherwise
        """
        return bool(self.ALPACA_API_KEY and self.ALPACA_SECRET_KEY)

    def __str__(self) -> str:
        """Return a string representation of the configuration."""
        return f"Config(paper={self.ALPACA_PAPER})"


# Create a global instance
config = Config(dict(os.environ))
