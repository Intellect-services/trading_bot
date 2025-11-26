#!/usr/bin/env python3
"""Script to verify what's actually implemented in the codebase."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_implementation(name: str, check_func, description: str) -> tuple[bool, str]:
    """Check if something is implemented."""
    try:
        result = check_func()
        if result:
            return True, f"✅ {name}: {description}"
        return False, f"❌ {name}: NOT FOUND"
    except ImportError as e:
        return False, f"❌ {name}: Import failed - {e}"
    except Exception as e:
        return False, f"⚠️  {name}: Error - {e}"


def main():
    """Main verification function."""
    print("=" * 70)
    print("VERIFICATION: What's Actually Implemented")
    print("=" * 70)
    print()

    checks = []

    # Check 1: Portfolio History
    checks.append(
        check_implementation(
            "Portfolio History API",
            lambda: hasattr(
                __import__("src.core.alpaca_service", fromlist=["AlpacaService"]).AlpacaService,
                "get_portfolio_history",
            ),
            "Method exists in AlpacaService",
        )
    )

    # Check 2: Account Activities
    checks.append(
        check_implementation(
            "Account Activities API",
            lambda: hasattr(
                __import__("src.core.alpaca_service", fromlist=["AlpacaService"]).AlpacaService,
                "get_account_activities",
            ),
            "Method exists in AlpacaService",
        )
    )

    # Check 3: Advanced Orders
    checks.append(
        check_implementation(
            "Bracket Orders",
            lambda: hasattr(
                __import__("src.core.alpaca_service", fromlist=["AlpacaService"]).AlpacaService,
                "submit_bracket_order",
            ),
            "Method exists in AlpacaService",
        )
    )

    checks.append(
        check_implementation(
            "Trailing Stop Orders",
            lambda: hasattr(
                __import__("src.core.alpaca_service", fromlist=["AlpacaService"]).AlpacaService,
                "submit_trailing_stop_order",
            ),
            "Method exists in AlpacaService",
        )
    )

    checks.append(
        check_implementation(
            "Stop Orders",
            lambda: hasattr(
                __import__("src.core.alpaca_service", fromlist=["AlpacaService"]).AlpacaService,
                "submit_stop_order",
            ),
            "Method exists in AlpacaService",
        )
    )

    # Check 4: WebSocket
    checks.append(
        check_implementation(
            "Alpaca WebSocket",
            lambda: __import__(
                "src.core.alpaca_websocket", fromlist=["AlpacaWebSocket"]
            ).AlpacaWebSocket
            is not None,
            "AlpacaWebSocket class exists",
        )
    )

    # Check 5: Data Cache
    checks.append(
        check_implementation(
            "Data Cache",
            lambda: __import__("src.core.data_cache", fromlist=["DataCache"]).DataCache is not None,
            "DataCache class exists",
        )
    )

    # Check 6: Data Provider
    checks.append(
        check_implementation(
            "Data Provider",
            lambda: __import__("src.core.data_provider", fromlist=["DataProvider"]).DataProvider
            is not None,
            "DataProvider class exists",
        )
    )

    # Check 7: Portfolio Analytics
    checks.append(
        check_implementation(
            "Portfolio Analytics",
            lambda: __import__(
                "src.core.portfolio_analytics", fromlist=["PortfolioAnalytics"]
            ).PortfolioAnalytics
            is not None,
            "PortfolioAnalytics class exists",
        )
    )

    # Check 8: Dashboard uses portfolio history
    checks.append(
        check_implementation(
            "Dashboard Portfolio History",
            lambda: "get_portfolio_history" in Path("src/app.py").read_text(),
            "Dashboard endpoint uses portfolio history",
        )
    )

    # Check 9: ML/AI Strategy
    checks.append(
        check_implementation(
            "AI Strategy",
            lambda: __import__("src.ml", fromlist=["AIStrategy"]).AIStrategy is not None,
            "AIStrategy class exists",
        )
    )

    # Check 10: Dependencies
    try:
        import yfinance

        _ = yfinance

        checks.append((True, "✅ yfinance: Installed"))
    except ImportError:
        checks.append((False, "❌ yfinance: NOT INSTALLED"))

    try:
        import sklearn

        checks.append((True, f"✅ scikit-learn: Installed (v{sklearn.__version__})"))
    except ImportError:
        checks.append((False, "❌ scikit-learn: NOT INSTALLED"))

    # Print results
    print("\nIMPLEMENTATION STATUS:\n")
    passed = 0
    failed = 0

    for success, message in checks:
        print(message)
        if success:
            passed += 1
        else:
            failed += 1

    print()
    print("=" * 70)
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed > 0:
        print("\n⚠️  Some features missing or dependencies not installed.")
        print("   Run: pip install -r requirements.txt")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
