"""Unit tests for database models."""

from datetime import datetime, timedelta

import pytest

from src.models.email_token import EmailToken
from src.models.user import User
from src.models.user_credentials import UserCredentials
from src.utils.encryption import generate_encryption_key


@pytest.fixture(autouse=True)
def _set_encryption_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure encryption key is configured for Fernet."""
    monkeypatch.setenv("ENCRYPTION_KEY", generate_encryption_key())


class TestUser:
    """Test User model."""

    def test_user_creation(self, flask_app):
        """Test creating a user."""
        with flask_app.app_context():
            from src.database import db

            user = User(
                email="test@example.com",
                name="Test User",
                email_verified=True,
                role="trader",
            )
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()

            assert user.id is not None
            assert user.email == "test@example.com"
            assert user.name == "Test User"
            assert user.email_verified is True
            assert user.role == "trader"
            assert user.check_password("password123")
            assert not user.check_password("wrongpassword")

    def test_user_roles(self, flask_app):
        """Test user role methods."""
        with flask_app.app_context():
            from src.database import db

            trader = User(email="trader@example.com", name="Trader", role="trader")
            admin = User(email="admin@example.com", name="Admin", role="admin")
            owner = User(email="owner@example.com", name="Owner", role="owner")

            trader.set_password("pass")
            admin.set_password("pass")
            owner.set_password("pass")

            db.session.add_all([trader, admin, owner])
            db.session.commit()

            assert trader.is_trader()
            assert not trader.is_admin()
            assert not trader.is_owner()

            assert admin.is_admin()
            assert not admin.is_owner()

            assert owner.is_owner()

    def test_user_can_trade(self, flask_app):
        """Test user can_trade method."""
        with flask_app.app_context():
            from src.database import db

            user = User(email="test@example.com", name="Test", role="trader", email_verified=True)
            user.set_password("pass")
            db.session.add(user)
            db.session.commit()

            # User without credentials cannot trade
            assert not user.can_trade()

            # Add credentials
            credentials = UserCredentials(
                user_id=user.id,
                trading_mode="paper",
                is_active=True,
            )
            credentials.set_credentials("api_key", "secret_key", "paper")
            db.session.add(credentials)
            db.session.commit()

            # User with active credentials can trade
            assert user.can_trade()


class TestUserCredentials:
    """Test UserCredentials model."""

    def test_credentials_encryption(self, flask_app):
        """Test credential encryption and decryption."""
        with flask_app.app_context():
            from src.database import db

            user = User(email="test@example.com", name="Test")
            user.set_password("pass")
            db.session.add(user)
            db.session.commit()

            credentials = UserCredentials(
                user_id=user.id,
                trading_mode="paper",
            )
            credentials.set_credentials("test_api_key", "test_secret_key", "paper")
            db.session.add(credentials)
            db.session.commit()

            assert credentials.has_credentials()
            assert credentials.get_api_key() == "test_api_key"
            assert credentials.get_secret_key() == "test_secret_key"
            assert credentials.trading_mode == "paper"

    def test_credentials_verification(self, flask_app):
        """Test credential verification."""
        with flask_app.app_context():
            from src.database import db

            user = User(email="test@example.com", name="Test")
            user.set_password("pass")
            db.session.add(user)
            db.session.commit()

            credentials = UserCredentials(
                user_id=user.id,
                trading_mode="paper",
                is_active=False,
            )
            credentials.set_credentials("api_key", "secret_key", "paper")
            db.session.add(credentials)
            db.session.commit()

            assert not credentials.is_active

            credentials.mark_verified()
            db.session.commit()

            assert credentials.is_active
            assert credentials.last_verified_at is not None


class TestEmailToken:
    """Test EmailToken model."""

    def test_verification_token_creation(self, flask_app):
        """Test creating verification token."""
        with flask_app.app_context():
            from src.database import db

            user = User(email="test@example.com", name="Test")
            user.set_password("pass")
            db.session.add(user)
            db.session.commit()

            token = EmailToken.create_verification_token(user.id)
            db.session.add(token)
            db.session.commit()

            assert token.user_id == user.id
            assert token.token_type == "verification"
            assert token.is_valid()
            assert not token.used_at

    def test_token_expiration(self, flask_app):
        """Test token expiration."""
        with flask_app.app_context():
            from src.database import db

            user = User(email="test@example.com", name="Test")
            user.set_password("pass")
            db.session.add(user)
            db.session.commit()

            token = EmailToken.create_verification_token(user.id)
            # Set expiration to past
            token.expires_at = datetime.utcnow() - timedelta(hours=1)
            db.session.add(token)
            db.session.commit()

            assert not token.is_valid()

    def test_token_mark_as_used(self, flask_app):
        """Test marking token as used."""
        with flask_app.app_context():
            from src.database import db

            user = User(email="test@example.com", name="Test")
            user.set_password("pass")
            db.session.add(user)
            db.session.commit()

            token = EmailToken.create_verification_token(user.id)
            db.session.add(token)
            db.session.commit()

            assert token.is_valid()

            token.mark_as_used()
            db.session.commit()

            assert not token.is_valid()
            assert token.used_at is not None
