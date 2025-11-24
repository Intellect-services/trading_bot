from typing import Any

import numpy as np
import pandas as pd
import pytest

from src.core.data_feed import DataFeed
from src.core.portfolio import Portfolio
from src.core.risk_manager import RiskManager
from src.core.strategy import Strategy


class SimpleMovingAverageStrategy(Strategy):
    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__()
        self.name = "SimpleMovingAverageStrategy"
        self.signals: list[list[dict[str, Any]]] = []
        self.config = config

    def calculate_position_size(self, price: float, risk_amount: float) -> float:
        return risk_amount / price

    def should_open_position(self, price: float) -> bool:
        return True  # Simplified for testing

    def should_close_position(self, price: float) -> bool:
        return False  # Simplified for testing

    def get_stop_loss(self, price: float) -> float | None:
        return price * 0.95  # 5% stop loss

    def get_take_profit(self, price: float) -> float | None:
        return price * 1.1  # 10% take profit

    def generate_signals(self, data: pd.DataFrame) -> list[dict[str, Any]]:
        # Simple moving average crossover strategy
        data["SMA_20"] = data["close"].rolling(window=20).mean()
        data["SMA_50"] = data["close"].rolling(window=50).mean()

        signals: list[dict[str, Any]] = []
        for idx, row in data.iterrows():
            if pd.isna(row["SMA_20"]) or pd.isna(row["SMA_50"]):
                continue

            signal = {
                "timestamp": idx,
                "price": row["close"],
                "side": "long" if row["SMA_20"] > row["SMA_50"] else "short",
            }
            signals.append(signal)

        self.signals.append(signals)
        return signals


@pytest.fixture()
def sample_data() -> pd.DataFrame:
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


@pytest.fixture()
def config() -> dict[str, Any]:
    return {
        "strategy": {"name": "SimpleMovingAverageStrategy", "parameters": {}},
        "risk": {
            "max_position_size": 0.1,
            "stop_loss": 0.02,
            "take_profit": 0.04,
            "max_drawdown": 0.1,
            "max_leverage": 2.0,
            "risk_per_trade": 0.02,
        },
    }


@pytest.fixture()
def strategy(config: dict[str, Any]) -> SimpleMovingAverageStrategy:
    return SimpleMovingAverageStrategy(config)


@pytest.fixture()
def risk_manager(config: dict[str, Any]) -> RiskManager:
    return RiskManager(
        initial_capital=100000.0,
        risk_per_trade=config["risk"]["risk_per_trade"],
        max_position_size=config["risk"]["max_position_size"],
        stop_loss_pct=config["risk"]["stop_loss"],
        take_profit_pct=config["risk"]["take_profit"],
        max_drawdown=config["risk"]["max_drawdown"],
        max_leverage=config["risk"]["max_leverage"],
    )


@pytest.fixture()
def portfolio() -> Portfolio:
    return Portfolio(100000)


@pytest.fixture()
def data_feed() -> DataFeed:
    return DataFeed()


def test_strategy_initialization(strategy: SimpleMovingAverageStrategy) -> None:
    assert strategy.name == "SimpleMovingAverageStrategy"
    assert isinstance(strategy.config, dict)
    assert "strategy" in strategy.config
    assert "risk" in strategy.config


def test_generate_signals(strategy: SimpleMovingAverageStrategy, sample_data: pd.DataFrame) -> None:
    signals = strategy.generate_signals(sample_data)
    assert isinstance(signals, list)
    assert all(isinstance(signal, dict) for signal in signals)
    assert all(
        "timestamp" in signal and "price" in signal and "side" in signal for signal in signals
    )

    # Calculate expected number of signals (excluding NaN values)
    data = sample_data.copy()
    data["SMA_20"] = data["close"].rolling(window=20).mean()
    data["SMA_50"] = data["close"].rolling(window=50).mean()
    expected_signals = len(data.dropna(subset=["SMA_20", "SMA_50"]))
    assert len(signals) == expected_signals


def test_strategy_with_risk_manager(
    strategy: SimpleMovingAverageStrategy, risk_manager: RiskManager, sample_data: pd.DataFrame
) -> None:
    # Create a sample position
    position = {
        "symbol": "AAPL",
        "size": 50,  # Smaller position size
        "avg_price": 150.0,
        "current_price": 155.0,
    }

    # Test risk management
    assert risk_manager.apply_risk_management(
        price=155.0, position=position, account_value=100000.0
    )

    # Test with position size too large
    large_position = position.copy()
    large_position["size"] = 1000
    assert not risk_manager.apply_risk_management(
        price=155.0, position=large_position, account_value=100000.0
    )


def test_strategy_with_portfolio(
    strategy: SimpleMovingAverageStrategy, portfolio: Portfolio, sample_data: pd.DataFrame
) -> None:
    initial_capital = portfolio.initial_capital

    # Simulate a trade
    portfolio.execute_order("AAPL", 100, "buy", 150.0)

    assert portfolio.current_balance < initial_capital
    assert "AAPL" in portfolio.positions
    assert portfolio.positions["AAPL"]["size"] == 100
    assert portfolio.positions["AAPL"]["avg_price"] == 150.0
