"""Database configuration and initialization."""

import os
from typing import TYPE_CHECKING

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.pool import StaticPool

if TYPE_CHECKING:
    from flask import Flask

db = SQLAlchemy()


def _create_user_settings_table(app: "Flask") -> None:
    """Create user_settings table using SQL."""
    with app.app_context():
        # Check if user_settings table already exists
        result = db.session.execute(
            db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'")
        )
        if result.fetchone():
            return  # Table already exists

        # Create user_settings table
        db.session.execute(
            db.text(
                """
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                key VARCHAR(100) NOT NULL,
                value TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, key)
            )
        """
            )
        )

        # Create indexes on user_settings
        db.session.execute(
            db.text(
                """
            CREATE INDEX IF NOT EXISTS ix_user_settings_id ON user_settings(id)
        """
            )
        )
        db.session.execute(
            db.text(
                """
            CREATE INDEX IF NOT EXISTS ix_user_settings_key ON user_settings(key)
        """
            )
        )
        db.session.execute(
            db.text(
                """
            CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id)
        """
            )
        )

        db.session.commit()


def _create_base_model_tables(app: "Flask") -> None:
    """Create BaseModel tables (portfolios, positions, orders, trades, portfolio_snapshots, strategies, signals, backtest_results, user_settings) using SQL.

    This function uses raw SQL to create tables because they use a different
    SQLAlchemy Base than Flask-SQLAlchemy models, causing foreign key resolution issues.
    Tables are created in order to satisfy foreign key dependencies.
    """
    with app.app_context():
        # Check if portfolios table exists (this is the root of the BaseModel dependency tree)
        result = db.session.execute(
            db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='portfolios'")
        )
        if result.fetchone():
            # Check if strategies table exists (old check for backwards compatibility)
            result = db.session.execute(
                db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='strategies'")
            )
            if result.fetchone():
                # Check if user_settings exists too, if not create it
                result = db.session.execute(
                    db.text(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'"
                    )
                )
                if result.fetchone():
                    return  # All tables already exist
                # Only user_settings is missing, create it
                _create_user_settings_table(app)
                return

        # Create portfolios table FIRST (no dependencies on other BaseModel tables)
        db.session.execute(
            db.text(
                """
            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                initial_capital NUMERIC(15, 2) NOT NULL,
                current_value NUMERIC(15, 2),
                cash_balance NUMERIC(15, 2),
                buying_power NUMERIC(15, 2),
                is_paper BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """
            )
        )

        # Create indexes on portfolios
        db.session.execute(
            db.text(
                """
            CREATE INDEX IF NOT EXISTS ix_portfolios_id ON portfolios(id)
        """
            )
        )
        db.session.execute(
            db.text(
                """
            CREATE INDEX IF NOT EXISTS ix_portfolios_user_id ON portfolios(user_id)
        """
            )
        )

        # Create positions table (depends on portfolios)
        db.session.execute(
            db.text(
                """
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                symbol VARCHAR(10) NOT NULL,
                quantity NUMERIC(15, 4) NOT NULL,
                avg_entry_price NUMERIC(15, 4) NOT NULL,
                current_price NUMERIC(15, 4),
                market_value NUMERIC(15, 2),
                unrealized_pl NUMERIC(15, 2),
                unrealized_pl_percent NUMERIC(10, 4),
                side VARCHAR(10) NOT NULL,
                opened_at DATETIME NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
            )
        """
            )
        )

        # Create indexes on positions
        db.session.execute(
            db.text(
                """
            CREATE INDEX IF NOT EXISTS idx_portfolio_symbol ON positions(portfolio_id, symbol)
        """
            )
        )
        db.session.execute(
            db.text(
                """
            CREATE INDEX IF NOT EXISTS idx_opened_at ON positions(opened_at)
        """
            )
        )

        # Create orders table (depends on portfolios)
        db.session.execute(
            db.text(
                """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                alpaca_order_id VARCHAR(100) UNIQUE,
                symbol VARCHAR(10) NOT NULL,
                quantity NUMERIC(15, 4) NOT NULL,
                filled_quantity NUMERIC(15, 4) DEFAULT 0,
                side VARCHAR(10) NOT NULL,
                type VARCHAR(20) NOT NULL,
                time_in_force VARCHAR(10),
                status VARCHAR(20) NOT NULL,
                limit_price NUMERIC(15, 4),
                stop_price NUMERIC(15, 4),
                filled_avg_price NUMERIC(15, 4),
                commission NUMERIC(10, 4) DEFAULT 0,
                filled_at DATETIME,
                cancelled_at DATETIME,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
            )
        """
            )
        )

        # Create indexes on orders
        db.session.execute(
            db.text(
                """
            CREATE INDEX IF NOT EXISTS idx_portfolio_symbol_orders ON orders(portfolio_id, symbol)
        """
            )
        )
        db.session.execute(
            db.text(
                """
            CREATE INDEX IF NOT EXISTS idx_status ON orders(status)
        """
            )
        )
        db.session.execute(
            db.text(
                """
            CREATE INDEX IF NOT EXISTS idx_created_at_orders ON orders(created_at)
        """
            )
        )

        # Create trades table (depends on orders and portfolios)
        db.session.execute(
            db.text(
                """
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                portfolio_id INTEGER NOT NULL,
                symbol VARCHAR(10) NOT NULL,
                quantity NUMERIC(15, 4) NOT NULL,
                price NUMERIC(15, 4) NOT NULL,
                side VARCHAR(10) NOT NULL,
                commission NUMERIC(10, 4) DEFAULT 0,
                realized_pl NUMERIC(15, 2),
                executed_at DATETIME NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
            )
        """
            )
        )

        # Create indexes on trades
        db.session.execute(
            db.text(
                """
            CREATE INDEX IF NOT EXISTS idx_portfolio_symbol_trades ON trades(portfolio_id, symbol)
        """
            )
        )
        db.session.execute(
            db.text(
                """
            CREATE INDEX IF NOT EXISTS idx_executed_at ON trades(executed_at)
        """
            )
        )

        # Create portfolio_snapshots table (depends on portfolios)
        db.session.execute(
            db.text(
                """
            CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                total_value NUMERIC(15, 2) NOT NULL,
                cash_balance NUMERIC(15, 2) NOT NULL,
                positions_value NUMERIC(15, 2) NOT NULL,
                total_pl NUMERIC(15, 2),
                daily_pl NUMERIC(15, 2),
                snapshot_at DATETIME NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
            )
        """
            )
        )

        # Create index on portfolio_snapshots
        db.session.execute(
            db.text(
                """
            CREATE INDEX IF NOT EXISTS idx_portfolio_time ON portfolio_snapshots(portfolio_id, snapshot_at)
        """
            )
        )

        # Create strategies table (depends on users, not portfolios)
        db.session.execute(
            db.text(
                """
            CREATE TABLE IF NOT EXISTS strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                type VARCHAR(50) NOT NULL,
                parameters TEXT NOT NULL DEFAULT '{}',
                risk_parameters TEXT,
                is_active BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """
            )
        )

        # Create index on strategies
        db.session.execute(
            db.text(
                """
            CREATE INDEX IF NOT EXISTS idx_user_type ON strategies(user_id, type)
        """
            )
        )

        # Create signals table
        db.session.execute(
            db.text(
                """
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id INTEGER NOT NULL,
                symbol VARCHAR(10) NOT NULL,
                signal_type VARCHAR(10) NOT NULL,
                strength NUMERIC(5, 2),
                price NUMERIC(15, 4) NOT NULL,
                indicators TEXT,
                generated_at DATETIME NOT NULL,
                executed BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE CASCADE
            )
        """
            )
        )

        # Create indexes on signals
        db.session.execute(
            db.text(
                """
            CREATE INDEX IF NOT EXISTS idx_strategy_symbol ON signals(strategy_id, symbol)
        """
            )
        )
        db.session.execute(
            db.text(
                """
            CREATE INDEX IF NOT EXISTS idx_generated_at ON signals(generated_at)
        """
            )
        )

        # Create backtest_results table
        db.session.execute(
            db.text(
                """
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id INTEGER NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                initial_capital NUMERIC(15, 2) NOT NULL,
                final_value NUMERIC(15, 2) NOT NULL,
                total_return NUMERIC(10, 4),
                sharpe_ratio NUMERIC(10, 4),
                max_drawdown NUMERIC(10, 4),
                win_rate NUMERIC(10, 4),
                total_trades INTEGER,
                metrics TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE CASCADE
            )
        """
            )
        )

        # Create index on backtest_results
        db.session.execute(
            db.text(
                """
            CREATE INDEX IF NOT EXISTS idx_strategy_date ON backtest_results(strategy_id, end_date)
        """
            )
        )

        db.session.commit()

        # Create user_settings table
        _create_user_settings_table(app)


def init_db(app: "Flask") -> None:
    """Initialize the database with the Flask app."""
    # Check for DATABASE_URL (Railway/PostgreSQL) or use SQLite for local development
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
                    os.chmod(db_path, 0o664)  # Make writable
                # Also ensure WAL and SHM files are writable if they exist
                wal_path = f"{db_path}-wal"
                shm_path = f"{db_path}-shm"
                if os.path.exists(wal_path):
                    os.chmod(wal_path, 0o664)
                if os.path.exists(shm_path):
                    os.chmod(shm_path, 0o664)
            except OSError:
                pass  # Ignore permission errors if we can't change them

        ensure_write_permissions(database_path)

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        # Configure SQLite pragmas on connection for writability
        if not database_url or database_url.startswith("sqlite"):

            @event.listens_for(db.engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                """Set SQLite pragmas on each connection to ensure writability."""
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=DELETE")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA locking_mode=NORMAL")
                cursor.close()

        # Import models here to avoid circular imports
        # These imports ensure all Flask-SQLAlchemy models are registered with db before create_all()
        from src.models.market_data_bar import MarketDataBar  # noqa: F401
        from src.models.user import User
        from src.models.user_credentials import UserCredentials  # noqa: F401

        # Create all Flask-SQLAlchemy tables (users, email_tokens, user_credentials, market_data_bars) FIRST
        db.create_all()

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

        # Ensure user_credentials table exists (it's a Flask-SQLAlchemy model but might not be created)
        # Check if user_credentials table exists, if not create it
        result = db.session.execute(
            db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='user_credentials'")
        )
        if not result.fetchone():
            # Table doesn't exist, create it manually
            db.session.execute(
                db.text(
                    """
                CREATE TABLE IF NOT EXISTS user_credentials (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    alpaca_api_key_encrypted TEXT,
                    alpaca_secret_key_encrypted TEXT,
                    trading_mode VARCHAR(20) NOT NULL DEFAULT 'paper',
                    is_active BOOLEAN NOT NULL DEFAULT 0,
                    last_verified_at DATETIME,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """
                )
            )
            db.session.execute(
                db.text(
                    "CREATE INDEX IF NOT EXISTS ix_user_credentials_user_id ON user_credentials(user_id)"
                )
            )
            db.session.commit()
            print("Created user_credentials table")

        # Create BaseModel tables (strategies, signals, backtest_results, user_settings) using SQL
        # This must be done AFTER users table is created
        try:
            _create_base_model_tables(app)
            # Also ensure user_settings exists (in case only strategies table existed)
            _create_user_settings_table(app)
        except Exception as e:
            # Log but don't fail - tables might already exist
            import logging

            logging.getLogger(__name__).warning(f"Could not create BaseModel tables: {e}")
