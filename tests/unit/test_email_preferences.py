"""Smoke tests for email preference APIs."""

from __future__ import annotations

from src.database import db
from src.models.email_preference import EmailPreference
from src.models.user import User


def test_preferences_get_and_update(authenticated_client, flask_app):
    with flask_app.app_context():
        response = authenticated_client.get("/api/email/preferences")
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["marketing_opt_in"] is True

        update = authenticated_client.put(
            "/api/email/preferences",
            json={"marketing_opt_in": False},
        )
        assert update.status_code == 200
        updated = update.get_json()
        assert updated["data"]["marketing_opt_in"] is False


def test_unsubscribe_endpoint_generates_opt_out(client, flask_app):
    with flask_app.app_context():
        user = User(email="unsubscribe@example.com", name="Un Sub", email_verified=True)
        user.set_password("test12345")
        db.session.add(user)
        db.session.commit()
        preference = EmailPreference.ensure_for_user(user.id)
        db.session.commit()

        response = client.get(f"/api/email/unsubscribe?token={preference.unsubscribe_token}")
        assert response.status_code in (301, 302)

        refreshed = EmailPreference.query.filter_by(user_id=user.id).first()
        assert refreshed is not None
        assert refreshed.marketing_opt_in is False


def test_resubscribe_endpoint(client, flask_app):
    with flask_app.app_context():
        user = User(email="resub@example.com", name="Re Sub", email_verified=True)
        user.set_password("test12345")
        db.session.add(user)
        db.session.commit()
        preference = EmailPreference.ensure_for_user(user.id)
        preference.mark_unsubscribed("testcase")
        db.session.commit()

        response = client.post(
            "/api/email/resubscribe", json={"token": preference.unsubscribe_token}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["marketing_opt_in"] is True
