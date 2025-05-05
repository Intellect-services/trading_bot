"""
Core trading bot components.
"""

from typing import Any, Optional, Type

from .data_feed import DataFeed
from .portfolio import Portfolio
from .risk_manager import RiskManager
from .strategy import Strategy

AlpacaService: Optional[Type[Any]] = None
TradingBot: Optional[Type[Any]] = None

try:
    from .alpaca_service import AlpacaService
except ImportError:
    pass

try:
    from .bot import TradingBot
except ImportError:
    pass

__all__ = [
    "Strategy",
    "RiskManager",
    "TradingBot",
    "Portfolio",
    "DataFeed",
    "AlpacaService",
]

# Core package initialization
