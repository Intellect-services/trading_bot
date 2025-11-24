"""User repository for user-specific database operations."""

from datetime import datetime

from sqlalchemy.orm import Session

from src.common.models.user import User
from src.common.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model with custom methods."""

    def __init__(self, session: Session):
        """Initialize user repository.

        Args:
            session: Database session
        """
        super().__init__(User, session)

    def get_by_email(self, email: str) -> User | None:
        """Get user by email address.

        Args:
            email: User email address

        Returns:
            User instance or None if not found
        """
        return self.get_one_by_filter(email=email)

    def get_active_users(self) -> list[User]:
        """Get all active users.

        Returns:
            List of active users
        """
        return self.get_by_filter(is_active=True)

    def get_admin_users(self) -> list[User]:
        """Get all admin users.

        Returns:
            List of admin users
        """
        return self.get_by_filter(is_admin=True)

    def update_last_login(self, user_id: int) -> User | None:
        """Update user's last login timestamp.

        Args:
            user_id: User ID

        Returns:
            Updated user instance or None if not found
        """
        return self.update(user_id, last_login=datetime.utcnow())

    def deactivate_user(self, user_id: int) -> User | None:
        """Deactivate a user account.

        Args:
            user_id: User ID

        Returns:
            Updated user instance or None if not found
        """
        return self.update(user_id, is_active=False)

    def activate_user(self, user_id: int) -> User | None:
        """Activate a user account.

        Args:
            user_id: User ID

        Returns:
            Updated user instance or None if not found
        """
        return self.update(user_id, is_active=True)

    def email_exists(self, email: str) -> bool:
        """Check if email already exists.

        Args:
            email: Email address to check

        Returns:
            True if email exists, False otherwise
        """
        return self.exists(email=email)
