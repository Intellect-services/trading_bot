"""Tests for Resend webhook processing."""

from __future__ import annotations

import hashlib
import hmac
import json

from src.config.constants import RESEND_WEBHOOK_SECRET
from src.database import db
from src.models.email_campaign import EmailCampaign
from src.models.email_send_log import EmailSendLog, EmailSendStatus
from src.models.user import User
from src.services.marketing_campaign_types import MarketingCampaignType


def _sign(payload: dict) -> str:
    body = json.dumps(payload).encode("utf-8")
    return hmac.new(RESEND_WEBHOOK_SECRET.encode("utf-8"), body, hashlib.sha256).hexdigest()


def test_resend_webhook_updates_log(client, flask_app):
    with flask_app.app_context():
        user = User(email="webhook@example.com", name="Hook Tester", email_verified=True)
        user.set_password("pass1234")
        db.session.add(user)
        db.session.commit()

        campaign = EmailCampaign.ensure_for_type(MarketingCampaignType.WELCOME_SERIES)
        log = EmailSendLog.record(
            campaign_id=campaign.id,
            user_id=user.id,
            status=EmailSendStatus.QUEUED,
            context={"test": True},
        )
        log.provider_message_id = "test_email_id"
        db.session.commit()

        payload = {
            "type": "email.delivered",
            "data": {
                "email": {"id": "test_email_id"},
            },
        }
        signature = _sign(payload)

        response = client.post(
            "/api/email/webhooks/resend",
            data=json.dumps(payload),
            headers={
                "Content-Type": "application/json",
                "X-Resend-Signature": signature,
            },
        )
        assert response.status_code == 200

        refreshed = EmailSendLog.query.get(log.id)
        assert refreshed.status == EmailSendStatus.SENT.value
        assert refreshed.last_event_type == "email.delivered"
        assert refreshed.events
