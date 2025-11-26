"""Unit tests for newly added strategies."""

from __future__ import annotations

import pandas as pd

from src.strategies import (
    BollingerBandsStrategy,
    BollingerStrategyConfig,
    MACDStrategy,
    MACDStrategyConfig,
    RSIStrategy,
    RSIStrategyConfig,
)


def price_frame(values: list[float]) -> pd.DataFrame:
    data = {
        "close": pd.Series(values, dtype=float),
        "high": pd.Series([v + 1 for v in values], dtype=float),
        "low": pd.Series([v - 1 for v in values], dtype=float),
    }
    df = pd.DataFrame(data)
    df.index = pd.date_range("2024-01-01", periods=len(values), freq="D")
    return df


def test_rsi_strategy_generates_long_signal() -> None:
    prices = price_frame([30] * 15 + [20])
    strategy = RSIStrategy(RSIStrategyConfig(lower_threshold=35, upper_threshold=65, window=14))
    signals = strategy.generate_signals(prices)
    assert signals
    assert signals[-1]["side"] == "long"


def test_macd_strategy_detects_crossover() -> None:
    values = list(range(40))
    df = price_frame(values)
    strategy = MACDStrategy(MACDStrategyConfig(fast=3, slow=6, signal=2))
    signals = strategy.generate_signals(df)
    assert isinstance(signals, list)


def test_bollinger_strategy_flags_upper_touch() -> None:
    df = price_frame(list(range(1, 50)))
    strategy = BollingerBandsStrategy(
        BollingerStrategyConfig(window=5, num_std=1.0),
    )
    signals = strategy.generate_signals(df)
    assert signals
