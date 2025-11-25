#!/usr/bin/env python3
"""Reset database - drop all tables and recreate with fresh schema."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from flask import Flask

load_dotenv()

# Create Flask app
app = Flask(__name__)

# Initialize database
from src.database import db, init_db

init_db(app)

# Get database path for permission fixing (do this inside app context)
database_url = os.getenv("DATABASE_URL")
database_path = None

with app.app_context():
    # Ensure database file has write permissions before proceeding
    if not database_url or database_url.startswith("sqlite"):
        # SQLite database - ensure file permissions
        try:
            # Access engine property inside app context
            database_path = db.engine.url.database.replace("///", "/").replace("//", "/")
            if database_path and os.path.exists(database_path):
                try:
                    os.chmod(database_path, 0o664)  # Make writable
                    print(f"✓ Set write permissions on {database_path}")
                except OSError as e:
                    print(f"⚠️  Warning: Could not set permissions on {database_path}: {e}")
        except Exception as e:
            # If we can't get the path, we'll try to infer it from the config
            print(f"⚠️  Could not get database path from engine: {e}")
            if not database_url:
                # Default SQLite path
                basedir = os.path.abspath(os.path.dirname(__file__))
                database_path = os.path.join(basedir, "..", "src", "trading_bot.db")
                database_path = os.path.abspath(database_path)
    # Import all Flask-SQLAlchemy models to ensure they're registered
    from src.models.email_token import EmailToken  # noqa: F401
    from src.models.market_data_bar import MarketDataBar  # noqa: F401
    from src.models.user import User  # noqa: F401
    from src.models.user_credentials import UserCredentials  # noqa: F401

    print("Dropping all Flask-SQLAlchemy tables...")
    db.drop_all()
    print("Creating all Flask-SQLAlchemy tables...")
    db.create_all()

    # IMPORTANT: Drop ALL BaseModel tables (trading domain + strategies)
    print("\nDropping all BaseModel tables...")

    # Drop trading domain tables first (they have foreign keys) - drop in reverse dependency order
    base_model_tables = [
        "trades",  # Depends on orders and portfolios
        "portfolio_snapshots",  # Depends on portfolios
        "positions",  # Depends on portfolios
        "orders",  # Depends on portfolios
        "portfolios",  # Root of trading domain
        "backtest_results",  # Depends on strategies
        "signals",  # Depends on strategies
        "strategies",  # Depends on users
        "user_settings",  # Depends on users
        "audit_log",  # Might exist
    ]

    for table in base_model_tables:
        result = db.session.execute(
            db.text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        )
        if result.fetchone():
            print(f"  Dropping table: {table}")
            db.session.execute(db.text(f"DROP TABLE IF EXISTS {table}"))

    db.session.commit()

    # Now create all BaseModel tables using the same function as init_db
    print("\nCreating BaseModel tables...")
    from src.database import _create_base_model_tables

    _create_base_model_tables(app)

    print("  ✅ All BaseModel tables created!")

    # All tables are now created by _create_base_model_tables which includes:
    # - portfolios, positions, orders, trades, portfolio_snapshots
    # - strategies, signals, backtest_results
    # - user_settings

    # Close all database connections
    db.session.close()
    try:
        if hasattr(db, "engine"):
            db.engine.dispose()
    except Exception:
        pass  # Ignore errors when disposing engine outside context

    # Ensure database file has write permissions after reset
    if not database_url or database_url.startswith("sqlite"):
        if database_path and os.path.exists(database_path):
            try:
                os.chmod(database_path, 0o664)  # Make writable
            except OSError:
                pass

    print("✅ Database reset complete!")
    print("\nAll tables have been dropped and recreated:")
    print("  - Flask-SQLAlchemy tables: users, email_tokens, user_credentials, market_data_bars")
    print("  - BaseModel tables: portfolios, positions, orders, trades, portfolio_snapshots,")
    print("                      strategies, signals, backtest_results, user_settings")
    print("\n⚠️  IMPORTANT:")
    print("  - All user accounts have been deleted")
    print("  - All trading data has been deleted")
    print("  - You MUST log out and log back in (or clear browser cookies) to reset your session")
    print("  - Default admin user will be created on next app startup")
    print("\n💡 To fully reset your session:")
    print("  1. Log out from the web interface, OR")
    print("  2. Clear your browser cookies for this site, OR")
    print("  3. Use an incognito/private browsing window")
    print("\n💾 Database file permissions have been set to allow writes.")
