import pytest
import pandas as pd
import numpy as np
from src.core.risk_manager import RiskManager


@pytest.fixture
def config():
    return {
        "risk": {
            "max_position_size": 0.1,
            "stop_loss": 0.02,
            "take_profit": 0.04,
            "max_drawdown": 0.1,
            "max_leverage": 2.0,
        }
    }


@pytest.fixture
def risk_manager(config):
    return RiskManager(config)


@pytest.fixture
def sample_data():
    dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")
    np.random.seed(42)
    prices = np.random.normal(100, 10, len(dates))
    return pd.DataFrame(
        {
            "open": prices,
            "high": prices + np.random.uniform(0, 2, len(dates)),
            "low": prices - np.random.uniform(0, 2, len(dates)),
            "close": prices + np.random.uniform(-1, 1, len(dates)),
            "volume": np.random.randint(1000, 10000, len(dates)),
        },
        index=dates,
    )


@pytest.fixture
def sample_signals(sample_data):
    signals = pd.DataFrame(index=sample_data.index)
    signals["signal"] = 0
    signals.loc[sample_data.index[:100], "signal"] = 1  # Buy signals
    signals.loc[sample_data.index[100:200], "signal"] = -1  # Sell signals
    return signals


def test_risk_manager_initialization(risk_manager):
    assert isinstance(risk_manager.config, dict)
    assert "risk" in risk_manager.config
    assert risk_manager.max_position_size == 0.1
    assert risk_manager.stop_loss == 0.02
    assert risk_manager.take_profit == 0.04


def test_apply_risk_management(risk_manager, sample_signals, sample_data):
    risk_managed_signals = risk_manager.apply_risk_management(
        sample_signals, sample_data
    )
    assert isinstance(risk_managed_signals, pd.DataFrame)
    assert "signal" in risk_managed_signals.columns
    assert len(risk_managed_signals) == len(sample_signals)
    assert risk_managed_signals["signal"].isin([-1, 0, 1]).all()


def test_calculate_position_size(risk_manager):
    portfolio_value = 100000
    price = 150.0
    risk_per_trade = 0.01

    position_size = risk_manager.calculate_position_size(
        portfolio_value=portfolio_value, price=price, risk_per_trade=risk_per_trade
    )

    assert isinstance(position_size, int)
    assert position_size > 0
    assert position_size * price <= portfolio_value * risk_manager.max_position_size


def test_check_stop_loss(risk_manager):
    entry_price = 100.0
    current_price = 98.0
    stop_loss = risk_manager.check_stop_loss(entry_price, current_price)
    assert stop_loss == (current_price <= entry_price * (1 - risk_manager.stop_loss))


def test_check_take_profit(risk_manager):
    entry_price = 100.0
    current_price = 104.0
    take_profit = risk_manager.check_take_profit(entry_price, current_price)
    assert take_profit == (
        current_price >= entry_price * (1 + risk_manager.take_profit)
    )


def test_check_max_drawdown(risk_manager):
    equity_curve = pd.Series([100000, 95000, 90000, 85000, 80000])
    max_drawdown = risk_manager.check_max_drawdown(equity_curve)
    assert max_drawdown == (
        equity_curve.min() / equity_curve.max() - 1 <= -risk_manager.max_drawdown
    )


def test_check_leverage(risk_manager):
    portfolio_value = 100000
    position_value = 150000
    leverage_ok = risk_manager.check_leverage(portfolio_value, position_value)
    assert leverage_ok == (
        position_value / portfolio_value <= risk_manager.max_leverage
    )
