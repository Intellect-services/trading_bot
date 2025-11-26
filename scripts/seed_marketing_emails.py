#!/usr/bin/env python3
"""Seed marketing email campaigns and preferences."""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv()

from src.app import app
from src.database import db
from src.models.email_campaign import EmailCampaign
from src.models.email_preference import EmailPreference
from src.models.user import User


def main() -> None:
    """Ensure campaign definitions and user preferences exist."""
    with app.app_context():
        EmailCampaign.ensure_seed_campaigns()

        user_count = 0
        for user in User.query.all():
            EmailPreference.ensure_for_user(user.id)
            user_count += 1

        db.session.commit()
        print(f"Seeded marketing campaigns and preferences for {user_count} users.")


if __name__ == "__main__":
    main()
