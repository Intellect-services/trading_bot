import pytest

from src.core.portfolio import Portfolio


@pytest.fixture()
def portfolio() -> Portfolio:
    return Portfolio(100_000)


def test_portfolio_initialization(portfolio: Portfolio) -> None:
    assert portfolio.initial_capital == 100_000
    assert portfolio.current_balance == 100_000
    assert portfolio.positions == {}
    assert portfolio.trades == []


def test_execute_order_buy_and_sell(portfolio: Portfolio) -> None:
    portfolio.execute_order("AAPL", 100, "buy", 150.0)
    assert portfolio.positions["AAPL"]["size"] == 100
    assert portfolio.current_balance == pytest.approx(85_000)

    portfolio.execute_order("AAPL", 50, "sell", 160.0)
    assert portfolio.positions["AAPL"]["size"] == 50
    # Cash plus mark-to-market value should exceed initial after profitable sale
    assert portfolio.get_value() > portfolio.initial_capital


def test_update_prices(portfolio: Portfolio) -> None:
    portfolio.execute_order("AAPL", 100, "buy", 150.0)
    portfolio.update_prices({"AAPL": 155.0})
    assert portfolio.positions["AAPL"]["current_price"] == 155.0


def test_calculate_position_value(portfolio: Portfolio) -> None:
    portfolio.execute_order("AAPL", 100, "buy", 150.0)
    value = portfolio.calculate_position_value("AAPL", 160.0)
    assert value == 16_000.0


def test_calculate_portfolio_value(portfolio: Portfolio) -> None:
    portfolio.execute_order("AAPL", 100, "buy", 150.0)
    total_value = portfolio.calculate_portfolio_value({"AAPL": 160.0})
    assert total_value == pytest.approx(portfolio.current_balance + 16_000.0)


def test_total_returns(portfolio: Portfolio) -> None:
    portfolio.execute_order("AAPL", 100, "buy", 100.0)
    portfolio.update_prices({"AAPL": 120.0})
    returns = portfolio.calculate_total_returns({"AAPL": 120.0})
    assert returns > 0


def test_get_trade_history(portfolio: Portfolio) -> None:
    portfolio.execute_order("AAPL", 100, "buy", 150.0)
    portfolio.execute_order("AAPL", 50, "sell", 160.0)
    history = portfolio.get_trade_history()
    assert len(history) == 2
    assert history[0]["side"] == "buy"
    assert history[1]["side"] == "sell"


def test_get_position_helpers(portfolio: Portfolio) -> None:
    portfolio.execute_order("AAPL", 100, "buy", 150.0)
    pos = portfolio.get_position("AAPL")
    assert pos is not None
    assert pos["size"] == 100
    assert portfolio.get_position("MSFT") is None


def test_get_all_positions(portfolio: Portfolio) -> None:
    portfolio.execute_order("AAPL", 100, "buy", 150.0)
    positions = portfolio.get_all_positions()
    assert "AAPL" in positions


def test_update_portfolio_wrapper(portfolio: Portfolio) -> None:
    portfolio.update_portfolio("AAPL", 10, 50.0, "buy")
    assert portfolio.positions["AAPL"]["size"] == 10


def test_get_summary_returns_field(portfolio: Portfolio) -> None:
    portfolio.execute_order("AAPL", 50, "buy", 100.0)
    portfolio.update_prices({"AAPL": 120.0})
    summary = portfolio.get_summary()
    assert summary["total_return"] == pytest.approx(
        (portfolio.get_value() - portfolio.initial_capital) / portfolio.initial_capital
    )
