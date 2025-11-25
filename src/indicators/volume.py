"""Volume-based indicators."""

from __future__ import annotations

import pandas as pd


def on_balance_volume(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On-Balance Volume (OBV)."""

    direction = close.diff().fillna(0).apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return (direction * volume).cumsum()


def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """Volume Weighted Average Price."""

    typical_price = (high + low + close) / 3
    cum_tp_vol = (typical_price * volume).cumsum()
    cum_vol = volume.cumsum()
    return cum_tp_vol / cum_vol.replace(0, pd.NA)


def money_flow_index(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    window: int = 14,
) -> pd.Series:
    """Money Flow Index (MFI)."""

    typical_price = (high + low + close) / 3
    money_flow = typical_price * volume
    delta = typical_price.diff()
    positive_flow = money_flow.where(delta > 0, 0.0)
    negative_flow = money_flow.where(delta < 0, 0.0)
    positive_sum = positive_flow.rolling(window=window, min_periods=window).sum()
    negative_sum = abs(negative_flow.rolling(window=window, min_periods=window).sum())
    ratio = positive_sum / negative_sum.replace(0, pd.NA)
    return 100 - (100 / (1 + ratio))


def chaikin_money_flow(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    window: int = 20,
) -> pd.Series:
    """Chaikin Money Flow (CMF)."""

    money_flow_multiplier = ((close - low) - (high - close)) / (high - low).replace(0, pd.NA)
    money_flow_volume = money_flow_multiplier * volume
    return (
        money_flow_volume.rolling(window=window, min_periods=window).sum()
        / volume.rolling(window=window, min_periods=window).sum()
    )
