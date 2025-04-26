"""Configuration module for the trading bot."""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv


def get_config() -> Dict[str, Any]:
    """Get configuration settings."""
    load_dotenv()

    config = {
        # API Configuration
        'ALPACA_API_KEY': os.getenv('ALPACA_API_KEY'),
        'ALPACA_SECRET_KEY': os.getenv('ALPACA_SECRET_KEY'),

        # Trading Parameters
        'DEFAULT_SYMBOL': os.getenv('DEFAULT_SYMBOL', 'AAPL'),
        'DEFAULT_QUANTITY': float(os.getenv('DEFAULT_QUANTITY', '1')),
        'DEFAULT_TIMEFRAME': os.getenv('DEFAULT_TIMEFRAME', '1D'),

        # Risk Management
        'MAX_POSITION_SIZE': float(os.getenv('MAX_POSITION_SIZE', '1000')),
        'STOP_LOSS_PERCENTAGE': float(os.getenv('STOP_LOSS_PERCENTAGE', '0.02')),
        'TAKE_PROFIT_PERCENTAGE': float(os.getenv('TAKE_PROFIT_PERCENTAGE', '0.05')),

        # Trading Hours
        'MARKET_OPEN': os.getenv('MARKET_OPEN', '09:30'),
        'MARKET_CLOSE': os.getenv('MARKET_CLOSE', '16:00'),

        # Data Storage
        'DATA_DIR': os.getenv('DATA_DIR', 'data'),
        'HISTORICAL_DATA_FILE': os.path.join(
            os.getenv('DATA_DIR', 'data'),
            os.getenv('HISTORICAL_DATA_FILE', 'historical_data.csv')
        ),

        # System Configuration
        'UPDATE_INTERVAL': int(os.getenv('UPDATE_INTERVAL', '60')),
        'ERROR_RETRY_INTERVAL': int(os.getenv('ERROR_RETRY_INTERVAL', '60')),
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),

        # Backtesting Configuration
        'BACKTEST_START_DATE': os.getenv('BACKTEST_START_DATE', '2020-01-01'),
        'BACKTEST_END_DATE': os.getenv('BACKTEST_END_DATE', '2023-12-31'),
        'BACKTEST_INITIAL_CAPITAL': float(os.getenv('BACKTEST_INITIAL_CAPITAL', '100000')),
        'BACKTEST_COMMISSION': float(os.getenv('BACKTEST_COMMISSION', '0.001')),
    }

    return config


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration settings."""
    required_keys = [
        'ALPACA_API_KEY',
        'ALPACA_SECRET_KEY',
        'DEFAULT_SYMBOL',
        'MARKET_OPEN',
        'MARKET_CLOSE'
    ]

    for key in required_keys:
        if not config.get(key):
            raise ValueError(f"Missing required configuration: {key}")

    return True


class Config:
    """Configuration class for the trading bot."""

    # API Configuration
    ALPACA_API_KEY: str = ""
    ALPACA_SECRET_KEY: str = ""
    ALPACA_PAPER: bool = True

    # Market Configuration
    DEFAULT_SYMBOL: str = "SPY"
    DEFAULT_TIMEFRAME: str = "1Min"
    MARKET_OPEN: str = "09:30"
    MARKET_CLOSE: str = "16:00"

    # Trading Configuration
    MAX_POSITION_SIZE: float = 10000.0
    RISK_PER_TRADE: float = 0.02
    STOP_LOSS_PERCENT: float = 0.02
    RISK_MAX_DRAWDOWN: float = 0.10
    RISK_MAX_LEVERAGE: float = 1.0
    RISK_STOP_LOSS: float = 0.02
    RISK_TAKE_PROFIT: float = 0.04

    # Backtesting Configuration
    BACKTEST_START_DATE: str = "2023-01-01"
    BACKTEST_END_DATE: str = "2023-12-31"
    INITIAL_CAPITAL: float = 100000.0

    def __init__(self) -> None:
        """Initialize configuration with environment variables."""
        self.load_env_vars()

    def load_env_vars(self) -> None:
        """Load configuration from environment variables."""
        load_dotenv()

        # Load API keys from environment
        self.ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
        self.ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")
        self.ALPACA_PAPER = bool(os.getenv("ALPACA_PAPER", "True"))

    def validate(self) -> bool:
        """Validate the configuration."""
        if not self.ALPACA_API_KEY or not self.ALPACA_SECRET_KEY:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary format."""
        return {
            "alpaca": {
                "api_key": self.ALPACA_API_KEY,
                "secret_key": self.ALPACA_SECRET_KEY,
                "paper": self.ALPACA_PAPER
            },
            "market": {
                "symbol": self.DEFAULT_SYMBOL,
                "timeframe": self.DEFAULT_TIMEFRAME,
                "market_open": self.MARKET_OPEN,
                "market_close": self.MARKET_CLOSE
            },
            "trading": {
                "max_position_size": self.MAX_POSITION_SIZE,
                "risk_per_trade": self.RISK_PER_TRADE,
                "stop_loss_percent": self.STOP_LOSS_PERCENT
            },
            "backtest": {
                "start_date": self.BACKTEST_START_DATE,
                "end_date": self.BACKTEST_END_DATE,
                "initial_capital": self.INITIAL_CAPITAL
            },
            "risk": {
                "max_drawdown": self.RISK_MAX_DRAWDOWN,
                "max_leverage": self.RISK_MAX_LEVERAGE,
                "stop_loss": self.RISK_STOP_LOSS,
                "take_profit": self.RISK_TAKE_PROFIT,
                "risk_per_trade": self.RISK_PER_TRADE,
                "max_position_size": self.MAX_POSITION_SIZE,
                "initial_capital": self.INITIAL_CAPITAL
            }
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
            parts = key.split('.')
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
            'max_position_size': cls.MAX_POSITION_SIZE,
            'risk_per_trade': cls.RISK_PER_TRADE,
            'stop_loss_percent': cls.STOP_LOSS_PERCENT
        }

    @classmethod
    def get_backtest_params(cls) -> Dict[str, str]:
        """Get backtesting parameters."""
        return {
            'start_date': cls.BACKTEST_START_DATE,
            'end_date': cls.BACKTEST_END_DATE,
            'initial_capital': str(cls.INITIAL_CAPITAL)
        }

    @classmethod
    def get_risk_params(cls) -> Dict[str, float]:
        """Get risk management parameters."""
        return {
            'max_drawdown': cls.RISK_MAX_DRAWDOWN,
            'max_leverage': cls.RISK_MAX_LEVERAGE,
            'stop_loss': cls.RISK_STOP_LOSS,
            'take_profit': cls.RISK_TAKE_PROFIT,
            'risk_per_trade': cls.RISK_PER_TRADE
        } 