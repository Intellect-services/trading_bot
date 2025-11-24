"""Development configuration."""

import os


class DevelopmentConfig:
    """Development configuration settings."""

    # Flask settings
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    FLASK_ENV = "development"
    DEBUG = True
    TESTING = False

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///./src/trading_bot.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session
    SESSION_TYPE = "filesystem"
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]  # noqa: RUF012

    # Email
    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@intellectscout.com")
    APP_URL = os.getenv("APP_URL", "http://localhost:5002")

    # Encryption
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
