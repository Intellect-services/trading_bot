"""
Core trading bot components.
"""

import contextlib
from typing import Any, Optional

from .data_feed import DataFeed
from .portfolio import Portfolio
from .risk_manager import RiskManager
from .strategy import Strategy

AlpacaService: type[Any] | None = None
TradingBot: type[Any] | None = None

with contextlib.suppress(ImportError):
    from .alpaca_service import AlpacaService

try:
    from .bot import TradingBot
except ImportError:
    TradingBot = None

__all__ = [
    "AlpacaService",
    "DataFeed",
    "Portfolio",
    "RiskManager",
    "Strategy",
    "TradingBot",
]

# Core package initialization
