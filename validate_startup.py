#!/usr/bin/env python3
"""Validation startup script for IntellectTrader paper trading."""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bcrypt
from sqlalchemy import text

from src.business.trading.repositories import PortfolioRepository
from src.common.repositories import UserRepository
from src.infrastructure import db_config


def check_database():
    """Check database connection and tables."""
    print("=" * 60)
    print("CHECKING DATABASE")
    print("=" * 60)

    try:
        with db_config.get_session() as session:
            # Test connection
            session.execute(text("SELECT 1"))
            print("✅ Database connection successful")

            # Check tables exist
            result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]

            expected_tables = [
                "users",
                "user_settings",
                "audit_log",
                "portfolios",
                "positions",
                "orders",
                "trades",
                "portfolio_snapshots",
                "strategies",
                "signals",
                "backtest_results",
            ]

            print(f"\n📊 Found {len(tables)} tables:")
            for table in sorted(tables):
                status = "✅" if table in expected_tables else "⚠️"
                print(f"  {status} {table}")

            missing = set(expected_tables) - set(tables)
            if missing:
                print(f"\n⚠️  Missing tables: {', '.join(missing)}")
                print("   Run: alembic upgrade head")
                return False

            return True

    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def check_user():
    """Check if user exists, create if not."""
    print("\n" + "=" * 60)
    print("CHECKING USER ACCOUNT")
    print("=" * 60)

    try:
        with db_config.get_session() as session:
            user_repo = UserRepository(session)
            user = user_repo.get_by_email("admin@admin.com")

            if user:
                print(f"✅ User found: {user.email}")
                print(f"   Name: {user.name}")
                print(f"   ID: {user.id}")
                return user.id
            print("⚠️  No user found, creating admin user...")

            # Create admin user
            password_hash = bcrypt.hashpw(b"admin", bcrypt.gensalt())
            user = user_repo.create(
                email="admin@admin.com",
                password_hash=password_hash.decode("utf-8"),
                name="Admin User",
                is_active=True,
                is_admin=True,
            )

            print(f"✅ User created: {user.email}")
            print("   Password: admin")
            print(f"   ID: {user.id}")
            return user.id

    except Exception as e:
        print(f"❌ User check error: {e}")
        return None


def check_portfolio(user_id):
    """Check if portfolio exists, create if not."""
    print("\n" + "=" * 60)
    print("CHECKING PORTFOLIO")
    print("=" * 60)

    try:
        with db_config.get_session() as session:
            portfolio_repo = PortfolioRepository(session)
            portfolio = portfolio_repo.get_active_portfolio(user_id)

            if portfolio:
                print(f"✅ Portfolio found: {portfolio.name}")
                print(f"   ID: {portfolio.id}")
                print(f"   Initial Capital: ${portfolio.initial_capital:,.2f}")
                print(f"   Current Value: ${portfolio.current_value:,.2f}")
                print(f"   Paper Trading: {portfolio.is_paper}")
                return portfolio.id
            print("⚠️  No portfolio found, creating default portfolio...")

            portfolio = portfolio_repo.create(
                user_id=user_id,
                name="Paper Trading Account",
                description="Default paper trading portfolio for validation",
                initial_capital=100000.00,
                current_value=100000.00,
                cash_balance=100000.00,
                buying_power=200000.00,
                is_paper=True,
            )

            print(f"✅ Portfolio created: {portfolio.name}")
            print(f"   ID: {portfolio.id}")
            print(f"   Initial Capital: ${portfolio.initial_capital:,.2f}")
            return portfolio.id

    except Exception as e:
        print(f"❌ Portfolio check error: {e}")
        return None


def check_components():
    """Check if all components are ready."""
    print("\n" + "=" * 60)
    print("CHECKING COMPONENTS")
    print("=" * 60)

    components = {
        "OrderManager": "src/core/order_manager.py",
        "Enhanced RiskManager": "src/core/enhanced_risk_manager.py",
        "StrategyManager": "src/core/strategy_manager.py",
        "PositionTracker": "src/core/position_tracker.py",
        "BotPersistence": "src/core/bot_persistence.py",
    }

    all_ready = True
    for name, path in components.items():
        if os.path.exists(path):
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - File not found: {path}")
            all_ready = False

    return all_ready


def main():
    """Main validation startup."""
    print("\n" + "=" * 60)
    print("INTELLECTTRADER - PAPER TRADING VALIDATION")
    print("=" * 60)

    # Check database
    if not check_database():
        print("\n❌ Database check failed. Please fix issues and try again.")
        return False

    # Check/create user
    user_id = check_user()
    if not user_id:
        print("\n❌ User check failed. Please fix issues and try again.")
        return False

    # Check/create portfolio
    portfolio_id = check_portfolio(user_id)
    if not portfolio_id:
        print("\n❌ Portfolio check failed. Please fix issues and try again.")
        return False

    # Check components
    if not check_components():
        print("\n❌ Component check failed. Please fix issues and try again.")
        return False

    # All checks passed
    print("\n" + "=" * 60)
    print("✅ ALL CHECKS PASSED - READY FOR VALIDATION")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Ensure backend is running: python3 run.py")
    print("2. Access frontend: http://localhost:5173")
    print("3. Login with: admin@admin.com / admin")
    print("4. Start trading bot from dashboard")
    print("\nMonitor logs for validation results.")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
