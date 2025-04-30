import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional
from .base import BaseStrategy


class MovingAverageCrossover(BaseStrategy):
    """Moving Average Crossover trading strategy."""

    def __init__(
        self, short_window: int = 20, long_window: int = 50, signal_threshold: float = 0.0
    ) -> None:
        """Initialize the Moving Average Crossover strategy.

        Args:
            short_window: Period for short-term moving average
            long_window: Period for long-term moving average
            signal_threshold: Minimum difference threshold for signal generation
        """
        super().__init__()
        self.short_window = short_window
        self.long_window = long_window
        self.signal_threshold = signal_threshold
        self.warmup_period = max(short_window, long_window)

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate moving averages and their differences.

        Args:
            data: Market data DataFrame with at least 'close' prices

        Returns:
            DataFrame with added indicator columns
        """
        df = data.copy()

        # Calculate moving averages
        df["short_ma"] = df["close"].rolling(window=self.short_window).mean()
        df["long_ma"] = df["close"].rolling(window=self.long_window).mean()

        # Calculate differences
        df["ma_diff"] = df["short_ma"] - df["long_ma"]
        df["ma_diff_pct"] = (df["ma_diff"] / df["long_ma"]) * 100

        return df

    def generate_signals(self, data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Generate trading signals based on moving average crossovers.

        Args:
            data: Market data DataFrame

        Returns:
            DataFrame with signals or None if data is invalid
        """
        if not self.validate_data(data):
            self.logger.error("Invalid input data format")
            return None

        df = self.calculate_indicators(data)

        # Initialize signals column
        df["signal"] = 0.0

        # Generate signals based on MA crossover with threshold
        df.loc[df["ma_diff_pct"] > self.signal_threshold, "signal"] = 1.0  # Buy signal
        df.loc[df["ma_diff_pct"] < -self.signal_threshold, "signal"] = -1.0  # Sell signal

        # Set signals to NaN during warmup period
        df.loc[: self.warmup_period, "signal"] = np.nan

        return df

    def get_parameters(self) -> Dict[str, float]:
        """Get the strategy parameters.

        Returns:
            Dictionary of parameter names and values
        """
        return {
            "short_window": self.short_window,
            "long_window": self.long_window,
            "signal_threshold": self.signal_threshold,
        }

    def set_parameters(self, params: Dict[str, Any]) -> None:
        """Update strategy parameters.

        Args:
            params: Dictionary of parameters to update
        """
        if "short_window" in params:
            self.short_window = int(params["short_window"])
        if "long_window" in params:
            self.long_window = int(params["long_window"])
        if "signal_threshold" in params:
            self.signal_threshold = float(params["signal_threshold"])

        # Update warmup period if windows changed
        self.warmup_period = max(self.short_window, self.long_window)

    def get_required_data(self) -> List[str]:
        """Get the list of required data fields.

        Returns:
            List of required column names
        """
        return ["timestamp", "close"]  # Only need close prices for this strategy
