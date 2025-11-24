"""Database configuration and initialization."""

import os
from typing import TYPE_CHECKING

from flask_sqlalchemy import SQLAlchemy

if TYPE_CHECKING:
    from flask import Flask

db = SQLAlchemy()


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
        app.config[
            "SQLALCHEMY_DATABASE_URI"
        ] = f"sqlite:///{os.path.join(basedir, 'trading_bot.db')}"

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        # Import models here to avoid circular imports
        from src.models.email_token import EmailToken  # noqa: F401
        from src.models.user import User

        # Create all tables
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
