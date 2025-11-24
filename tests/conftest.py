"""Pytest configuration and shared fixtures."""

import os
from datetime import datetime
from typing import Any
from unittest.mock import Mock

import pandas as pd
import pytest

# Set test environment variables
os.environ["FLASK_ENV"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
os.environ["ENCRYPTION_KEY"] = "test-encryption-key-32-bytes-long!!"
os.environ["RESEND_API_KEY"] = os.getenv("RESEND_API_KEY", "test-mode")
os.environ["EMAIL_FROM"] = os.getenv("EMAIL_FROM", "test@intellectscout.com")


@pytest.fixture()
def mock_alpaca_service() -> Mock:
    """Create a mock AlpacaService for testing."""
    mock_service = Mock()
    mock_service.get_account.return_value = {
        "cash": 10000.0,
        "portfolio_value": 10000.0,
        "buying_power": 10000.0,
        "equity": 10000.0,
        "last_equity": 10000.0,
    }
    mock_service.get_positions.return_value = []
    mock_service.get_clock.return_value = {
        "is_open": True,
        "timestamp": datetime.now().isoformat(),
        "next_open": None,
        "next_close": None,
    }
    mock_service.get_orders.return_value = []
    mock_service.submit_order.return_value = {
        "id": "test-order-id",
        "status": "filled",
        "symbol": "AAPL",
        "qty": 10,
    }
    return mock_service


@pytest.fixture()
def sample_market_data() -> pd.DataFrame:
    """Generate sample market data for testing."""
    dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")
    return pd.DataFrame(
        {
            "open": [100.0 + i * 0.1 for i in range(len(dates))],
            "high": [101.0 + i * 0.1 for i in range(len(dates))],
            "low": [99.0 + i * 0.1 for i in range(len(dates))],
            "close": [100.5 + i * 0.1 for i in range(len(dates))],
            "volume": [1000000] * len(dates),
        },
        index=dates,
    )


@pytest.fixture()
def test_config() -> dict[str, Any]:
    """Create a test configuration dictionary."""
    return {
        "alpaca_api_key_id": "test-key",
        "alpaca_api_secret_key": "test-secret",
        "trading_mode": "paper",
        "trading_symbols": ["AAPL", "MSFT", "GOOGL"],
        "trading_timeframe": "1D",
        "risk_max_position_size": 0.1,
        "risk_stop_loss": 0.02,
        "risk_take_profit": 0.04,
    }


@pytest.fixture()
def mock_user() -> dict[str, Any]:
    """Create a mock user dictionary."""
    return {
        "id": 1,
        "email": "test@example.com",
        "name": "Test User",
        "email_verified": True,
        "role": "trader",
    }


@pytest.fixture()
def mock_user_credentials() -> dict[str, Any]:
    """Create mock user credentials."""
    return {
        "user_id": 1,
        "alpaca_api_key_encrypted": "encrypted-key",
        "alpaca_secret_key_encrypted": "encrypted-secret",
        "trading_mode": "paper",
        "is_active": True,
    }


@pytest.fixture()
def flask_app():
    """Create a Flask application for testing."""
    import os

    # Override environment for testing
    os.environ["FLASK_ENV"] = "testing"
    os.environ["TESTING"] = "1"
    os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["SESSION_TYPE"] = "filesystem"

    # Import the actual app after env vars are set
    from src.app import app
    from src.database import db

    # Configure for testing
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SECRET_KEY"] = "test-secret-key-for-testing-only"
    app.config["SESSION_TYPE"] = "filesystem"

    with app.app_context():
        from src.models.email_token import EmailToken  # noqa: F401
        from src.models.user import User  # noqa: F401
        from src.models.user_credentials import UserCredentials  # noqa: F401

        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(flask_app):
    """Create a test client for the Flask app."""
    return flask_app.test_client()


@pytest.fixture()
def authenticated_client(client, flask_app):
    """Create an authenticated test client."""

    from src.database import db
    from src.models.user import User

    with flask_app.app_context():
        # Create test user
        test_user = User(
            email="test@example.com",
            name="Test User",
            email_verified=True,
            role="trader",
        )
        password = "testpassword123"
        test_user.set_password(password)
        db.session.add(test_user)
        db.session.commit()

        # Login
        client.post(
            "/login",
            json={"email": "test@example.com", "password": password},
            content_type="application/json",
        )

        yield client


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration before each test."""
    import logging

    # Clear all handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    yield

    # Cleanup after test
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
