"""Email service using Resend API for sending transactional emails."""

import logging
import os

import resend
from resend.emails._emails import Emails

from src.config.constants import APP_URL, EMAIL_FROM, FRONTEND_URL
from src.models.user import User

logger = logging.getLogger(__name__)


def get_frontend_url() -> str:
    """Get the frontend URL dynamically.

    Tries to read .frontend.port file (created by isbot script),
    falls back to FRONTEND_URL constant.
    """
    # Try to read the frontend port from the file created by isbot script
    # Get project root (assuming this file is in src/services/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    frontend_port_file = os.path.join(project_root, ".frontend.port")

    if os.path.exists(frontend_port_file):
        try:
            with open(frontend_port_file, encoding="utf-8") as f:
                port = f.read().strip()
                if port and port.isdigit():
                    return f"http://localhost:{port}"
        except Exception as e:
            logger.debug(f"Could not read .frontend.port file: {e}")

    # Fall back to constant
    return FRONTEND_URL


resend_api_key = os.getenv("RESEND_API_KEY")
SendParams = Emails.SendParams

emails_client: Emails | None
if resend_api_key:
    resend.api_key = resend_api_key
    emails_client = Emails()
else:
    emails_client = None
    logger.warning("RESEND_API_KEY not set. Email functionality will be disabled.")


def send_verification_email(user: User, token: str) -> bool:
    """Send email verification email to user.

    Args:
        user: User instance.
        token: Verification token.

    Returns:
        True if email sent successfully, False otherwise.
    """
    if not emails_client:
        logger.error("Resend client not initialized. Cannot send verification email.")
        return False

    verification_url = f"{APP_URL}/api/verify-email?token={token}"

    try:
        params: Emails.SendParams = {
            "from": EMAIL_FROM,
            "to": [user.email],
            "subject": "Verify your IntellectScout account",
            "html": f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to IntellectScout</h1>
                    </div>
                    <div class="content">
                        <p>Hi {user.name},</p>
                        <p>Thank you for signing up for IntellectScout! Please verify your email address to complete your registration.</p>
                        <p style="text-align: center;">
                            <a href="{verification_url}" class="button">Verify Email Address</a>
                        </p>
                        <p>Or copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; color: #667eea;">{verification_url}</p>
                        <p>This link will expire in 24 hours.</p>
                        <p>If you didn't create an account, please ignore this email.</p>
                    </div>
                    <div class="footer">
                        <p>© 2024 IntellectScout. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
        }

        result = emails_client.send(params)
        email_id = getattr(result, "id", "unknown") if result else "unknown"
        logger.info(f"Verification email sent to {user.email}. Email ID: {email_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {e!s}")
        return False


def send_password_reset_email(user: User, token: str) -> bool:
    """Send password reset email to user.

    Args:
        user: User instance.
        token: Password reset token.

    Returns:
        True if email sent successfully, False otherwise.
    """
    if not emails_client:
        logger.error("Resend client not initialized. Cannot send password reset email.")
        return False

    reset_url = f"{get_frontend_url()}/reset-password?token={token}"

    try:
        params: Emails.SendParams = {
            "from": EMAIL_FROM,
            "to": [user.email],
            "subject": "Reset your IntellectScout password",
            "html": f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                    .warning {{ background: #fee; border-left: 4px solid #ef4444; padding: 12px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Password Reset Request</h1>
                    </div>
                    <div class="content">
                        <p>Hi {user.name},</p>
                        <p>We received a request to reset your password for your IntellectScout account.</p>
                        <p style="text-align: center;">
                            <a href="{reset_url}" class="button">Reset Password</a>
                        </p>
                        <p>Or copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; color: #667eea;">{reset_url}</p>
                        <div class="warning">
                            <p><strong>Security Notice:</strong> This link will expire in 1 hour. If you didn't request a password reset, please ignore this email and your password will remain unchanged.</p>
                        </div>
                    </div>
                    <div class="footer">
                        <p>© 2024 IntellectScout. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
        }

        result = emails_client.send(params)
        email_id = getattr(result, "id", "unknown") if result else "unknown"
        logger.info(f"Password reset email sent to {user.email}. Email ID: {email_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {e!s}")
        return False


def send_welcome_email(user: User) -> bool:
    """Send welcome email to newly verified user.

    Args:
        user: User instance.

    Returns:
        True if email sent successfully, False otherwise.
    """
    if not emails_client:
        logger.error("Resend client not initialized. Cannot send welcome email.")
        return False

    try:
        params: Emails.SendParams = {
            "from": EMAIL_FROM,
            "to": [user.email],
            "subject": "Welcome to IntellectScout!",
            "html": f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to IntellectScout!</h1>
                    </div>
                    <div class="content">
                        <p>Hi {user.name},</p>
                        <p>Your email has been verified successfully. You're all set to start trading with IntellectScout!</p>
                        <p>To get started:</p>
                        <ol>
                            <li>Configure your Alpaca API credentials in your Account Settings</li>
                            <li>Choose your trading strategy</li>
                            <li>Start automated trading</li>
                        </ol>
                        <p style="text-align: center;">
                            <a href="{APP_URL}/account" class="button">Go to Account Settings</a>
                        </p>
                        <p>If you have any questions, feel free to reach out to our support team.</p>
                        <p>Happy trading!</p>
                        <p>The IntellectScout Team</p>
                    </div>
                    <div class="footer">
                        <p>© 2024 IntellectScout. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
        }

        result = emails_client.send(params)
        email_id = getattr(result, "id", "unknown") if result else "unknown"
        logger.info(f"Welcome email sent to {user.email}. Email ID: {email_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {e!s}")
        return False
