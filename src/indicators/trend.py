"""Trend-following indicators."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _validate_series(series: pd.Series, min_length: int, name: str) -> pd.Series:
    if not isinstance(series, pd.Series):
        raise TypeError(f"{name} expects a pandas Series")
    if len(series) < min_length:
        raise ValueError(f"{name} requires at least {min_length} data points")
    return series.astype(float)


def sma(series: pd.Series, window: int) -> pd.Series:
    """Simple moving average."""

    series = _validate_series(series, window, "sma")
    if window <= 0:
        raise ValueError("window must be positive")
    return series.rolling(window=window, min_periods=window).mean()


def ema(series: pd.Series, window: int) -> pd.Series:
    """Exponential moving average."""

    series = _validate_series(series, window, "ema")
    if window <= 0:
        raise ValueError("window must be positive")
    return series.ewm(span=window, adjust=False).mean()


def wma(series: pd.Series, window: int) -> pd.Series:
    """Weighted moving average."""

    series = _validate_series(series, window, "wma")
    if window <= 0:
        raise ValueError("window must be positive")
    weights = np.arange(1, window + 1)
    return (
        series.rolling(window)
        .apply(lambda values: np.dot(values, weights) / weights.sum(), raw=True)
        .rename(series.name)
    )


def macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """Moving Average Convergence Divergence."""

    if slow <= fast:
        raise ValueError("slow window must be greater than fast window")
    fast_ema = ema(series, fast)
    slow_ema = ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return pd.DataFrame(
        {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram,
        }
    )


def adx(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    window: int = 14,
) -> pd.Series:
    """Average Directional Index."""

    high = _validate_series(high, window + 1, "adx-high")
    low = _validate_series(low, window + 1, "adx-low")
    close = _validate_series(close, window + 1, "adx-close")

    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)

    tr_components = pd.concat(
        [
            (high - low).abs(),
            (high - close.shift()).abs(),
            (low - close.shift()).abs(),
        ],
        axis=1,
    )
    true_range = tr_components.max(axis=1)

    atr = true_range.rolling(window=window, min_periods=window).mean()
    plus_di = 100 * (plus_dm.rolling(window=window).sum() / atr)
    minus_di = 100 * (minus_dm.rolling(window=window).sum() / atr)

    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    return dx.rolling(window=window).mean()
