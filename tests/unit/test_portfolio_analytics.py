"""Tests for PortfolioAnalytics."""

from datetime import datetime, timedelta

from src.core.portfolio_analytics import PortfolioAnalytics


def _history() -> list[dict[str, float | str]]:
    base = datetime(2024, 1, 1)
    points = []
    equity = 100000.0
    for day in range(5):
        timestamp = base + timedelta(days=day)
        points.append(
            {
                "timestamp": timestamp.isoformat(),
                "equity": equity,
                "profit_loss": 100.0,
                "profit_loss_pct": 0.001,
            }
        )
        equity *= 1.002  # Simulate growth
    return points


def test_calculate_metrics_returns_values() -> None:
    """Analytics should compute standard metrics without crashing."""

    analytics = PortfolioAnalytics()
    metrics = analytics.calculate_metrics(_history())

    assert "sharpe" in metrics
    assert "max_drawdown" in metrics
    assert "cumulative_return" in metrics
    assert metrics["cumulative_return"] > 0
