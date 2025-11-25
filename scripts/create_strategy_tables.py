#!/usr/bin/env python3
"""Create strategy tables manually using SQL to avoid foreign key metadata issues."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask

from src.database import db, init_db


def create_strategy_tables():
    """Create strategy tables using raw SQL."""
    app = Flask(__name__)
    init_db(app)  # Creates users table first

    with app.app_context():
        # Check if strategies table already exists
        result = db.session.execute(
            db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='strategies'")
        )
        if result.fetchone():
            print("✅ strategies table already exists")
            return True

        print("Creating strategies, signals, and backtest_results tables...")

        # Create strategies table
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

        print("✅ All strategy tables created successfully!")
        print("   - strategies")
        print("   - signals")
        print("   - backtest_results")
        return True


if __name__ == "__main__":
    try:
        success = create_strategy_tables()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
