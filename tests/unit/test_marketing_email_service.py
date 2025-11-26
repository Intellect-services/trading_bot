"""Unit tests for the marketing email system."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.database import db
from src.models.email_preference import EmailPreference
from src.models.email_send_log import EmailSendLog, EmailSendStatus
from src.models.user import User
from src.services.marketing_campaign_types import MarketingCampaignType
from src.services.marketing_email_service import MarketingEmailService


class DummyClient:
    """Simple Resend client stub."""

    def __init__(self) -> None:
        self.params = None

    def send(self, params):  # - matches Resend API duck type
        self.params = params
        return SimpleNamespace(id="test-email-id")


@pytest.fixture()
def marketing_service():
    return MarketingEmailService(client=DummyClient())


def _create_user(email: str = "alex@example.com", name: str = "Alex Trader") -> User:
    user = User(email=email, name=name, email_verified=True)
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user


def test_marketing_email_is_personalized_and_branded(flask_app, marketing_service):
    with flask_app.app_context():
        user = _create_user("jordan@example.com", "Jordan Miles")
        sent = marketing_service.send_campaign(MarketingCampaignType.WELCOME_SERIES, user, {})

        assert sent is True
        client_params = marketing_service.client.params
        assert "Jordan" in client_params["subject"]
        assert "Unsubscribe instantly" in client_params["html"]

        log = EmailSendLog.query.filter_by(user_id=user.id).one()
        assert log.status == EmailSendStatus.SENT.value


def test_context_overrides_are_respected(flask_app, marketing_service):
    with flask_app.app_context():
        user = _create_user("maya@example.com", "Alex Doe")
        context = {
            "first_name": "Maya",
            "new_features": ["Deep risk audit", "Auto hedging", "Faster fills"],
        }
        marketing_service.send_campaign(MarketingCampaignType.PRODUCT_UPDATE, user, context)

        client_params = marketing_service.client.params
        assert "Maya" in client_params["subject"]
        assert "Deep risk audit" in client_params["html"]


def test_suppressed_when_opted_out(flask_app, marketing_service):
    with flask_app.app_context():
        user = _create_user("optout@example.com", "Opt Out")
        preference = EmailPreference.ensure_for_user(user.id)
        preference.mark_unsubscribed("test")
        db.session.commit()

        sent = marketing_service.send_campaign(MarketingCampaignType.PRODUCT_UPDATE, user, {})
        assert sent is False

        log = EmailSendLog.query.filter_by(user_id=user.id).one()
        assert log.status == EmailSendStatus.SUPPRESSED.value


def test_missing_client_returns_false(flask_app):
    with flask_app.app_context():
        user = _create_user("noclient@example.com", "No Client")
        service = MarketingEmailService(client=None)
        service.client = None

        success = service.send_campaign(MarketingCampaignType.MARKET_BRIEFING, user, {})
        assert success is False
