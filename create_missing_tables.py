#!/usr/bin/env python3
"""Create missing database tables."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


from src.infrastructure import db_config


def create_missing_tables():
    """Create missing tables."""
    print("Creating missing tables...")

    try:
        # Import all models to ensure they're registered
        from src.infrastructure.base_model import Base

        # Create all tables
        engine = db_config.engine
        Base.metadata.create_all(engine, checkfirst=True)

        print("✅ All tables created successfully")
        return True

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False


if __name__ == "__main__":
    success = create_missing_tables()
    sys.exit(0 if success else 1)
