"""Add email events table and delivery metrics columns.

Revision ID: add_email_event_metrics
Revises: add_email_marketing_tables
Create Date: 2025-11-26
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_email_event_metrics"
down_revision = "add_email_marketing_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "email_send_logs",
        sa.Column("last_event_type", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "email_send_logs",
        sa.Column("last_event_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "email_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("send_log_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.ForeignKeyConstraint(["send_log_id"], ["email_send_logs.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_email_events_send_log_id", "email_events", ["send_log_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_email_events_send_log_id", table_name="email_events")
    op.drop_table("email_events")
    op.drop_column("email_send_logs", "last_event_at")
    op.drop_column("email_send_logs", "last_event_type")
