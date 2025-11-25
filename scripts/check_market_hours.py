#!/usr/bin/env python3
"""Check market hours and next open time."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime

from src.core.alpaca_service import AlpacaService
from src.utils.config import Config


def check_market_hours():
    """Check current market status and hours."""
    try:
        config = Config()
        if not config.alpaca_api_key_id or not config.alpaca_api_secret_key:
            print("❌ Alpaca credentials not configured")
            print("   Set ALPACA_API_KEY_ID and ALPACA_API_SECRET_KEY in .env")
            return

        alpaca = AlpacaService(
            api_key=config.alpaca_api_key_id,
            secret_key=config.alpaca_api_secret_key,
            trading_mode=config.trading_mode or "paper",
        )

        clock = alpaca.get_clock()

        print("=" * 70)
        print("MARKET STATUS")
        print("=" * 70)
        print()

        is_open = clock.get("is_open", False)
        status_emoji = "🟢" if is_open else "🔴"
        status_text = "OPEN" if is_open else "CLOSED"

        print(f"Market Status: {status_emoji} {status_text}")
        print()

        if clock.get("timestamp"):
            current_time = clock["timestamp"]
            if isinstance(current_time, str):
                current_time = datetime.fromisoformat(current_time.replace("Z", "+00:00"))
            print(f"Current Time: {current_time}")

        if not is_open:
            next_open = clock.get("next_open")
            if next_open:
                if isinstance(next_open, str):
                    next_open = datetime.fromisoformat(next_open.replace("Z", "+00:00"))
                print(f"⏰ Next Open: {next_open}")
                print(f"   (That's in about {_time_until(next_open)} from now)")

        if clock.get("next_close"):
            next_close = clock.get("next_close")
            if isinstance(next_close, str):
                next_close = datetime.fromisoformat(next_close.replace("Z", "+00:00"))
            if is_open:
                print(f"⏰ Next Close: {next_close}")
                print(f"   (That's in about {_time_until(next_close)} from now)")

        print()
        print("US Market Hours:")
        print("  Monday-Friday: 9:30 AM - 4:00 PM Eastern Time")
        print("  Timezone: ET (Eastern Time)")
        print()
        print("=" * 70)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


def _time_until(target_time: datetime) -> str:
    """Calculate time until target."""
    now = datetime.now(target_time.tzinfo) if target_time.tzinfo else datetime.now()
    delta = target_time - now

    if delta.total_seconds() < 0:
        return "past"

    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days > 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")

    return ", ".join(parts) if parts else "now"


if __name__ == "__main__":
    check_market_hours()
