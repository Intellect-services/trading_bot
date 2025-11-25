"""Portfolio analytics derived from Alpaca free-tier endpoints."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd


class PortfolioAnalytics:
    """Calculate performance metrics from portfolio history."""

    def calculate_metrics(self, history: list[dict[str, Any]]) -> dict[str, float]:
        """Return Sharpe ratio, max drawdown, and cumulative return."""

        if not history:
            return {"sharpe": 0.0, "max_drawdown": 0.0, "cumulative_return": 0.0}

        df = pd.DataFrame(history)
        if df.empty or "equity" not in df:
            return {"sharpe": 0.0, "max_drawdown": 0.0, "cumulative_return": 0.0}

        df = df.sort_values("timestamp")
        df["returns"] = df["equity"].pct_change().fillna(0.0)

        mean_return = df["returns"].mean()
        std_return = df["returns"].std() or 1e-9
        sharpe = (mean_return / std_return) * math.sqrt(252)

        rolling_max = df["equity"].cummax()
        drawdowns = (df["equity"] - rolling_max) / rolling_max
        max_drawdown = float(drawdowns.min())

        cumulative_return = float((df["equity"].iloc[-1] / df["equity"].iloc[0]) - 1.0)

        return {
            "sharpe": float(sharpe),
            "max_drawdown": max_drawdown,
            "cumulative_return": cumulative_return,
        }
