from typing import Dict, Any, Optional, List, Union
import pandas as pd
from datetime import datetime

from src.core.strategy import Strategy
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class MovingAverageStrategy(Strategy):
    """Moving average crossover strategy."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize moving average strategy.

        Args:
            config: Strategy configuration with parameters:
                - short_window: Short moving average window (default: 20)
                - long_window: Long moving average window (default: 50)
                - symbols: List of symbols to trade
        """
        super().__init__(config)
        self.short_window = self.config.get("short_window", 20)
        self.long_window = self.config.get("long_window", 50)
        self.symbols = self.config.get("symbols", [])
        self.price_history: Dict[str, List[float]] = {}

    def update_state(
        self, data: Union[pd.Series[Any], Dict[str, Any]], timestamp: datetime
    ) -> None:
        """Update the strategy state with new market data."""
        if isinstance(data, pd.Series):
            data_dict = data.to_dict()
        else:
            data_dict = data

        # Update price history for each symbol
        for symbol in self.symbols:
            if symbol in data_dict:
                price = float(data_dict[symbol])
                if symbol not in self.price_history:
                    self.price_history[symbol] = []
                self.price_history[symbol].append(price)
                # Keep only the necessary history
                if len(self.price_history[symbol]) > self.long_window:
                    self.price_history[symbol] = self.price_history[symbol][-self.long_window :]

        # Update the base state
        super().update_state(data_dict, timestamp)

    def generate_signals(self) -> Dict[str, float]:
        """Generate trading signals based on moving average crossovers."""
        signals: Dict[str, float] = {}

        for symbol in self.symbols:
            if (
                symbol not in self.price_history
                or len(self.price_history[symbol]) < self.long_window
            ):
                signals[symbol] = 0.0
                continue

            prices = pd.Series(self.price_history[symbol])
            short_ma = prices.rolling(window=self.short_window).mean()
            long_ma = prices.rolling(window=self.long_window).mean()

            if short_ma.iloc[-1] > long_ma.iloc[-1] and short_ma.iloc[-2] <= long_ma.iloc[-2]:
                signals[symbol] = 1.0  # Buy signal
            elif short_ma.iloc[-1] < long_ma.iloc[-1] and short_ma.iloc[-2] >= long_ma.iloc[-2]:
                signals[symbol] = -1.0  # Sell signal
            else:
                signals[symbol] = 0.0  # No signal

        return signals

    def reset(self) -> None:
        """Reset the strategy state and price history."""
        super().reset()
        self.price_history = {}
