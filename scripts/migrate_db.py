#!/usr/bin/env python3
"""Database migration script to add new columns to users table and create new tables."""

import os
import sqlite3
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def migrate_database():
    """Migrate database schema to add new authentication features."""
    # Get database path from environment or use default
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        # Default SQLite path
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        database_url = f"sqlite:///{os.path.join(project_root, 'src', 'trading_bot.db')}"

    if "sqlite" in database_url.lower():
        # SQLite migration
        db_path = database_url.replace("sqlite:///", "")
        if not os.path.isabs(db_path):
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(project_root, db_path)

        if not os.path.exists(db_path):
            print(f"❌ Database file not found: {db_path}")
            return False

        print(f"📁 Database: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            # Check if columns already exist
            cursor.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cursor.fetchall()]

            # Add new columns to users table if they don't exist
            if "email_verified" not in columns:
                print("  ✓ Adding email_verified column to users table...")
                cursor.execute("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0")

            if "email_verification_token" not in columns:
                print("  ✓ Adding email_verification_token column to users table...")
                cursor.execute("ALTER TABLE users ADD COLUMN email_verification_token VARCHAR(255)")

            if "email_verification_sent_at" not in columns:
                print("  ✓ Adding email_verification_sent_at column to users table...")
                cursor.execute("ALTER TABLE users ADD COLUMN email_verification_sent_at DATETIME")

            if "role" not in columns:
                print("  ✓ Adding role column to users table...")
                cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'trader'")

            # Create index on email_verification_token if it doesn't exist
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='ix_users_email_verification_token'"
            )
            if not cursor.fetchone():
                print("  ✓ Creating index on email_verification_token...")
                cursor.execute(
                    "CREATE INDEX ix_users_email_verification_token ON users(email_verification_token)"
                )

            # Create user_credentials table if it doesn't exist
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='user_credentials'"
            )
            if not cursor.fetchone():
                print("  ✓ Creating user_credentials table...")
                cursor.execute(
                    """
                    CREATE TABLE user_credentials (
                        id INTEGER NOT NULL PRIMARY KEY,
                        user_id INTEGER NOT NULL UNIQUE,
                        alpaca_api_key_encrypted TEXT,
                        alpaca_secret_key_encrypted TEXT,
                        trading_mode VARCHAR(20) NOT NULL DEFAULT 'paper',
                        is_active BOOLEAN NOT NULL DEFAULT 0,
                        last_verified_at DATETIME,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        FOREIGN KEY(user_id) REFERENCES users (id)
                    )
                """
                )
                cursor.execute(
                    "CREATE INDEX ix_user_credentials_user_id ON user_credentials(user_id)"
                )

            # Create email_tokens table if it doesn't exist
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='email_tokens'"
            )
            if not cursor.fetchone():
                print("  ✓ Creating email_tokens table...")
                cursor.execute(
                    """
                    CREATE TABLE email_tokens (
                        id INTEGER NOT NULL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        token VARCHAR(255) NOT NULL UNIQUE,
                        token_type VARCHAR(50) NOT NULL,
                        expires_at DATETIME NOT NULL,
                        used_at DATETIME,
                        created_at DATETIME NOT NULL,
                        FOREIGN KEY(user_id) REFERENCES users (id)
                    )
                """
                )
                cursor.execute("CREATE INDEX ix_email_tokens_token ON email_tokens(token)")
                cursor.execute("CREATE INDEX ix_email_tokens_user_id ON email_tokens(user_id)")

            # Update existing users to have email_verified=True and role='trader' if not set
            cursor.execute("UPDATE users SET email_verified = 1 WHERE email_verified IS NULL")
            cursor.execute("UPDATE users SET role = 'trader' WHERE role IS NULL")

            # Set owner role for admin user
            cursor.execute(
                "UPDATE users SET role = 'owner', email_verified = 1 WHERE email = 'admin@admin.com'"
            )

            conn.commit()
            print("\n✅ Database migration completed successfully!")
            return True

        except Exception as e:
            conn.rollback()
            print(f"\n❌ Migration failed: {e}")
            import traceback

            traceback.print_exc()
            return False
        finally:
            conn.close()
    else:
        # For PostgreSQL or other databases
        print("⚠️  PostgreSQL migration - please run Alembic migrations or update manually")
        print("   For now, this script only supports SQLite")
        return False


if __name__ == "__main__":
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Database Migration Script")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    if migrate_database():
        sys.exit(0)
    else:
        sys.exit(1)
