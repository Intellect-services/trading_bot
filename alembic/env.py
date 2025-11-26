"""Alembic environment configuration for database migrations.

This module configures Alembic to track both Flask-SQLAlchemy models (db.Model)
and BaseModel classes, allowing migrations to manage all database tables.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import MetaData, engine_from_config, pool

from alembic import context

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# =============================================================================
# IMPORT ALL MODELS FOR AUTOGENERATE SUPPORT
# =============================================================================
# Import Flask app and database to get Flask-SQLAlchemy metadata
from dotenv import load_dotenv
from flask import Flask

load_dotenv()

# Create a temporary Flask app to initialize Flask-SQLAlchemy
app = Flask(__name__)
database_url = os.getenv("DATABASE_URL", "sqlite:///./src/trading_bot.db")

# Convert postgres:// to postgresql:// if needed
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

if database_url.startswith("sqlite"):
    # SQLite configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "connect_args": {"check_same_thread": False, "timeout": 30},
        "poolclass": pool.StaticPool,
        "pool_pre_ping": False,
    }
else:
    # PostgreSQL configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "connect_args": {"sslmode": "require"} if "railway" in database_url.lower() else {},
    }

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize Flask-SQLAlchemy
from src.database import db

db.init_app(app)

# Import BaseModel metadata
from src.infrastructure.base_model import Base

# Import all Flask-SQLAlchemy models to register them with db.metadata
with app.app_context():
    # Import all BaseModel classes to register them with Base.metadata
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
    from src.models.email_token import EmailToken  # noqa: F401
    from src.models.market_data_bar import MarketDataBar  # noqa: F401
    from src.models.user import User  # noqa: F401
    from src.models.user_credentials import UserCredentials  # noqa: F401

    # Combine metadata from both Flask-SQLAlchemy and BaseModel
    # Flask-SQLAlchemy uses db.metadata, BaseModel uses Base.metadata
    target_metadata = MetaData()

    # Add all tables from Flask-SQLAlchemy metadata
    for _table_name, table in db.metadata.tables.items():
        table.tometadata(target_metadata)

    # Add all tables from BaseModel metadata
    for table_name, table in Base.metadata.tables.items():
        # Only add if not already present (avoid duplicates)
        if table_name not in target_metadata.tables:
            table.tometadata(target_metadata)

# Override sqlalchemy.url from environment variable if present
config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
