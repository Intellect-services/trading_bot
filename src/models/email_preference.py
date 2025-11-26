"""User email preference tracking."""

from __future__ import annotations

import secrets
from datetime import datetime
from typing import Any, cast

from src.database import SQLAlchemyModel, db


class EmailPreference(SQLAlchemyModel):
    """Stores per-user marketing and transactional opt-ins."""

    __tablename__ = "email_preferences"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    marketing_opt_in = db.Column(db.Boolean, nullable=False, default=True)
    transactional_opt_in = db.Column(db.Boolean, nullable=False, default=True)
    unsubscribe_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    unsubscribed_at = db.Column(db.DateTime, nullable=True)
    last_sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = db.relationship("User", backref="email_preferences", uselist=False)

    @staticmethod
    def _generate_token() -> str:
        return secrets.token_urlsafe(24)

    @classmethod
    def ensure_for_user(cls, user_id: int) -> EmailPreference:
        """Fetch or create default preferences for a user."""
        preference = cls.query.filter_by(user_id=user_id).first()
        if preference:
            return cast("EmailPreference", preference)
        creator: Any = cls
        preference = creator(
            user_id=user_id,
            unsubscribe_token=cls._generate_token(),
        )
        db.session.add(preference)
        db.session.flush()
        return cast("EmailPreference", preference)

    @classmethod
    def from_token(cls, token: str) -> EmailPreference | None:
        """Locate preference row by unsubscribe token."""
        preference = cls.query.filter_by(unsubscribe_token=token).first()
        if preference is None:
            return None
        return cast("EmailPreference", preference)

    def mark_unsubscribed(self, reason: str | None = None) -> None:
        """Disable marketing emails for the user."""
        self.marketing_opt_in = False
        self.unsubscribed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if not reason:
            return
        # Optionally store reason in future telemetry tables.

    def resubscribe(self) -> None:
        """Re-enable marketing communications."""
        self.marketing_opt_in = True
        self.unsubscribed_at = None
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict[str, bool | int | str | None]:
        """Return API-safe representation."""
        return {
            "user_id": self.user_id,
            "marketing_opt_in": self.marketing_opt_in,
            "transactional_opt_in": self.transactional_opt_in,
            "unsubscribed_at": self.unsubscribed_at.isoformat() if self.unsubscribed_at else None,
            "last_sent_at": self.last_sent_at.isoformat() if self.last_sent_at else None,
        }
