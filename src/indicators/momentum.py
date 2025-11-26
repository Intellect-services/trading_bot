"""Momentum indicators."""

from __future__ import annotations

import pandas as pd


def _series(series: pd.Series, name: str) -> pd.Series:
    if not isinstance(series, pd.Series):
        raise TypeError(f"{name} expects a pandas Series")
    return series.astype(float)


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Relative Strength Index."""

    series = _series(series, "rsi")
    if window <= 0:
        raise ValueError("window must be positive")
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi_series = 100 - (100 / (1 + rs))
    return rsi_series.fillna(0.0).astype(float)


def stochastic_oscillator(
    close: pd.Series,
    high: pd.Series,
    low: pd.Series,
    k_window: int = 14,
    d_window: int = 3,
) -> pd.DataFrame:
    """Stochastic oscillator (%K and %D)."""

    close = _series(close, "stochastic-close")
    high = _series(high, "stochastic-high")
    low = _series(low, "stochastic-low")

    lowest_low = low.rolling(window=k_window, min_periods=k_window).min()
    highest_high = high.rolling(window=k_window, min_periods=k_window).max()
    percent_k = (close - lowest_low) / (highest_high - lowest_low) * 100
    percent_d = percent_k.rolling(window=d_window, min_periods=d_window).mean()
    return pd.DataFrame({"%K": percent_k, "%D": percent_d})


def williams_r(close: pd.Series, high: pd.Series, low: pd.Series, window: int = 14) -> pd.Series:
    """Williams %R oscillator."""

    close = _series(close, "williams-close")
    high = _series(high, "williams-high")
    low = _series(low, "williams-low")
    highest_high = high.rolling(window=window, min_periods=window).max()
    lowest_low = low.rolling(window=window, min_periods=window).min()
    return -100 * (highest_high - close) / (highest_high - lowest_low)


def commodity_channel_index(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    window: int = 20,
) -> pd.Series:
    """Commodity Channel Index."""

    typical_price = (high + low + close) / 3
    sma_tp = typical_price.rolling(window=window, min_periods=window).mean()
    mean_deviation = typical_price.rolling(window=window, min_periods=window).apply(
        lambda x: (abs(x - x.mean())).mean(), raw=True
    )
    return (typical_price - sma_tp) / (0.015 * mean_deviation)


def rate_of_change(series: pd.Series, window: int = 10) -> pd.Series:
    """Rate of change indicator."""

    series = _series(series, "roc")
    return series.pct_change(periods=window) * 100
