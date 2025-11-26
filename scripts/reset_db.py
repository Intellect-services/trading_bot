#!/usr/bin/env python3
"""Reset database - drop all tables and recreate with fresh schema using Alembic migrations."""

import os
import sys
from contextlib import suppress
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

# Get database path for permission fixing (SQLite only)
database_url = os.getenv("DATABASE_URL")
database_path = None

with app.app_context():
    # Ensure database file has write permissions before proceeding (SQLite only)
    if not database_url or database_url.startswith("sqlite"):
        try:
            database_path = db.engine.url.database.replace("///", "/").replace("//", "/")
            if database_path and os.path.exists(database_path):
                try:
                    os.chmod(database_path, 0o664)  # Make writable
                    print(f"✓ Set write permissions on {database_path}")
                except OSError as e:
                    print(f"⚠️  Warning: Could not set permissions on {database_path}: {e}")
        except Exception as e:
            print(f"⚠️  Could not get database path from engine: {e}")
            if not database_url:
                basedir = os.path.abspath(os.path.dirname(__file__))
                database_path = os.path.join(basedir, "..", "src", "trading_bot.db")
                database_path = os.path.abspath(database_path)

    # Import all models to ensure they're registered
    # Import BaseModel classes to ensure they're registered
    from src.business.strategy.models.backtest_result import BacktestResult  # noqa: F401
    from src.business.strategy.models.signal import Signal  # noqa: F401
    from src.business.strategy.models.strategy import Strategy  # noqa: F401
    from src.business.trading.models.order import Order  # noqa: F401
    from src.business.trading.models.portfolio import Portfolio  # noqa: F401
    from src.business.trading.models.portfolio_snapshot import PortfolioSnapshot  # noqa: F401
    from src.business.trading.models.position import Position  # noqa: F401
    from src.business.trading.models.trade import Trade  # noqa: F401
    from src.common.models.audit_log import AuditLog  # noqa: F401
    from src.common.models.user_settings import UserSettings  # noqa: F401
    from src.models.email_campaign import EmailCampaign  # noqa: F401
    from src.models.email_event import EmailEvent  # noqa: F401
    from src.models.email_preference import EmailPreference  # noqa: F401
    from src.models.email_send_log import EmailSendLog  # noqa: F401
    from src.models.email_token import EmailToken  # noqa: F401
    from src.models.market_data_bar import MarketDataBar  # noqa: F401
    from src.models.user import User  # noqa: F401
    from src.models.user_credentials import UserCredentials  # noqa: F401

    print("🔄 Resetting database using Alembic migrations...")

    # Use Alembic to downgrade to base (drops all tables)
    try:
        from alembic import command
        from alembic.config import Config

        alembic_cfg = Config(str(project_root / "alembic.ini"))

        # Override database URL from environment if present
        if database_url:
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        else:
            default_db_path = project_root / "src" / "trading_bot.db"
            alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{default_db_path}")

        # Check if alembic_version table exists
        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        if "alembic_version" in tables:
            print("  📉 Downgrading all migrations...")
            try:
                command.downgrade(alembic_cfg, "base")
                print("  ✅ All tables dropped")
            except Exception as e:
                print(f"  ⚠️  Downgrade failed: {e}")
                print("  📉 Falling back to db.drop_all()...")
                db.drop_all()
        else:
            print("  📉 No migrations found, using db.drop_all()...")
            db.drop_all()

        # Recreate all tables using migrations
        print("\n  📈 Creating all tables using migrations...")
        try:
            # Try to upgrade to head first (single head case)
            command.upgrade(alembic_cfg, "head")
            print("  ✅ All tables created from migrations")
        except Exception as upgrade_error:
            # If multiple heads exist, upgrade to all heads
            if "Multiple head revisions" in str(upgrade_error):
                print("Multiple migration heads detected, upgrading all heads...")
                command.upgrade(alembic_cfg, "heads")
                print("  ✅ All tables created from migrations (all heads)")
            else:
                raise  # Re-raise if it's a different error

        # If Alembic fails, fallback to Flask-SQLAlchemy
    except Exception as e:
        print(f"  ⚠️  Alembic migration failed: {e}")
        print("  📉 Falling back to db.drop_all() and db.create_all()...")
        db.drop_all()
        db.create_all()
        print("  ✅ Tables created using Flask-SQLAlchemy (fallback)")

    # Close all database connections
    db.session.close()
    try:
        if hasattr(db, "engine"):
            db.engine.dispose()
    except Exception:
        pass  # Ignore errors when disposing engine

    # Ensure database file has write permissions after reset (SQLite only)
    if (
        (not database_url or database_url.startswith("sqlite"))
        and database_path
        and os.path.exists(database_path)
    ):
        with suppress(OSError):
            os.chmod(database_path, 0o664)  # Make writable

    print("\n✅ Database reset complete!")
    print("\nAll tables have been dropped and recreated using Alembic migrations:")
    print("  - Flask-SQLAlchemy tables: users, email_tokens, user_credentials, market_data_bars")
    print("  - BaseModel tables: portfolios, positions, orders, trades, portfolio_snapshots,")
    print("                      strategies, signals, backtest_results, user_settings, audit_log")
    print("\n⚠️  IMPORTANT:")
    print("  - All user accounts have been deleted")
    print("  - All trading data has been deleted")
    print("  - You MUST log out and log back in (or clear browser cookies) to reset your session")
    print("  - Default admin user will be created on next app startup")
    print("\n💡 To fully reset your session:")
    print("  1. Log out from the web interface, OR")
    print("  2. Clear your browser cookies for this site, OR")
    print("  3. Use an incognito/private browsing window")
