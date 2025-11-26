"""Tests for database initialization in Docker environment."""

import os

import pytest

# Skip if not in Docker/CI environment
pytestmark = pytest.mark.skipif(
    not os.getenv("CI") and not os.getenv("DOCKER_ENV"),
    reason="Docker tests only run in CI or with DOCKER_ENV set",
)


def test_database_container_accessible():
    """Test that database container is accessible from app container."""
    import psycopg2

    database_url = os.getenv("DATABASE_URL")
    if not database_url or "postgresql" not in database_url.lower():
        pytest.skip("DATABASE_URL not set or not PostgreSQL")

    # Try to connect
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        assert result[0] == 1
    except Exception as e:
        pytest.fail(f"Failed to connect to database: {e}")


def test_tables_created_in_docker():
    """Test that all tables are created when app starts in Docker."""
    from flask import Flask
    from sqlalchemy import inspect

    from src.database import db, init_db

    app = Flask(__name__)

    # Set DATABASE_URL if not already set
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            app.config["SQLALCHEMY_DATABASE_URI"] = database_url

    init_db(app)

    with app.app_context():
        inspector = inspect(db.engine)
        tables = set(inspector.get_table_names())

        required_tables = {
            "users",
            "user_credentials",
            "email_tokens",
            "market_data_bars",
            "portfolios",
            "positions",
            "orders",
            "trades",
            "portfolio_snapshots",
            "strategies",
            "signals",
            "backtest_results",
            "user_settings",
            "audit_log",
            "alembic_version",
        }

        missing = required_tables - tables
        assert not missing, f"Missing tables in Docker: {missing}"
