"""Relative Strength Index strategy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from src.indicators import rsi
from src.core.strategy import Strategy


@dataclass
class RSIStrategyConfig:
    """Configuration for the RSI strategy."""

    upper_threshold: float = 70.0
    lower_threshold: float = 30.0
    window: int = 14


class RSIStrategy(Strategy):
    """Mean-reversion strategy based on RSI extremes."""

    def __init__(self, config: RSIStrategyConfig | None = None) -> None:
        super().__init__()
        self.config = config or RSIStrategyConfig()
        self.current_rsi: float | None = None

    def generate_signals(self, bars: pd.DataFrame) -> list[dict[str, Any]]:
        """Generate RSI overbought/oversold signals from OHLC data."""

        if bars.empty or "close" not in bars:
            return []

        rsi_series = rsi(bars["close"], window=self.config.window)
        if rsi_series.empty:
            return []

        self.current_rsi = float(rsi_series.iloc[-1])
        signals: list[dict[str, Any]] = []

        if self.current_rsi <= self.config.lower_threshold:
            signals.append(
                {
                    "side": "long",
                    "price": float(bars["close"].iloc[-1]),
                    "timestamp": bars.index[-1],
                    "indicator": "RSI",
                    "value": self.current_rsi,
                }
            )
        elif self.current_rsi >= self.config.upper_threshold:
            signals.append(
                {
                    "side": "short",
                    "price": float(bars["close"].iloc[-1]),
                    "timestamp": bars.index[-1],
                    "indicator": "RSI",
                    "value": self.current_rsi,
                }
            )
        return signals

    def calculate_position_size(self, price: float, risk_amount: float) -> float:
        """Naive fixed fraction sizing."""

        return max(risk_amount / max(price, 1e-9), 0.0)

    def should_open_position(self, price: float) -> bool:  # noqa: ARG002
        return True

    def should_close_position(self, price: float) -> bool:  # noqa: ARG002
        return True

    def get_stop_loss(self, price: float) -> float:
        return price * 0.97

    def get_take_profit(self, price: float) -> float:
        return price * 1.03
