#!/usr/bin/env python3
"""Create missing database tables for BaseModel-based tables (strategies, signals, etc.).

This script creates the strategies, signals, and backtest_results tables that use
SQLAlchemy BaseModel (separate from Flask-SQLAlchemy models).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask

from src.database import init_db


def create_missing_tables():
    """Create missing tables for BaseModel-based models."""
    print("Creating missing BaseModel tables...")

    # Create Flask app to get proper database configuration
    app = Flask(__name__)
    init_db(app)  # This creates users table first

    with app.app_context():
        try:
            # Import all BaseModel-based models to ensure they're registered
            from src.business.strategy.models.backtest_result import BacktestResult  # noqa: F401
            from src.business.strategy.models.signal import Signal  # noqa: F401
            from src.business.strategy.models.strategy import Strategy  # noqa: F401
            from src.infrastructure import db_config
            from src.infrastructure.base_model import Base

            # Use the SAME database URL as Flask app
            database_url = app.config.get("SQLALCHEMY_DATABASE_URI")
            if database_url:
                db_config.database_url = database_url

            print(f"Database URL: {db_config.database_url}")

            # Create all BaseModel tables (users table should already exist from init_db)
            Base.metadata.create_all(bind=db_config.engine, checkfirst=True)

            print("✅ All tables created successfully!")
            print("   Created/verified: strategies, signals, backtest_results")
            return True

        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            import traceback

            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = create_missing_tables()
    sys.exit(0 if success else 1)
