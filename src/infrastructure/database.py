"""Database configuration and session management."""

import os
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.infrastructure.base_model import Base


class DatabaseConfig:
    """Database configuration and connection management."""

    def __init__(self, database_url: str | None = None):
        """Initialize database configuration.

        Args:
            database_url: Database connection URL. If None, uses environment variable or defaults to SQLite.
        """
        if database_url is None:
            database_url = os.getenv("DATABASE_URL", "sqlite:///./src/trading_bot.db")

        self.database_url = database_url
        self.is_sqlite = database_url.startswith("sqlite")

        # Create engine with appropriate settings
        if self.is_sqlite:
            self.engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=os.getenv("SQL_ECHO", "false").lower() == "true",
            )

            # Enable foreign keys for SQLite
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_conn: Any, connection_record: Any) -> None:  # noqa: ARG001
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        else:
            # PostgreSQL configuration
            self.engine = create_engine(
                database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=os.getenv("SQL_ECHO", "false").lower() == "true",
            )

        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_all_tables(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)

    def drop_all_tables(self) -> None:
        """Drop all database tables. Use with caution!"""
        Base.metadata.drop_all(bind=self.engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup.

        Yields:
            Database session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_db(self) -> Generator[Session, None, None]:
        """Dependency for FastAPI/Flask to get database session.

        Yields:
            Database session
        """
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()


# Global database instance
db_config = DatabaseConfig()


# Convenience function for getting sessions
def get_db_session() -> Generator[Session, None, None]:
    """Get a database session.

    Yields:
        Database session
    """
    return db_config.get_db()
