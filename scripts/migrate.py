#!/usr/bin/env python3
"""Database migration CLI script using Alembic.

This script provides a convenient interface for running database migrations
across all environments (local, staging, production).

Usage:
    python scripts/migrate.py upgrade head          # Run all migrations
    python scripts/migrate.py downgrade -1          # Rollback one migration
    python scripts/migrate.py current               # Show current revision
    python scripts/migrate.py history               # Show migration history
    python scripts/migrate.py revision --autogenerate -m "description"  # Create new migration
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

# Import Alembic command
from alembic import command
from alembic.config import Config


def get_alembic_config() -> Config:
    """Get Alembic configuration.

    Returns:
        Configured Alembic Config object
    """
    alembic_cfg = Config(str(project_root / "alembic.ini"))

    # Override database URL from environment if present
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Convert postgres:// to postgresql:// if needed
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    else:
        # Default to SQLite for local development
        default_db_path = project_root / "src" / "trading_bot.db"
        alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{default_db_path}")

    return alembic_cfg


def main() -> None:
    """Main entry point for migration CLI."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    alembic_cfg = get_alembic_config()
    command_name = sys.argv[1]
    args = sys.argv[2:]

    try:
        if command_name == "upgrade":
            revision = args[0] if args else "head"
            print(f"🔄 Upgrading database to revision: {revision}")
            command.upgrade(alembic_cfg, revision)
            print("✅ Database upgrade completed!")

        elif command_name == "downgrade":
            revision = args[0] if args else "-1"
            print(f"🔄 Downgrading database to revision: {revision}")
            confirm = input("⚠️  This will modify your database. Continue? [y/N]: ")
            if confirm.lower() != "y":
                print("❌ Downgrade cancelled")
                sys.exit(0)
            command.downgrade(alembic_cfg, revision)
            print("✅ Database downgrade completed!")

        elif command_name == "current":
            print("📋 Current database revision:")
            command.current(alembic_cfg)

        elif command_name == "history":
            print("📜 Migration history:")
            command.history(alembic_cfg)

        elif command_name == "revision":
            # Create new migration
            autogenerate = "--autogenerate" in args or "-m" in args
            message_index = args.index("-m") if "-m" in args else -1
            message = (
                args[message_index + 1]
                if message_index >= 0 and message_index + 1 < len(args)
                else None
            )

            if autogenerate:
                print("🔄 Generating new migration...")
                command.revision(
                    alembic_cfg, autogenerate=True, message=message or "Auto-generated migration"
                )
                print("✅ Migration file created!")
            else:
                print("🔄 Creating new empty migration...")
                command.revision(alembic_cfg, message=message or "New migration")
                print("✅ Migration file created!")

        elif command_name == "stamp":
            revision = args[0] if args else "head"
            print(f"📌 Stamping database with revision: {revision}")
            command.stamp(alembic_cfg, revision)
            print("✅ Database stamped!")

        elif command_name == "show":
            revision = args[0] if args else "head"
            print(f"📄 Showing revision: {revision}")
            command.show(alembic_cfg, revision)

        else:
            print(f"❌ Unknown command: {command_name}")
            print(__doc__)
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
