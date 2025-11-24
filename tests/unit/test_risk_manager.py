import pytest

from src.core.risk_manager import RiskManager


@pytest.fixture()
def risk_manager() -> RiskManager:
    return RiskManager(
        initial_capital=100_000.0,
        risk_per_trade=0.02,
        max_position_size=0.1,
        stop_loss_pct=0.02,
        take_profit_pct=0.04,
        max_drawdown=0.1,
        max_leverage=2.0,
    )


def test_risk_manager_initialization(risk_manager: RiskManager) -> None:
    assert risk_manager.initial_capital == 100_000
    assert risk_manager.risk_per_trade == 0.02
    assert risk_manager.max_position_size == 0.1
    assert risk_manager.max_drawdown == 0.1
    assert risk_manager.max_leverage == 2.0


def test_apply_risk_management(risk_manager: RiskManager) -> None:
    position = {
        "symbol": "AAPL",
        "size": 50,
        "avg_price": 150.0,
        "current_price": 155.0,
        "side": "long",
        "stop_loss": 147.0,
        "take_profit": 160.0,
    }
    assert risk_manager.apply_risk_management(155.0, position, 100_000.0)

    oversized = {**position, "size": 10_000}
    assert not risk_manager.apply_risk_management(155.0, oversized, 100_000.0)

    stop_hit = {**position, "stop_loss": 156.0}
    assert not risk_manager.apply_risk_management(150.0, stop_hit, 100_000.0)

    tp_hit = {**position, "take_profit": 150.0}
    assert not risk_manager.apply_risk_management(160.0, tp_hit, 100_000.0)


def test_calculate_position_size_bounds(risk_manager: RiskManager) -> None:
    size = risk_manager.calculate_position_size(100.0, 2_000.0)
    assert size == pytest.approx(20.0)

    with pytest.raises(ValueError):
        risk_manager.calculate_position_size(0.0, 1_000.0)

    with pytest.raises(ValueError):
        risk_manager.calculate_position_size(-1.0, 1_000.0)


def test_stop_loss_and_take_profit(risk_manager: RiskManager) -> None:
    assert risk_manager.calculate_stop_loss(100.0, quantity=10) == pytest.approx(98.0)
    assert risk_manager.calculate_stop_loss(100.0, quantity=-10) == pytest.approx(102.0)

    assert risk_manager.calculate_take_profit(100.0, quantity=10) == pytest.approx(104.0)
    assert risk_manager.calculate_take_profit(100.0, quantity=-10) == pytest.approx(96.0)

    with pytest.raises(ValueError):
        risk_manager.calculate_take_profit(0.0, quantity=1)


def test_check_leverage_and_validate_trade(risk_manager: RiskManager) -> None:
    assert risk_manager.check_leverage(1.5, 100_000.0)
    assert not risk_manager.check_leverage(2.5, 100_000.0)

    with pytest.raises(ValueError):
        risk_manager.check_leverage(1.0, 0.0)

    assert risk_manager.validate_trade("AAPL", 10, 100.0, 100_000.0)
    assert not risk_manager.validate_trade("AAPL", 10_000, 100.0, 100_000.0)


def test_trailing_stop_updates(risk_manager: RiskManager) -> None:
    positions = {
        "AAPL": {
            "symbol": "AAPL",
            "size": 10,
            "avg_price": 100.0,
            "current_price": 110.0,
            "side": "long",
            "stop_loss": 95.0,
            "take_profit": 120.0,
        }
    }
    risk_manager.update_trailing_stops(positions)
    assert positions["AAPL"]["stop_loss"] >= 95.0
