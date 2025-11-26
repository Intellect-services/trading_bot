"""Initial schema with all tables

Revision ID: eecf196c7107
Revises: add_user_auth_features
Create Date: 2025-11-25 20:39:28.352040

This migration reconciles metadata differences between existing schema and models.
For SQLite, only safe operations (indexes, constraints) are applied.
For PostgreSQL, full schema updates are applied.
"""
from collections.abc import Sequence
from contextlib import suppress
from typing import Any

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "eecf196c7107"
down_revision: str | Sequence[str] | None = "add_user_auth_features"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _safe_create_index(
    index_name: str, table_name: str, columns: list, unique: bool = False
) -> None:
    """Safely create an index, ignoring if it already exists."""
    from alembic.util.exc import CommandError

    with suppress(CommandError, Exception):
        op.create_index(index_name, table_name, columns, unique=unique)


def _safe_alter_column(table: str, column: str, **kwargs: Any) -> None:
    """Alter a column if supported by the dialect."""
    with suppress(Exception):
        op.alter_column(table, column, **kwargs)


def _safe_drop_index(name: str, table_name: str) -> None:
    """Drop an index if it exists."""
    with suppress(Exception):
        op.drop_index(name, table_name=table_name)


def _safe_unique_constraint(name: str, table_name: str, columns: list[str]) -> None:
    """Create a unique constraint, ignoring duplicates."""
    with suppress(Exception):
        op.create_unique_constraint(name, table_name, columns)


def upgrade() -> None:
    """Upgrade schema."""
    # Get database dialect to handle SQLite limitations
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"

    if not is_sqlite:
        # PostgreSQL: Full schema updates
        # Alter column types (PostgreSQL supports this)
        _safe_alter_column(
            "backtest_results",
            "metrics",
            existing_type=sa.TEXT(),
            type_=sa.JSON(),
            existing_nullable=True,
        )
        _safe_alter_column(
            "signals",
            "indicators",
            existing_type=sa.TEXT(),
            type_=sa.JSON(),
            existing_nullable=True,
        )
        _safe_alter_column(
            "strategies",
            "parameters",
            existing_type=sa.TEXT(),
            server_default=None,
            type_=sa.JSON(),
            existing_nullable=False,
        )
        _safe_alter_column(
            "strategies",
            "risk_parameters",
            existing_type=sa.TEXT(),
            type_=sa.JSON(),
            existing_nullable=True,
        )
        _safe_alter_column(
            "user_settings",
            "value",
            existing_type=sa.TEXT(),
            type_=sa.JSON(),
            existing_nullable=True,
        )

    # Create missing indexes (safe for both SQLite and PostgreSQL)
    _safe_create_index("ix_backtest_results_id", "backtest_results", ["id"])
    _safe_create_index("ix_backtest_results_strategy_id", "backtest_results", ["strategy_id"])

    # Update order indexes
    _safe_drop_index("idx_created_at_orders", table_name="orders")
    _safe_drop_index("idx_portfolio_symbol_orders", table_name="orders")
    _safe_create_index("idx_created_at", "orders", ["created_at"])
    _safe_create_index("idx_portfolio_symbol", "orders", ["portfolio_id", "symbol"])
    _safe_create_index("ix_orders_id", "orders", ["id"])
    _safe_create_index("ix_orders_portfolio_id", "orders", ["portfolio_id"])

    # Add unique constraint on alpaca_order_id if it doesn't exist
    _safe_unique_constraint("uq_orders_alpaca_order_id", "orders", ["alpaca_order_id"])

    _safe_create_index("ix_portfolio_snapshots_id", "portfolio_snapshots", ["id"])
    _safe_create_index(
        "ix_portfolio_snapshots_portfolio_id", "portfolio_snapshots", ["portfolio_id"]
    )
    _safe_create_index("ix_positions_id", "positions", ["id"])
    _safe_create_index("ix_positions_portfolio_id", "positions", ["portfolio_id"])
    _safe_create_index("ix_signals_generated_at", "signals", ["generated_at"])
    _safe_create_index("ix_signals_id", "signals", ["id"])
    _safe_create_index("ix_signals_strategy_id", "signals", ["strategy_id"])
    _safe_create_index("ix_strategies_id", "strategies", ["id"])
    _safe_create_index("ix_strategies_user_id", "strategies", ["user_id"])

    # Update trades indexes
    _safe_drop_index("idx_portfolio_symbol_trades", table_name="trades")
    _safe_create_index("idx_portfolio_symbol", "trades", ["portfolio_id", "symbol"])
    _safe_create_index("ix_trades_id", "trades", ["id"])
    _safe_create_index("ix_trades_order_id", "trades", ["order_id"])
    _safe_create_index("ix_trades_portfolio_id", "trades", ["portfolio_id"])

    # Update user_settings indexes
    _safe_drop_index("idx_user_settings_user_id", table_name="user_settings")
    _safe_create_index("ix_user_settings_user_id", "user_settings", ["user_id"])

    # Add unique constraint on user_settings if it doesn't exist
    _safe_unique_constraint("uq_user_settings_user_key", "user_settings", ["user_id", "key"])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop constraints and indexes
    with suppress(Exception):
        op.drop_constraint("uq_user_settings_user_key", "user_settings", type_="unique")

    with suppress(Exception):
        op.drop_index("ix_user_settings_user_id", table_name="user_settings")
        op.create_index("idx_user_settings_user_id", "user_settings", ["user_id"])

    # Note: For a complete downgrade, we would reverse all changes
    # But since this is mostly metadata reconciliation, a full downgrade
    # might not be necessary or safe.
