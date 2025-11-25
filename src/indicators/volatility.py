"""Volatility indicators."""

from __future__ import annotations

import pandas as pd

from .trend import sma


def bollinger_bands(
    series: pd.Series,
    window: int = 20,
    num_std: float = 2.0,
) -> pd.DataFrame:
    """Return Bollinger Bands (middle, upper, lower)."""

    mid = sma(series, window)
    std = series.rolling(window=window, min_periods=window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return pd.DataFrame({"middle": mid, "upper": upper, "lower": lower})


def average_true_range(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    window: int = 14,
) -> pd.Series:
    """Average True Range (ATR)."""

    tr_components = pd.concat(
        [
            (high - low).abs(),
            (high - close.shift()).abs(),
            (low - close.shift()).abs(),
        ],
        axis=1,
    )
    true_range = tr_components.max(axis=1)
    return true_range.rolling(window=window, min_periods=window).mean()


def keltner_channels(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    ema_window: int = 20,
    atr_window: int = 10,
    multiplier: float = 2.0,
) -> pd.DataFrame:
    """Keltner Channels using EMA and ATR."""

    typical_price = (high + low + close) / 3
    ema_tp = typical_price.ewm(span=ema_window, adjust=False).mean()
    atr = average_true_range(high, low, close, window=atr_window)
    upper = ema_tp + multiplier * atr
    lower = ema_tp - multiplier * atr
    return pd.DataFrame({"middle": ema_tp, "upper": upper, "lower": lower})
