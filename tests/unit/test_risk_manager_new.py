"""Additional risk manager tests."""

from src.core.risk_manager import RiskManager


def test_kelly_fraction_bounds() -> None:
    rm = RiskManager(10000)
    frac = rm.kelly_fraction(win_rate=0.55, reward_risk=2.0)
    assert 0 < frac < 1


def test_position_size_kelly_respects_max() -> None:
    rm = RiskManager(10000, max_position_size=0.2)
    qty = rm.position_size_kelly(price=50, portfolio_value=10000, win_rate=0.6, reward_risk=2.0)
    assert qty * 50 <= 10000 * 0.2


def test_drawdown_checks() -> None:
    rm = RiskManager(10000, max_drawdown=0.1)
    rm.update_equity(9500)
    assert rm.check_drawdown_limit(9500)
    assert not rm.check_drawdown_limit(8800)


def test_daily_loss_limit() -> None:
    rm = RiskManager(10000, max_daily_loss=0.05)
    rm.reset_daily_equity(10000)
    assert rm.check_daily_loss_limit(9600)
    assert not rm.check_daily_loss_limit(9400)
