"Bollinger Bands mean-reversion strategy." ""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd

from src.core.strategy import Strategy
from src.indicators import bollinger_bands


@dataclass
class BollingerStrategyConfig:
    window: int = 20
    num_std: float = 2.0


class BollingerBandsStrategy(Strategy):
    """Mean-reversion strategy using Bollinger Band touches."""

    def __init__(self, config: BollingerStrategyConfig | None = None) -> None:
        super().__init__()
        self.config = config or BollingerStrategyConfig()

    def generate_signals(self, bars: pd.DataFrame) -> list[dict[str, Any]]:
        """Generate signals based on price touching upper/lower band."""

        if bars.empty or "close" not in bars:
            return []

        bands = bollinger_bands(
            bars["close"],
            window=self.config.window,
            num_std=self.config.num_std,
        ).dropna()
        if bands.empty:
            return []

        latest_close = float(bars["close"].iloc[-1])
        upper = float(bands["upper"].iloc[-1])
        lower = float(bands["lower"].iloc[-1])

        signals: list[dict[str, Any]] = []
        if latest_close <= lower:
            signals.append(
                {
                    "side": "long",
                    "price": latest_close,
                    "timestamp": bars.index[-1],
                    "indicator": "BOLL",
                    "value": lower,
                }
            )
        elif latest_close >= upper:
            signals.append(
                {
                    "side": "short",
                    "price": latest_close,
                    "timestamp": bars.index[-1],
                    "indicator": "BOLL",
                    "value": upper,
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
        return price * 0.96

    def get_take_profit(self, price: float) -> float:
        return price * 1.04
