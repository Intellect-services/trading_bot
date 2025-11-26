#!/usr/bin/env python3
"""DEPRECATED: Create user_settings table if it doesn't exist.

⚠️  This script is deprecated. Use Alembic migrations instead:
    python scripts/migrate.py upgrade head

All tables are now managed through Alembic migrations. See:
- docs/database/MIGRATION_GUIDE.md
- scripts/migrate.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask

from src.database import db, init_db

app = Flask(__name__)
init_db(app)

with app.app_context():
    # Check if user_settings table exists
    result = db.session.execute(
        db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'")
    )
    if result.fetchone():
        print("✅ user_settings table already exists")
    else:
        print("Creating user_settings table...")
        db.session.execute(
            db.text(
                """
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                key VARCHAR(100) NOT NULL,
                value TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, key)
            )
        """
            )
        )

        # Create indexes
        db.session.execute(
            db.text(
                """
            CREATE INDEX IF NOT EXISTS ix_user_settings_id ON user_settings(id)
        """
            )
        )
        db.session.execute(
            db.text(
                """
            CREATE INDEX IF NOT EXISTS ix_user_settings_key ON user_settings(key)
        """
            )
        )
        db.session.execute(
            db.text(
                """
            CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id)
        """
            )
        )

        db.session.commit()
        print("✅ user_settings table created successfully!")
