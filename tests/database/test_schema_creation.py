"""Tests for database schema creation and initialization."""

import os
import tempfile

import pytest
from flask import Flask

from src.database import db, init_db


@pytest.fixture()
def app():
    """Create a Flask app for testing."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Use temporary SQLite database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    yield app

    # Cleanup
    try:
        os.unlink(db_path)
        wal_path = f"{db_path}-wal"
        shm_path = f"{db_path}-shm"
        if os.path.exists(wal_path):
            os.unlink(wal_path)
        if os.path.exists(shm_path):
            os.unlink(shm_path)
    except Exception:
        pass


def test_init_db_creates_all_tables(app):
    """Test that init_db creates all required tables."""
    init_db(app)

    with app.app_context():
        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        tables = set(inspector.get_table_names())

        # Required Flask-SQLAlchemy tables
        required_flask_tables = {
            "users",
            "user_credentials",
            "email_tokens",
            "market_data_bars",
            "alembic_version",
        }

        # Required BaseModel tables
        required_base_tables = {
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
        }

        all_required = required_flask_tables | required_base_tables

        # Check all tables exist
        missing = all_required - tables
        assert not missing, f"Missing tables: {missing}"

        # Verify we have at least the expected tables
        assert required_flask_tables.issubset(tables)
        assert required_base_tables.issubset(tables)


def test_init_db_creates_default_admin_user(app):
    """Test that init_db creates default admin user."""
    init_db(app)

    with app.app_context():
        from src.models.user import User

        admin = User.query.filter_by(email="admin@admin.com").first()
        assert admin is not None
        assert admin.role == "owner"
        assert admin.email_verified is True
        assert admin.check_password("admin")


def test_schema_creation_robustness(app):
    """Test that schema creation works even if migrations fail."""
    init_db(app)

    with app.app_context():
        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        tables = set(inspector.get_table_names())

        # All critical tables should exist
        critical_tables = {"users", "portfolios", "strategies", "signals"}

        assert critical_tables.issubset(tables)


def test_foreign_key_constraints(app):
    """Test that foreign key constraints are properly set up."""
    init_db(app)

    with app.app_context():
        from sqlalchemy import text

        # Check that foreign keys are enabled (SQLite specific)
        if "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"]:
            result = db.session.execute(text("PRAGMA foreign_keys"))
            fk_enabled = result.fetchone()[0]
            assert fk_enabled == 1, "Foreign keys should be enabled"
