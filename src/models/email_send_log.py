"""Audit log for marketing email sends."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, cast

from sqlalchemy import and_

from src.database import SQLAlchemyModel, db


class EmailSendStatus(str, Enum):
    """Possible delivery states for a marketing email attempt."""

    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    SUPPRESSED = "suppressed"
    SKIPPED = "skipped"


class EmailSendLog(SQLAlchemyModel):
    """Persistent log of each email send attempt."""

    __tablename__ = "email_send_logs"

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("email_campaigns.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False)
    provider_message_id = db.Column(db.String(255), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    context = db.Column(db.JSON, nullable=True)
    attempt_number = db.Column(db.Integer, nullable=False, default=1)
    sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_event_type = db.Column(db.String(50), nullable=True)
    last_event_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", backref="email_send_logs", lazy=True)

    @classmethod
    def record(
        cls,
        campaign_id: int,
        user_id: int,
        status: EmailSendStatus,
        context: Mapping[str, Any] | None = None,
        error_message: str | None = None,
    ) -> EmailSendLog:
        """Create a log entry in the desired status."""
        if context and not isinstance(context, Mapping):
            raise ValueError("context must be a mapping if provided")

        creator: Any = cls
        log = creator(
            campaign_id=campaign_id,
            user_id=user_id,
            status=status.value,
            context=dict(context or {}),
            error_message=error_message,
        )
        db.session.add(log)
        db.session.flush()
        return cast("EmailSendLog", log)

    def mark_sent(self, provider_message_id: str) -> None:
        """Mark the log as successfully sent."""
        self.status = EmailSendStatus.SENT.value
        self.provider_message_id = provider_message_id
        self.sent_at = datetime.utcnow()
        self.error_message = None

    def mark_failed(self, reason: str) -> None:
        """Mark the log as failed."""
        self.status = EmailSendStatus.FAILED.value
        self.sent_at = None
        self.error_message = reason

    @classmethod
    def sent_within(
        cls,
        campaign_id: int,
        user_id: int,
        window: timedelta,
    ) -> bool:
        """Return True if a successful send happened within the window."""
        threshold = datetime.utcnow() - window
        count: int = cls.query.filter(
            and_(
                cls.campaign_id == campaign_id,
                cls.user_id == user_id,
                cls.status == EmailSendStatus.SENT.value,
                cls.sent_at.isnot(None),
                cls.sent_at >= threshold,
            )
        ).count()
        return count > 0
