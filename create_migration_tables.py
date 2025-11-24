"""Script to create migration tables for user authentication features.
This can be run manually if Alembic is not set up properly."""

import os
import sys

from flask import Flask

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create Flask app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///./src/trading_bot.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
from src.database import init_db

init_db(app)

print("Migration tables created successfully!")
print("User authentication features are now available.")
