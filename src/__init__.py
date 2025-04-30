"""
Trading Bot Package
"""

from src.core.strategy import Strategy
from src.core.risk_manager import RiskManager
from src.utils.config import Config

__all__ = ["Strategy", "RiskManager", "Config"]

__version__ = '1.0.0'

# This file makes the src directory a Python package
