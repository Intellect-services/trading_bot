#!/usr/bin/env python3
"""Script to manually verify a user's email address."""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import app
from src.database import db
from src.models.user import User


def verify_user_email(email: str):
    """Verify a user's email address."""
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"❌ User not found: {email}")
            return False

        user.email_verified = True
        db.session.commit()
        print(f"✅ Email verified for user: {user.email}")
        print(f"   Name: {user.name}")
        print(f"   Role: {user.role}")
        print(f"   Email verified: {user.email_verified}")
        return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/verify_user.py <email>")
        print("Example: python scripts/verify_user.py user@example.com")
        sys.exit(1)

    email = sys.argv[1]
    verify_user_email(email)
