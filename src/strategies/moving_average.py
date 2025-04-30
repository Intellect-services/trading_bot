from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from .base import Strategy


class MovingAverageCrossover(Strategy):
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.params = params or {
            "short_window": 20,
            "long_window": 50,
            "signal_threshold": 0.01,
        }

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate moving averages and their crossover signals"""
        if not self.validate_data(data):
            return pd.DataFrame()

        df = data.copy()

        # Calculate moving averages
        df["short_ma"] = df["close"].rolling(window=self.params["short_window"]).mean()
        df["long_ma"] = df["close"].rolling(window=self.params["long_window"]).mean()

        # Calculate the difference between moving averages
        df["ma_diff"] = df["short_ma"] - df["long_ma"]

        # Calculate percentage difference
        df["ma_diff_pct"] = df["ma_diff"] / df["long_ma"]

        return df

    def generate_signals(self, data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Generate trading signals based on moving average crossover"""
        df = self.calculate_indicators(data)
        if df.empty:
            return None

        # Initialize signal column
        df["signal"] = 0

        # Generate signals
        df.loc[df["ma_diff_pct"] > self.params["signal_threshold"], "signal"] = 1  # Buy signal
        df.loc[df["ma_diff_pct"] < -self.params["signal_threshold"], "signal"] = -1  # Sell signal

        # Remove signals during the warmup period
        df.loc[: self.params["long_window"], "signal"] = 0

        return df

    def get_parameters(self) -> Dict[str, float]:
        """Get strategy parameters"""
        return {
            name: float(value)
            for name, value in self.params.items()
            if isinstance(value, (int, float))
        }

    def set_parameters(self, params: Dict[str, Any]) -> None:
        """Update strategy parameters"""
        self.params.update(params)
