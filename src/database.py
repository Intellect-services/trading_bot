"""Database configuration and initialization.

This module handles database setup using Alembic migrations for schema management.
All tables are created and managed through migrations, ensuring database-agnostic code.
"""

import os
from typing import TYPE_CHECKING

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.pool import StaticPool

if TYPE_CHECKING:
    from flask import Flask

db = SQLAlchemy()

if TYPE_CHECKING:
    # Re-export the SQLAlchemy model base class for type checking.
    # At runtime this is provided by Flask-SQLAlchemy via db.Model.
    from flask_sqlalchemy.model import Model as SQLAlchemyModel
else:  # pragma: no cover - simple runtime alias
    SQLAlchemyModel = db.Model


def init_db(app: "Flask") -> None:
    """Initialize the database with the Flask app.

    This function configures the database connection and runs Alembic migrations
    to ensure the schema is up-to-date. It supports both SQLite (local) and
    PostgreSQL (production) databases.

    Args:
        app: Flask application instance
    """
    # Check for DATABASE_URL (PostgreSQL) or use SQLite for local development
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        # PostgreSQL (production/staging)
        # Railway provides DATABASE_URL in format: postgresql://user:pass@host:port/dbname
        # SQLAlchemy expects postgresql:// but some providers use postgres://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_pre_ping": True,
            "pool_recycle": 300,
            "connect_args": {"sslmode": "require"} if "railway" in database_url.lower() else {},
        }
    else:
        # SQLite (local development)
        basedir = os.path.abspath(os.path.dirname(__file__))
        database_path = os.path.join(basedir, "trading_bot.db")
        database_url = f"sqlite:///{database_path}"
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url

        # SQLite-specific configuration for concurrent access
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "connect_args": {
                "check_same_thread": False,  # Allow multi-threaded access
                "timeout": 30,  # Wait up to 30 seconds for locks
            },
            "poolclass": StaticPool,  # Use StaticPool for SQLite
            "pool_pre_ping": False,  # Not needed for SQLite
        }

        # Ensure database directory exists and has write permissions
        database_dir = os.path.dirname(database_path)
        if not os.path.exists(database_dir):
            os.makedirs(database_dir, mode=0o755, exist_ok=True)

        # Ensure database file and related files have write permissions
        def ensure_write_permissions(db_path: str) -> None:
            """Ensure database file and all related files are writable."""
            try:
                if os.path.exists(db_path):
                    # SQLite files must be writable by the app process.
                    # Use a moderately permissive mask that avoids world-writable bits.
                    os.chmod(db_path, 0o660)  # nosec B103
                # Also ensure WAL and SHM files are writable if they exist
                wal_path = f"{db_path}-wal"
                shm_path = f"{db_path}-shm"
                if os.path.exists(wal_path):
                    os.chmod(wal_path, 0o660)  # nosec B103
                if os.path.exists(shm_path):
                    os.chmod(shm_path, 0o660)  # nosec B103
            except OSError:
                pass  # Ignore permission errors if we can't change them

        ensure_write_permissions(database_path)

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # Configure SQLite pragmas on connection for writability
    # This must be done after db.init_app() within an app context
    with app.app_context():
        if not database_url or database_url.startswith("sqlite"):

            @event.listens_for(db.engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):  # noqa: ARG001
                """Set SQLite pragmas on each connection to ensure writability."""
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=DELETE")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA locking_mode=NORMAL")
                cursor.close()

    with app.app_context():
        # Import models here to avoid circular imports
        # These imports ensure all Flask-SQLAlchemy models are registered with db before migrations
        # Import all BaseModel classes to ensure they're registered
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
        from src.models.user import User
        from src.models.user_credentials import UserCredentials  # noqa: F401

        # Run Alembic migrations to create/update schema
        # This ensures all tables are created according to the migration definitions
        try:
            from alembic import command
            from alembic.config import Config

            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)

            # Check if alembic_version table exists (indicates migrations have been run)
            from sqlalchemy import inspect

            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            if "alembic_version" not in tables:
                # First time setup - create initial schema
                # Create Flask-SQLAlchemy tables
                db.create_all()
                # Create BaseModel tables using their metadata
                from src.infrastructure.base_model import Base

                Base.metadata.create_all(bind=db.engine, checkfirst=True)

                # Stamp the database with the latest migration revision
                # This marks the database as being at the current migration state
                try:
                    # Get the latest revision from the migrations
                    from alembic.script import ScriptDirectory

                    script = ScriptDirectory.from_config(alembic_cfg)
                    head_revision = script.get_current_head()
                    if head_revision:
                        command.stamp(alembic_cfg, head_revision)
                except Exception as exc:  # nosec B110 - safe best-effort stamping
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.debug("Failed to stamp Alembic head revision: %s", exc)
            else:
                # Database has migrations - run them to ensure schema is up-to-date
                try:
                    # Try to upgrade to head first (single head case)
                    command.upgrade(alembic_cfg, "head")
                except Exception as e:
                    # If multiple heads exist, upgrade to all heads
                    if "Multiple head revisions" in str(e):
                        import logging

                        logger = logging.getLogger(__name__)
                        logger.info("Multiple migration heads detected, upgrading all heads...")
                        command.upgrade(alembic_cfg, "heads")
                    else:
                        # If migration fails for other reasons, create all tables as fallback
                        import logging

                        logger = logging.getLogger(__name__)
                        logger.warning(f"Migration failed: {e}. Creating all tables as fallback.")
                        # Create Flask-SQLAlchemy tables
                        db.create_all()
                        # Create BaseModel tables
                        from src.infrastructure.base_model import Base

                        Base.metadata.create_all(bind=db.engine, checkfirst=True)

        except Exception as e:
            # Fallback to creating all tables if Alembic is not available
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Alembic not available: {e}. Creating all tables as fallback.")
            # Create Flask-SQLAlchemy tables
            db.create_all()
            # Create BaseModel tables
            from src.infrastructure.base_model import Base

            Base.metadata.create_all(bind=db.engine, checkfirst=True)

        # Final safety check: ensure all required tables exist
        # This is a last resort if something went wrong above
        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        existing_tables = set(inspector.get_table_names())

        # Required Flask-SQLAlchemy tables
        required_flask_tables = {
            "users",
            "user_credentials",
            "email_tokens",
            "market_data_bars",
            "email_campaigns",
            "email_preferences",
            "email_send_logs",
            "email_events",
        }
        missing_flask = required_flask_tables - existing_tables

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
        missing_base = required_base_tables - existing_tables

        if missing_flask or missing_base:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"Missing tables detected. Flask: {missing_flask}, BaseModel: {missing_base}. Creating them now."
            )

            if missing_flask:
                db.create_all()

            if missing_base:
                from src.infrastructure.base_model import Base

                Base.metadata.create_all(bind=db.engine, checkfirst=True)

        # Create default owner user if it doesn't exist
        owner = User.query.filter_by(email="admin@admin.com").first()
        if not owner:
            owner = User(
                email="admin@admin.com",
                name="Admin User",
                avatar="https://ui-avatars.com/api/?name=Admin+User&background=667eea&color=fff",
                role="owner",
                email_verified=True,  # Auto-verify owner account
            )
            owner.set_password("admin")
            db.session.add(owner)
            db.session.commit()
            print("Created default owner user")
