#!/usr/bin/env python3
"""Reset database - drop all tables and recreate with fresh schema."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from flask import Flask

load_dotenv()

# Create Flask app
app = Flask(__name__)

# Initialize database
from src.database import db, init_db

init_db(app)

with app.app_context():
    # Import all models to ensure they're registered
    from src.models.email_token import EmailToken  # noqa: F401
    from src.models.user import User  # noqa: F401
    from src.models.user_credentials import UserCredentials  # noqa: F401

    print("Dropping all tables...")
    db.drop_all()
    print("Creating all tables...")
    db.create_all()
    print("Database reset complete!")
    print("\nAll tables have been dropped and recreated.")
    print("Default admin user will be created on next app startup.")
