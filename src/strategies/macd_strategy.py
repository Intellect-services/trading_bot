"""MACD crossover strategy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd

from src.core.strategy import Strategy
from src.indicators import macd


@dataclass
class MACDStrategyConfig:
    fast: int = 12
    slow: int = 26
    signal: int = 9


class MACDStrategy(Strategy):
    """Trend-following strategy using MACD crossovers."""

    def __init__(self, config: MACDStrategyConfig | None = None) -> None:
        super().__init__()
        self.config = config or MACDStrategyConfig()
        self.previous_macd: float | None = None
        self.previous_signal: float | None = None

    def generate_signals(self, bars: pd.DataFrame) -> list[dict[str, Any]]:
        """Generate MACD crossover signals."""

        if bars.empty or "close" not in bars:
            return []

        macd_df = macd(
            bars["close"],
            fast=self.config.fast,
            slow=self.config.slow,
            signal=self.config.signal,
        )
        if macd_df.empty or macd_df[["macd", "signal"]].isnull().all().all():
            return []

        macd_line = macd_df["macd"].iloc[-1]
        signal_line = macd_df["signal"].iloc[-1]
        prev_macd = macd_df["macd"].iloc[-2] if len(macd_df) > 1 else None
        prev_signal = macd_df["signal"].iloc[-2] if len(macd_df) > 1 else None

        signals: list[dict[str, Any]] = []
        if prev_macd is not None and prev_signal is not None:
            if prev_macd <= prev_signal and macd_line > signal_line:
                signals.append(
                    {
                        "side": "long",
                        "price": float(bars["close"].iloc[-1]),
                        "timestamp": bars.index[-1],
                        "indicator": "MACD",
                        "value": macd_line,
                    }
                )
            elif prev_macd >= prev_signal and macd_line < signal_line:
                signals.append(
                    {
                        "side": "short",
                        "price": float(bars["close"].iloc[-1]),
                        "timestamp": bars.index[-1],
                        "indicator": "MACD",
                        "value": macd_line,
                    }
                )
        return signals

    def calculate_position_size(self, price: float, risk_amount: float) -> float:
        return max(risk_amount / max(price, 1e-9), 0.0)

    def should_open_position(self, price: float) -> bool:  # noqa: ARG002
        return True

    def should_close_position(self, price: float) -> bool:  # noqa: ARG002
        return True

    def get_stop_loss(self, price: float) -> float:
        return price * 0.95

    def get_take_profit(self, price: float) -> float:
        return price * 1.05
