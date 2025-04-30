import numpy as np
import pandas as pd
import pytest

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
            "risk_per_trade": 0.02,
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


@pytest.fixture
def sample_position():
    return {"symbol": "AAPL", "size": 100, "avg_price": 150.0, "current_price": 155.0}


def test_risk_manager_initialization(risk_manager):
    assert risk_manager.max_position_size == 0.1
    assert risk_manager.stop_loss == 0.02
    assert risk_manager.take_profit == 0.04
    assert risk_manager.max_drawdown == 0.1
    assert risk_manager.max_leverage == 2.0


def test_apply_risk_management(risk_manager, sample_position):
    # Test with valid position
    small_position = sample_position.copy()
    small_position["size"] = 50  # Smaller position size
    assert risk_manager.apply_risk_management(
        price=155.0, position=small_position, account_value=100000.0
    )

    # Test with position size too large
    large_position = sample_position.copy()
    large_position["size"] = 1000
    assert not risk_manager.apply_risk_management(
        price=155.0, position=large_position, account_value=100000.0
    )

    # Test with stop loss triggered
    losing_position = sample_position.copy()
    losing_position["size"] = 50
    losing_position["avg_price"] = 160.0
    assert not risk_manager.apply_risk_management(
        price=155.0, position=losing_position, account_value=100000.0
    )


def test_calculate_position_size(risk_manager):
    portfolio_value = 100000.0
    price = 150.0

    position_size = risk_manager.calculate_position_size(
        portfolio_value=portfolio_value, price=price
    )

    assert isinstance(position_size, int)
    assert position_size > 0
    assert position_size * price <= portfolio_value * risk_manager.max_position_size


def test_calculate_stop_loss(risk_manager):
    price = 100.0
    quantity = 100  # Long position
    stop_loss = risk_manager.calculate_stop_loss(price, quantity)
    assert stop_loss == price * (1 - risk_manager.stop_loss)

    quantity = -100  # Short position
    stop_loss = risk_manager.calculate_stop_loss(price, quantity)
    assert stop_loss == price * (1 + risk_manager.stop_loss)


def test_calculate_take_profit(risk_manager):
    price = 100.0
    quantity = 100  # Long position
    take_profit = risk_manager.calculate_take_profit(price, quantity)
    assert take_profit == price * (1 + risk_manager.take_profit)

    quantity = -100  # Short position
    take_profit = risk_manager.calculate_take_profit(price, quantity)
    assert take_profit == price * (1 - risk_manager.take_profit)


def test_check_leverage(risk_manager):
    portfolio_value = 100000.0
    position_value = 150000.0  # 1.5x leverage
    assert risk_manager.check_leverage(portfolio_value, position_value)

    position_value = 250000.0  # 2.5x leverage
    assert not risk_manager.check_leverage(portfolio_value, position_value)
