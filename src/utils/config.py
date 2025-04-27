"""Configuration module for the trading bot."""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from datetime import datetime, time
import json

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


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
    """Configuration class for managing trading parameters."""

    def __init__(self, config_file: str = "config.json"):
        """Initialize configuration.

        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config_data: Dict[str, Any] = {}
        self.load_config()

        # Trading settings
        self.INITIAL_BALANCE: float = self.config_data.get("initial_balance", 10000.0)
        self.PAPER_TRADING: bool = self.config_data.get("paper_trading", True)
        self.COMMISSION: float = self.config_data.get("commission", 0.001)
        self.SLIPPAGE: float = self.config_data.get("slippage", 0.0005)

        # API keys
        self.ALPACA_API_KEY: str = self.config_data.get("alpaca_api_key", os.getenv("ALPACA_API_KEY", ""))
        self.ALPACA_SECRET_KEY: str = self.config_data.get("alpaca_secret_key", os.getenv("ALPACA_SECRET_KEY", ""))

        # Risk management
        self.RISK_FREE_RATE: float = self.config_data.get("risk_free_rate", 0.02)
        self.RISK_MAX_POSITION_SIZE: float = self.config_data.get("risk_max_position_size", 0.1)
        self.RISK_STOP_LOSS_PCT: float = self.config_data.get("risk_stop_loss_pct", 0.02)
        self.RISK_MAX_DRAWDOWN: float = self.config_data.get("risk_max_drawdown", 0.1)
        self.RISK_PER_TRADE: float = self.config_data.get("risk_per_trade", 0.01)
        self.RISK_MAX_LEVERAGE: float = self.config_data.get("risk_max_leverage", 2.0)

        # Strategy parameters
        self.STRATEGY_PARAMS: Dict[str, Any] = self.config_data.get("strategy_params", {})

        # Market Configuration
        self.MARKET_OPEN = time(9, 30)  # 9:30 AM ET
        self.MARKET_CLOSE = time(16, 0)  # 4:00 PM ET
        self.DEFAULT_SYMBOL = self.config_data.get("default_symbol", "SPY")
        self.DEFAULT_TIMEFRAME = self.config_data.get("default_timeframe", "1Min")

        # Backtesting Configuration
        self.BACKTEST_START_DATE = datetime.strptime(
            self.config_data.get("backtest_start_date", "2020-01-01"),
            '%Y-%m-%d'
        )
        self.BACKTEST_END_DATE = datetime.strptime(
            self.config_data.get("backtest_end_date", "2020-12-31"),
            '%Y-%m-%d'
        )

        logger.info("Configuration initialized")

    def load_config(self) -> None:
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    self.config_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading config file: {str(e)}")
            self.config_data = {}

    def to_dict(self) -> Dict[str, str]:
        """Convert config to dictionary format.

        Returns:
            Dictionary containing configuration values
        """
        return {
            'ALPACA_API_KEY': self.ALPACA_API_KEY,
            'ALPACA_SECRET_KEY': self.ALPACA_SECRET_KEY,
            'INITIAL_BALANCE': str(self.INITIAL_BALANCE),
            'PAPER_TRADING': str(self.PAPER_TRADING),
            'COMMISSION': str(self.COMMISSION),
            'SLIPPAGE': str(self.SLIPPAGE),
            'RISK_FREE_RATE': str(self.RISK_FREE_RATE),
            'RISK_MAX_POSITION_SIZE': str(self.RISK_MAX_POSITION_SIZE),
            'RISK_STOP_LOSS_PCT': str(self.RISK_STOP_LOSS_PCT),
            'RISK_MAX_DRAWDOWN': str(self.RISK_MAX_DRAWDOWN),
            'RISK_PER_TRADE': str(self.RISK_PER_TRADE),
            'RISK_MAX_LEVERAGE': str(self.RISK_MAX_LEVERAGE),
            'DEFAULT_SYMBOL': self.DEFAULT_SYMBOL,
            'DEFAULT_TIMEFRAME': self.DEFAULT_TIMEFRAME,
            'BACKTEST_START_DATE': self.BACKTEST_START_DATE.strftime('%Y-%m-%d'),
            'BACKTEST_END_DATE': self.BACKTEST_END_DATE.strftime('%Y-%m-%d'),
        }

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.

        Args:
            key: The configuration key (e.g., 'risk.max_drawdown')
            default: Default value if key is not found

        Returns:
            The configuration value
        """
        try:
            # Handle nested keys (e.g., 'risk.max_drawdown')
            parts = key.split(".")
            if len(parts) == 2:
                section, param = parts
                attr_name = f"{section.upper()}_{param.upper()}"
            else:
                attr_name = key.upper()

            return getattr(cls, attr_name, default)
        except (AttributeError, ValueError):
            return default

    @classmethod
    def get_trading_params(cls) -> Dict[str, float]:
        """Get trading parameters."""
        return {
            "max_position_size": cls.RISK_MAX_POSITION_SIZE,
            "risk_per_trade": cls.RISK_PER_TRADE,
            "stop_loss_percent": cls.RISK_STOP_LOSS_PCT,
        }

    @classmethod
    def get_backtest_params(cls) -> Dict[str, Any]:
        """Get backtesting parameters."""
        return {
            "start_date": cls.BACKTEST_START_DATE.strftime('%Y-%m-%d'),
            "end_date": cls.BACKTEST_END_DATE.strftime('%Y-%m-%d'),
            "initial_capital": str(cls.INITIAL_BALANCE),
        }

    @classmethod
    def get_risk_params(cls) -> Dict[str, float]:
        """Get risk management parameters."""
        return {
            "max_drawdown": cls.RISK_MAX_DRAWDOWN,
            "risk_per_trade": cls.RISK_PER_TRADE,
        }
