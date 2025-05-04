"""
Core trading bot components.
"""

from .data_feed import DataFeed
from .portfolio import Portfolio
from .risk_manager import RiskManager
from .strategy import Strategy

try:
    from .alpaca_service import AlpacaService
except ImportError:
    AlpacaService = None

try:
    from .bot import TradingBot
except ImportError:
    TradingBot = None

__all__ = [
    "Strategy",
    "RiskManager",
    "TradingBot",
    "Portfolio",
    "DataFeed",
    "AlpacaService",
]

# Core package initialization
