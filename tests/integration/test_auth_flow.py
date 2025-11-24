"""Integration tests for authentication flow."""


class TestAuthenticationFlow:
    """Test complete authentication flow."""

    def test_register_verify_login_flow(self, client, flask_app):
        """Test complete flow: register -> verify email -> login."""
        with flask_app.app_context():
            from src.database import db
            from src.models.email_token import EmailToken
            from src.models.user import User

            # Register
            response = client.post(
                "/api/register",
                json={
                    "email": "newuser@example.com",
                    "password": "password123",
                    "name": "New User",
                },
                content_type="application/json",
            )
            assert response.status_code == 200
            data = response.get_json()
            assert data["status"] == "success"

            # Check user was created but not verified
            user = User.query.filter_by(email="newuser@example.com").first()
            assert user is not None
            assert user.email_verified is False

            # Get verification token
            token = EmailToken.query.filter_by(user_id=user.id, token_type="verification").first()
            assert token is not None

            # Try to login before verification (should fail)
            response = client.post(
                "/login",
                json={"email": "newuser@example.com", "password": "password123"},
                content_type="application/json",
            )
            assert response.status_code in [401, 403]

            # Verify email
            response = client.get(
                f"/api/verify-email?token={token.token}",
                headers={"Accept": "application/json"},
            )
            assert response.status_code == 200

            # Check user is now verified
            db.session.refresh(user)
            assert user.email_verified is True

            # Login should now work
            response = client.post(
                "/login",
                json={"email": "newuser@example.com", "password": "password123"},
                content_type="application/json",
            )
            assert response.status_code == 200
            data = response.get_json()
            assert data["status"] == "success"

    def test_password_reset_flow(self, client, flask_app):
        """Test password reset flow."""
        with flask_app.app_context():
            from src.database import db
            from src.models.email_token import EmailToken
            from src.models.user import User

            # Create user
            user = User(
                email="reset@example.com",
                name="Reset User",
                email_verified=True,
            )
            user.set_password("oldpassword")
            db.session.add(user)
            db.session.commit()

            # Request password reset
            response = client.post(
                "/api/forgot-password",
                json={"email": "reset@example.com"},
                content_type="application/json",
            )
            assert response.status_code == 200

            # Get reset token
            token = EmailToken.query.filter_by(user_id=user.id, token_type="password_reset").first()
            assert token is not None

            # Reset password
            response = client.post(
                "/api/reset-password",
                json={
                    "token": token.token,
                    "new_password": "newpassword123",
                },
                content_type="application/json",
            )
            assert response.status_code == 200

            # Verify old password doesn't work
            db.session.refresh(user)
            assert not user.check_password("oldpassword")

            # Verify new password works
            assert user.check_password("newpassword123")
