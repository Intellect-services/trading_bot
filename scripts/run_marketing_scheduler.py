#!/usr/bin/env python3
"""Entry point for the always-on marketing email scheduler."""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv()

from src.app import app  # (ensure app + db are initialized)
from src.services.marketing_email_scheduler import run_scheduler_forever


def main() -> None:
    """Run the scheduler loop inside an application context."""
    poll_interval = int(os.getenv("MARKETING_SCHEDULER_INTERVAL_SECONDS", "300"))
    with app.app_context():
        run_scheduler_forever(poll_interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Marketing scheduler stopped by user.")
        sys.exit(0)
