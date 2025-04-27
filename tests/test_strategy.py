import pytest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from src.core.strategy import Strategy
from src.core.risk_manager import RiskManager
from src.core.portfolio import Portfolio
from src.core.data_feed import DataFeed


class TestStrategy(Strategy):
    def __init__(self, config):
        super().__init__(config)
        self.name = "TestStrategy"
        self.signals = []

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        # Simple moving average crossover strategy
        data["SMA_20"] = data["close"].rolling(window=20).mean()
        data["SMA_50"] = data["close"].rolling(window=50).mean()

        signals = pd.DataFrame(index=data.index)
        signals["signal"] = 0
        signals.loc[data["SMA_20"] > data["SMA_50"], "signal"] = 1
        signals.loc[data["SMA_20"] < data["SMA_50"], "signal"] = -1

        self.signals.append(signals)
        return signals


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
def config():
    return {
        "strategy": {"name": "TestStrategy", "parameters": {}},
        "risk": {
            "max_position_size": 0.1,
            "stop_loss": 0.02,
            "take_profit": 0.04,
            "max_drawdown": 0.1,
            "max_leverage": 2.0,
            "risk_per_trade": 0.02
        }
    }


@pytest.fixture
def strategy(config):
    return TestStrategy(config)


@pytest.fixture
def risk_manager(config):
    return RiskManager(config)


@pytest.fixture
def portfolio():
    return Portfolio(100000)


@pytest.fixture
def data_feed():
    return DataFeed()


def test_strategy_initialization(strategy):
    assert strategy.name == "TestStrategy"
    assert isinstance(strategy.config, dict)
    assert "strategy" in strategy.config
    assert "risk" in strategy.config


def test_generate_signals(strategy, sample_data):
    signals = strategy.generate_signals(sample_data)
    assert isinstance(signals, pd.DataFrame)
    assert "signal" in signals.columns
    assert len(signals) == len(sample_data)
    assert signals["signal"].isin([-1, 0, 1]).all()


def test_strategy_with_risk_manager(strategy, risk_manager, sample_data):
    # Create a sample position
    position = {
        "symbol": "AAPL",
        "size": 50,  # Smaller position size
        "avg_price": 150.0,
        "current_price": 155.0
    }

    # Test risk management
    assert risk_manager.apply_risk_management(
        price=155.0,
        position=position,
        account_value=100000.0
    )

    # Test with position size too large
    large_position = position.copy()
    large_position["size"] = 1000
    assert not risk_manager.apply_risk_management(
        price=155.0,
        position=large_position,
        account_value=100000.0
    )


def test_strategy_with_portfolio(strategy, portfolio, sample_data):
    initial_capital = portfolio.initial_capital
    
    # Simulate a trade
    portfolio.execute_order("AAPL", 100, "buy", 150.0)
    
    assert portfolio.current_balance < initial_capital
    assert "AAPL" in portfolio.positions
    assert portfolio.positions["AAPL"]["size"] == 100
    assert portfolio.positions["AAPL"]["avg_price"] == 150.0
