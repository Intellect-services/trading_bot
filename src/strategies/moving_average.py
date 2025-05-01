"""Moving average crossover strategy."""

from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from pandas import DataFrame, Series

from src.core.strategy import Strategy
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class MovingAverageCrossover(Strategy):
    """Moving average crossover strategy."""

    def __init__(
        self,
        config: dict[str, Any],
        short_window: int = 20,
        long_window: int = 50,
        rsi_period: int = 14,
        rsi_overbought: float = 70.0,
        rsi_oversold: float = 30.0,
    ):
        """Initialize the strategy.

        Args:
            config: Strategy configuration
            short_window: Short-term moving average window
            long_window: Long-term moving average window
            rsi_period: RSI calculation period
            rsi_overbought: RSI overbought threshold
            rsi_oversold: RSI oversold threshold
        """
        # Convert dictionary to Config instance
        config_instance = Config.from_dict(config)
        super().__init__(config_instance)
        self.short_window = short_window
        self.long_window = long_window
        self.lookback = max(short_window, long_window) * 2  # Ensure enough data for calculations
        self.signal_threshold = float(config.get("signal_threshold", 0.0))
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.price_history: list[float] = []
        self.current_position = 0

    def calculate_signals(self, data: DataFrame) -> DataFrame:
        """Calculate trading signals.

        Args:
            data: Market data

        Returns:
            DataFrame: Signals
        """
        signals = pd.DataFrame(index=data.index)
        signals["signal"] = 0.0

        # Calculate moving averages
        signals["short_mavg"] = data["close"].rolling(window=self.short_window).mean()
        signals["long_mavg"] = data["close"].rolling(window=self.long_window).mean()

        # Generate signals
        signals["signal"][self.long_window :] = np.where(
            signals["short_mavg"][self.long_window :] > signals["long_mavg"][self.long_window :],
            1.0,
            0.0,
        )

        # Generate trading orders
        signals["positions"] = signals["signal"].diff()

        return signals

    def update_state(self, data: Series[Any] | dict[str, float | str], timestamp: datetime) -> None:
        """Update strategy state with new market data."""
        if isinstance(data, dict):
            self.price_history.append(float(data["close"]))
            if len(self.price_history) > self.lookback:
                self.price_history = self.price_history[-self.lookback :]
        else:
            self.price_history.append(float(data["close"]))
            if len(self.price_history) > self.lookback:
                self.price_history = self.price_history[-self.lookback :]

    def generate_signals(self) -> dict[str, Any]:
        """Generate trading signals based on moving average crossover."""
        if len(self.price_history) < self.lookback:
            return {"signal": "HOLD", "price": self.price_history[-1]}

        short_ma = sum(self.price_history[-self.short_window :]) / self.short_window
        long_ma = sum(self.price_history[-self.long_window :]) / self.long_window

        signals = {"signal": "HOLD", "price": self.price_history[-1]}

        if short_ma > long_ma and self.current_position <= 0:
            signals["signal"] = "BUY"
        elif short_ma < long_ma and self.current_position >= 0:
            signals["signal"] = "SELL"

        return signals

    def reset(self) -> None:
        """Reset the strategy state and price history."""
        super().reset()
        self.price_history = []
        self.current_position = 0
