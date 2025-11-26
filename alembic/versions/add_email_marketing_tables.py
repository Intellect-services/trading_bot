"""Add marketing email tracking tables.

Revision ID: add_email_marketing_tables
Revises: add_user_auth_features
Create Date: 2025-11-26
"""

from __future__ import annotations

import secrets
from datetime import datetime

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_email_marketing_tables"
down_revision = "add_user_auth_features"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create email marketing tables and seed defaults."""
    op.create_table(
        "email_campaigns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("campaign_type", sa.String(length=60), nullable=False),
        sa.Column(
            "schedule_strategy", sa.String(length=20), nullable=False, server_default="recurring"
        ),
        sa.Column("cadence_minutes", sa.Integer(), nullable=True, server_default="1440"),
        sa.Column("max_emails_per_run", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("next_run_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("audience_rules", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_email_campaigns_slug", "email_campaigns", ["slug"], unique=True)

    op.create_table(
        "email_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("marketing_opt_in", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column(
            "transactional_opt_in", sa.Boolean(), nullable=False, server_default=sa.text("1")
        ),
        sa.Column("unsubscribe_token", sa.String(length=64), nullable=False),
        sa.Column("unsubscribed_at", sa.DateTime(), nullable=True),
        sa.Column("last_sent_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_unique_constraint("uq_email_preferences_user_id", "email_preferences", ["user_id"])
    op.create_unique_constraint(
        "uq_email_preferences_unsubscribe_token", "email_preferences", ["unsubscribe_token"]
    )

    op.create_table(
        "email_send_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["email_campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_email_send_logs_user_id", "email_send_logs", ["user_id"], unique=False)
    op.create_index(
        "ix_email_send_logs_campaign_id", "email_send_logs", ["campaign_id"], unique=False
    )

    # Seed default campaigns
    campaign_defaults = [
        (
            "welcome_series",
            "Welcome Series",
            "Guided onboarding series",
            "welcome_series",
            1440,
            200,
        ),
        (
            "product_update",
            "Product Pulse",
            "Monthly product highlights",
            "product_update",
            10080,
            1000,
        ),
        (
            "market_briefing",
            "Market Briefing",
            "Weekly macro digest",
            "market_briefing",
            10080,
            750,
        ),
        (
            "education_series",
            "Education Series",
            "Automation curriculum drops",
            "education_series",
            20160,
            750,
        ),
        ("reengagement", "Re-engagement", "Win-back automation", "reengagement", 4320, 250),
    ]
    bind = op.get_bind()
    now = datetime.utcnow()
    existing_slugs = {row[0] for row in bind.execute(sa.text("SELECT slug FROM email_campaigns"))}
    for slug, name, description, campaign_type, cadence, max_run in campaign_defaults:
        if slug in existing_slugs:
            continue
        bind.execute(
            sa.text(
                """
                INSERT INTO email_campaigns
                (slug, name, description, campaign_type, cadence_minutes, max_emails_per_run, next_run_at, created_at, updated_at)
                VALUES (:slug, :name, :description, :campaign_type, :cadence_minutes, :max_emails_per_run, :next_run_at, :now, :now)
                """
            ),
            {
                "slug": slug,
                "name": name,
                "description": description,
                "campaign_type": campaign_type,
                "cadence_minutes": cadence,
                "max_emails_per_run": max_run,
                "next_run_at": now,
                "now": now,
            },
        )

    # Seed preferences for existing users
    user_ids = [row[0] for row in bind.execute(sa.text("SELECT id FROM users"))]
    existing_pref_users = {
        row[0] for row in bind.execute(sa.text("SELECT user_id FROM email_preferences"))
    }
    for user_id in user_ids:
        if user_id in existing_pref_users:
            continue
        bind.execute(
            sa.text(
                """
                INSERT INTO email_preferences
                    (user_id, marketing_opt_in, transactional_opt_in, unsubscribe_token, created_at, updated_at)
                VALUES (:user_id, 1, 1, :token, :now, :now)
                """
            ),
            {
                "user_id": user_id,
                "token": secrets.token_urlsafe(24),
                "now": now,
            },
        )


def downgrade() -> None:
    """Drop marketing email tables."""
    op.drop_index("ix_email_send_logs_campaign_id", table_name="email_send_logs")
    op.drop_index("ix_email_send_logs_user_id", table_name="email_send_logs")
    op.drop_table("email_send_logs")

    op.drop_constraint(
        "uq_email_preferences_unsubscribe_token", "email_preferences", type_="unique"
    )
    op.drop_constraint("uq_email_preferences_user_id", "email_preferences", type_="unique")
    op.drop_table("email_preferences")

    op.drop_index("ix_email_campaigns_slug", table_name="email_campaigns")
    op.drop_table("email_campaigns")
