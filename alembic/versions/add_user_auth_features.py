"""Add user authentication features

Revision ID: add_user_auth_features
Revises: f9179e223e34
Create Date: 2025-01-XX XX:XX:XX

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_user_auth_features"
down_revision = "f9179e223e34"  # Update this to match your latest migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add user authentication features."""
    # Add columns to users table
    op.add_column(
        "users", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="0")
    )
    op.add_column(
        "users", sa.Column("email_verification_token", sa.String(length=255), nullable=True)
    )
    op.add_column("users", sa.Column("email_verification_sent_at", sa.DateTime(), nullable=True))
    op.add_column(
        "users", sa.Column("role", sa.String(length=20), nullable=False, server_default="trader")
    )

    # Create index on email_verification_token
    op.create_index(
        "ix_users_email_verification_token", "users", ["email_verification_token"], unique=False
    )

    # Create user_credentials table
    op.create_table(
        "user_credentials",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("alpaca_api_key_encrypted", sa.Text(), nullable=True),
        sa.Column("alpaca_secret_key_encrypted", sa.Text(), nullable=True),
        sa.Column("trading_mode", sa.String(length=20), nullable=False, server_default="paper"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("last_verified_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_user_credentials_user_id", "user_credentials", ["user_id"], unique=False)

    # Create email_tokens table
    op.create_table(
        "email_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("token_type", sa.String(length=50), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index("ix_email_tokens_token", "email_tokens", ["token"], unique=False)
    op.create_index("ix_email_tokens_user_id", "email_tokens", ["user_id"], unique=False)


def downgrade() -> None:
    """Remove user authentication features."""
    # Drop email_tokens table
    op.drop_index("ix_email_tokens_user_id", table_name="email_tokens")
    op.drop_index("ix_email_tokens_token", table_name="email_tokens")
    op.drop_table("email_tokens")

    # Drop user_credentials table
    op.drop_index("ix_user_credentials_user_id", table_name="user_credentials")
    op.drop_table("user_credentials")

    # Remove columns from users table
    op.drop_index("ix_users_email_verification_token", table_name="users")
    op.drop_column("users", "role")
    op.drop_column("users", "email_verification_sent_at")
    op.drop_column("users", "email_verification_token")
    op.drop_column("users", "email_verified")
