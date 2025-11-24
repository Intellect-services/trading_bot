"""Staging configuration."""

import os
from typing import Any


class StagingConfig:
    """Staging configuration settings."""

    # Flask settings
    SECRET_KEY = os.getenv("SECRET_KEY")
    FLASK_ENV = "staging"
    DEBUG = True
    TESTING = False

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS: dict[str, Any] = {  # noqa: RUF012
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "connect_args": {"sslmode": "require"}
        if os.getenv("DATABASE_URL", "").startswith("postgresql")
        else {},
    }

    # Session
    SESSION_TYPE = os.getenv("SESSION_TYPE", "filesystem")
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

    # CORS
    CORS_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://staging.intellectscout.com").split(",")

    # Email
    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@intellectscout.com")
    APP_URL = os.getenv("APP_URL", "https://staging.intellectscout.com")

    # Encryption
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
