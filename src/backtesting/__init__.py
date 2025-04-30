"""
Backtesting module for strategy evaluation.
"""

from src.backtesting.metrics import calculate_metrics, format_metrics

from .engine import BacktestEngine, BacktestResult, BacktestTrade

__all__ = [
    "BacktestEngine",
    "BacktestResult",
    "BacktestTrade",
    "calculate_metrics",
    "format_metrics",
]
