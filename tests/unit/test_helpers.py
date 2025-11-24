"""Tests for helper utility functions."""

from decimal import Decimal

from src.utils.helpers import calculate_position_size, format_price


def test_calculate_position_size_with_stop_loss() -> None:
    """Ensure stop-loss-aware position sizing works."""
    size = calculate_position_size(
        portfolio_value=100_000,
        risk_per_trade=0.02,
        entry_price=100,
        stop_loss=95,
        leverage=1.0,
    )
    # Risk amount = 2000, price diff = 5, so size should be 400
    assert size == 400


def test_calculate_position_size_without_stop_loss() -> None:
    """Fallback calculation when stop loss is not provided."""
    size = calculate_position_size(
        portfolio_value=50_000,
        risk_per_trade=0.01,
        entry_price=250,
        stop_loss=None,
        leverage=2.0,
    )
    # (50_000 * 0.01 * 2) / 250 = 4
    assert size == 4


def test_format_price_currency() -> None:
    """Verify formatting with currency symbol."""
    formatted = format_price(123.4567, decimals=2, include_currency=True)
    assert formatted == "$123.46"


def test_format_price_trims_trailing_zeroes() -> None:
    """Ensure trailing zeros after decimal are removed."""
    formatted = format_price(Decimal("10.5000"), decimals=4, include_currency=False)
    assert formatted == "10.5"
