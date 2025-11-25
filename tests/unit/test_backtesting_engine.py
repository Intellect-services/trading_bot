"""Tests for backtesting engine enhancements."""

from __future__ import annotations

import pandas as pd

from src.backtesting.engine import BacktestEngine
from src.core.strategy import Strategy


class DummyStrategy(Strategy):
    """Simple strategy that buys then sells each bar."""

    def __init__(self, symbol: str = "TEST") -> None:
        super().__init__()
        self.symbol = symbol

    def generate_signals(self, bars: pd.DataFrame) -> list[dict]:
        signals: list[dict] = []
        for idx, row in bars.iterrows():
            price = float(row["close"])
            signals.append(
                {
                    "symbol": self.symbol,
                    "action": "buy",
                    "timestamp": idx,
                    "price": price,
                    "size": 0.1,
                }
            )
            signals.append(
                {
                    "symbol": self.symbol,
                    "action": "sell",
                    "timestamp": idx,
                    "price": price * 1.01,
                    "size": 0.1,
                }
            )
        return signals

    def calculate_position_size(self, price: float, risk_amount: float) -> float:  # noqa: ARG002
        return 1.0

    def should_open_position(self, price: float) -> bool:  # noqa: ARG002
        return True

    def should_close_position(self, price: float) -> bool:  # noqa: ARG002
        return True

    def get_stop_loss(self, price: float) -> float:
        return price * 0.95

    def get_take_profit(self, price: float) -> float:
        return price * 1.05


def _price_frame(symbol: str) -> pd.DataFrame:
    data = {
        "close": pd.Series([100, 101, 102, 103], dtype=float),
    }
    df = pd.DataFrame(data)
    df.index = pd.date_range("2024-01-01", periods=len(df), freq="D")
    return df


def test_backtest_engine_reports_metrics() -> None:
    engine = BacktestEngine(DummyStrategy(), initial_capital=10000)
    result = engine.run(_price_frame("TEST"))
    metrics = result["metrics"]
    assert "sharpe_ratio" in metrics
    assert "sortino_ratio" in metrics
    assert "profit_factor" in metrics
    assert "cagr" in metrics
    assert "equity_curve" in result


def test_run_multiple_symbols() -> None:
    engine = BacktestEngine(DummyStrategy(), initial_capital=5000)
    market_data = {"AAA": _price_frame("AAA"), "BBB": _price_frame("BBB")}
    results = engine.run_multiple(
        market_data,
        strategy_factory=DummyStrategy,
    )
    assert set(results.keys()) == {"AAA", "BBB"}
    for symbol, summary in results.items():
        assert "metrics" in summary
        assert summary["metrics"]["total_trades"] > 0
