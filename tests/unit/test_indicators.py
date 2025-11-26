"""Unit tests for indicator helper functions."""

from __future__ import annotations

import pandas as pd
import pytest

from src.indicators import (
    average_true_range,
    bollinger_bands,
    chaikin_money_flow,
    commodity_channel_index,
    ema,
    keltner_channels,
    macd,
    money_flow_index,
    on_balance_volume,
    rate_of_change,
    rsi,
    sma,
    stochastic_oscillator,
    vwap,
    williams_r,
)


def _sample_prices() -> pd.DataFrame:
    values = pd.Series(range(10, 50), dtype=float)  # 40 samples
    data = {
        "close": values,
        "high": values + 1,
        "low": values - 1,
        "volume": pd.Series(range(100, 100 + len(values) * 5, 5), dtype=float),
    }
    return pd.DataFrame(data)


def test_sma_matches_manual_average() -> None:
    df = _sample_prices()
    series = sma(df["close"], window=3)
    assert series.iloc[4] == pytest.approx(df["close"].iloc[2:5].mean())


def test_ema_weights_recent_prices_more() -> None:
    df = _sample_prices()
    series = ema(df["close"], window=3)
    assert series.iloc[-1] > series.iloc[-2]  # upward trend


def test_macd_returns_dataframe() -> None:
    df = _sample_prices()
    result = macd(df["close"])
    assert {"macd", "signal", "histogram"} <= set(result.columns)


def test_rsi_between_zero_and_hundred() -> None:
    df = _sample_prices()
    values = rsi(df["close"])
    assert values.max() <= 100
    assert values.min() >= 0


def test_stochastic_oscillator_ranges() -> None:
    df = _sample_prices()
    osc = stochastic_oscillator(df["close"], df["high"], df["low"], k_window=3)
    assert osc["%K"].dropna().between(0, 100).all()


def test_bollinger_bands_relationships() -> None:
    df = _sample_prices()
    bands = bollinger_bands(df["close"], window=3)
    middle = bands["middle"].dropna()
    assert (bands["upper"].dropna() >= middle).all()
    assert (bands["lower"].dropna() <= middle).all()


def test_average_true_range_positive() -> None:
    df = _sample_prices()
    atr = average_true_range(df["high"], df["low"], df["close"], window=3)
    assert atr.dropna().gt(0).all()


def test_keltner_channels_bounds() -> None:
    df = _sample_prices()
    kc = keltner_channels(df["high"], df["low"], df["close"])
    upper = kc["upper"].dropna()
    middle = kc["middle"].loc[upper.index]
    lower = kc["lower"].loc[upper.index]
    assert (upper >= middle).all()
    assert (lower <= middle).all()


def test_volume_indicators() -> None:
    df = _sample_prices()
    obv = on_balance_volume(df["close"], df["volume"])
    assert len(obv) == len(df)
    mf = money_flow_index(df["high"], df["low"], df["close"], df["volume"])
    assert mf.dropna().between(0, 100).all()
    cmf = chaikin_money_flow(df["high"], df["low"], df["close"], df["volume"])
    assert len(cmf) == len(df)
    assert cmf.dropna().size > 0


def test_vwap_monotonic() -> None:
    df = _sample_prices()
    vw = vwap(df["high"], df["low"], df["close"], df["volume"])
    assert vw.iloc[-1] >= vw.iloc[0]


def test_rate_of_change() -> None:
    df = _sample_prices()
    roc_series = rate_of_change(df["close"], window=2)
    expected = ((df["close"].iloc[5] - df["close"].iloc[3]) / df["close"].iloc[3]) * 100
    assert pytest.approx(roc_series.iloc[5], rel=1e-5) == expected


def test_williams_r_range() -> None:
    df = _sample_prices()
    wr = williams_r(df["close"], df["high"], df["low"])
    assert wr.dropna().between(-100, 0).all()


def test_cci_outputs_series() -> None:
    df = _sample_prices()
    cci = commodity_channel_index(df["high"], df["low"], df["close"])
    assert len(cci) == len(df)
