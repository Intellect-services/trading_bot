"""Backtesting metrics module."""

from typing import Any, Dict, List

import numpy as np
import pandas as pd


def calculate_metrics(
    trades: List[Dict[str, Any]], initial_capital: float
) -> Dict[str, float]:
    """Calculate performance metrics from trade history.

    Args:
        trades: List of trade dictionaries
        initial_capital: Initial capital amount

    Returns:
        Dictionary containing performance metrics
    """
    if not trades:
        return {
            "total_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
        }

    # Convert trades to DataFrame
    df = pd.DataFrame(trades)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("timestamp", inplace=True)

    # Calculate returns
    df["returns"] = df["value"].pct_change()
    total_return = (df["value"].iloc[-1] - initial_capital) / initial_capital

    # Calculate Sharpe ratio
    risk_free_rate = 0.02  # 2% annual risk-free rate
    excess_returns = df["returns"] - risk_free_rate / 252  # Daily risk-free rate
    sharpe_ratio = np.sqrt(252) * excess_returns.mean() / excess_returns.std()

    # Calculate maximum drawdown
    rolling_max = df["value"].expanding().max()
    drawdowns = df["value"] / rolling_max - 1
    max_drawdown = drawdowns.min()

    # Calculate win rate
    profitable_trades = len(df[df["returns"] > 0])
    win_rate = profitable_trades / len(df) if len(df) > 0 else 0.0

    return {
        "total_return": float(total_return),
        "sharpe_ratio": float(sharpe_ratio),
        "max_drawdown": float(max_drawdown),
        "win_rate": float(win_rate),
    }


def format_metrics(metrics: Dict[str, float]) -> Dict[str, str]:
    """Format metrics for display"""
    formatted = {}
    for key, value in metrics.items():
        if key in [
            "total_return",
            "annualized_return",
            "volatility",
            "max_drawdown",
            "win_rate",
        ]:
            formatted[key] = f"{value:.2%}"
        elif key in ["sharpe_ratio"]:
            formatted[key] = f"{value:.2f}"
        else:
            formatted[key] = str(value)
    return formatted
