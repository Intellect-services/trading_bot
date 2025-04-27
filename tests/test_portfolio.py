import pytest
import pandas as pd
import numpy as np
from src.core.portfolio import Portfolio


@pytest.fixture
def config():
    return {
        "portfolio": {
            "initial_capital": 100000,
            "max_position_size": 0.1,
            "commission": 0.001,
        }
    }


@pytest.fixture
def portfolio(config):
    return Portfolio(config["portfolio"]["initial_capital"])


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


def test_portfolio_initialization(portfolio):
    assert portfolio.initial_capital == 100000
    assert portfolio.current_capital == 100000
    assert portfolio.max_position_size == 0.1
    assert portfolio.commission == 0.001
    assert len(portfolio.positions) == 0
    assert len(portfolio.trades) == 0


def test_update_portfolio(portfolio, sample_data):
    # Simulate a buy trade
    price = sample_data["close"].iloc[0]
    quantity = 100
    portfolio.update_portfolio("AAPL", quantity, price, "buy")

    assert len(portfolio.positions) == 1
    assert portfolio.positions["AAPL"]["quantity"] == quantity
    assert portfolio.positions["AAPL"]["entry_price"] == price
    assert portfolio.current_capital < portfolio.initial_capital


def test_calculate_position_value(portfolio, sample_data):
    # Add a position
    price = sample_data["close"].iloc[0]
    quantity = 100
    portfolio.update_portfolio("AAPL", quantity, price, "buy")

    # Calculate position value
    current_price = sample_data["close"].iloc[1]
    position_value = portfolio.calculate_position_value("AAPL", current_price)

    assert position_value == quantity * current_price


def test_calculate_portfolio_value(portfolio, sample_data):
    # Add positions
    price1 = sample_data["close"].iloc[0]
    price2 = sample_data["close"].iloc[1]
    portfolio.update_portfolio("AAPL", 100, price1, "buy")
    portfolio.update_portfolio("MSFT", 50, price2, "buy")

    # Calculate portfolio value
    current_prices = {
        "AAPL": sample_data["close"].iloc[2],
        "MSFT": sample_data["close"].iloc[2],
    }
    portfolio_value = portfolio.calculate_portfolio_value(current_prices)

    assert portfolio_value > 0
    assert portfolio_value == portfolio.current_capital + sum(
        portfolio.calculate_position_value(symbol, price)
        for symbol, price in current_prices.items()
    )


def test_calculate_returns(portfolio, sample_data):
    # Add a position and simulate price changes
    initial_price = sample_data["close"].iloc[0]
    portfolio.execute_order("AAPL", 100, "buy", initial_price)

    # Simulate price changes
    current_price = initial_price * 1.1  # 10% increase
    portfolio.update_prices({"AAPL": current_price})
    position = portfolio.get_position("AAPL")
    returns = (current_price - position["avg_price"]) / position["avg_price"]

    assert returns == pytest.approx(0.1, rel=1e-9)  # 10% return


def test_calculate_total_returns(portfolio, sample_data):
    # Add positions
    price1 = sample_data["close"].iloc[0]
    price2 = sample_data["close"].iloc[1]
    portfolio.update_portfolio("AAPL", 100, price1, "buy")
    portfolio.update_portfolio("MSFT", 50, price2, "buy")

    # Calculate total returns
    current_prices = {
        "AAPL": price1 * 1.1,  # 10% increase
        "MSFT": price2 * 1.05,  # 5% increase
    }
    total_returns = portfolio.calculate_total_returns(current_prices)

    assert total_returns > 0
    assert (
        total_returns
        == (
            portfolio.calculate_portfolio_value(current_prices)
            - portfolio.initial_capital
        )
        / portfolio.initial_capital
    )


def test_get_position(portfolio, sample_data):
    # Add a position
    price = sample_data["close"].iloc[0]
    quantity = 100
    portfolio.update_portfolio("AAPL", quantity, price, "buy")

    position = portfolio.get_position("AAPL")
    assert position["quantity"] == quantity
    assert position["entry_price"] == price


def test_get_all_positions(portfolio, sample_data):
    # Add positions
    price1 = sample_data["close"].iloc[0]
    price2 = sample_data["close"].iloc[1]
    portfolio.update_portfolio("AAPL", 100, price1, "buy")
    portfolio.update_portfolio("MSFT", 50, price2, "buy")

    positions = portfolio.get_all_positions()
    assert len(positions) == 2
    assert "AAPL" in positions
    assert "MSFT" in positions
