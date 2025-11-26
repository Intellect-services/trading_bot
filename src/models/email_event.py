"""Stores lifecycle events (delivered/opened/etc.) for marketing emails."""

from __future__ import annotations

from datetime import datetime

from src.database import SQLAlchemyModel, db


class EmailEvent(SQLAlchemyModel):
    """Event stream for a marketing email send log."""

    __tablename__ = "email_events"

    id = db.Column(db.Integer, primary_key=True)
    send_log_id = db.Column(
        db.Integer, db.ForeignKey("email_send_logs.id"), nullable=False, index=True
    )
    event_type = db.Column(db.String(50), nullable=False)
    occurred_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    payload = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    send_log = db.relationship("EmailSendLog", backref="events")
