"""Alert management for IntellectTrader."""

import logging
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

logger = logging.getLogger(__name__)


class AlertManager:
    """Manage alerts and notifications."""

    def __init__(self) -> None:
        """Initialize alert manager."""
        self.logger = logging.getLogger(__name__)
        self.email_enabled = bool(os.getenv("SMTP_HOST"))
        self.sms_enabled = False  # Would need Twilio setup

        # Email configuration
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.alert_email = os.getenv("ALERT_EMAIL", "")

    def send_email(self, subject: str, message: str, priority: str = "normal") -> bool:
        """Send email alert.

        Args:
            subject: Email subject
            message: Email message
            priority: Priority level (low, normal, high, critical)

        Returns:
            True if sent successfully
        """
        if not self.email_enabled or not self.alert_email:
            self.logger.warning("Email alerts not configured")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.smtp_user
            msg["To"] = self.alert_email
            msg["Subject"] = f"[IntellectTrader - {priority.upper()}] {subject}"

            # Add timestamp
            body = f"Time: {datetime.utcnow().isoformat()}\n\n{message}"
            msg.attach(MIMEText(body, "plain"))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            self.logger.info(f"Email alert sent: {subject}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
            return False

    def send_sms(self, message: str) -> bool:
        """Send SMS alert via Twilio.

        Args:
            message: SMS message

        Returns:
            True if sent successfully
        """
        if not self.sms_enabled:
            self.logger.warning("SMS alerts not configured")
            return False

        # TODO: Implement Twilio integration
        self.logger.info(f"SMS alert (not sent): {message}")
        return False

    def log_alert(self, level: str, message: str, **kwargs: Any) -> None:
        """Log alert to database.

        Args:
            level: Alert level (info, warning, error, critical)
            message: Alert message
            **kwargs: Additional context
        """
        try:
            from src.common.models import AuditLog
            from src.infrastructure import db_config

            with db_config.get_session() as session:
                audit = AuditLog(
                    user_id=kwargs.get("user_id"),
                    entity_type="alert",
                    entity_id=0,
                    action=level,
                    changes={"message": message, **kwargs},
                )
                session.add(audit)
                session.commit()

        except Exception as e:
            self.logger.error(f"Failed to log alert: {e}")

    def alert_bot_stopped(self, reason: str = "Unknown") -> None:
        """Alert that bot stopped unexpectedly.

        Args:
            reason: Reason for stopping
        """
        subject = "Trading Bot Stopped"
        message = f"The trading bot has stopped unexpectedly.\n\nReason: {reason}"

        self.send_email(subject, message, priority="critical")
        self.log_alert("critical", message)
        self.logger.critical(message)

    def alert_order_rejected(self, symbol: str, reason: str) -> None:
        """Alert that order was rejected.

        Args:
            symbol: Stock symbol
            reason: Rejection reason
        """
        subject = f"Order Rejected: {symbol}"
        message = f"Order for {symbol} was rejected.\n\nReason: {reason}"

        self.send_email(subject, message, priority="high")
        self.log_alert("warning", message)
        self.logger.warning(message)

    def alert_risk_breach(self, risk_type: str, current: float, limit: float) -> None:
        """Alert that risk limit was breached.

        Args:
            risk_type: Type of risk limit
            current: Current value
            limit: Limit value
        """
        subject = f"Risk Limit Breached: {risk_type}"
        message = (
            f"Risk limit breached!\n\nType: {risk_type}\nCurrent: {current:.2%}\nLimit: {limit:.2%}"
        )

        self.send_email(subject, message, priority="critical")
        self.log_alert("critical", message)
        self.logger.critical(message)

    def alert_api_connection_lost(self) -> None:
        """Alert that API connection was lost."""
        subject = "API Connection Lost"
        message = "Connection to Alpaca API was lost. Attempting to reconnect..."

        self.send_email(subject, message, priority="high")
        self.log_alert("error", message)
        self.logger.error(message)

    def alert_daily_loss_limit(self, loss_pct: float, limit_pct: float) -> None:
        """Alert that daily loss limit was reached.

        Args:
            loss_pct: Current loss percentage
            limit_pct: Loss limit percentage
        """
        subject = "Daily Loss Limit Reached"
        message = (
            f"Daily loss limit reached!\n\n"
            f"Current Loss: {loss_pct:.2%}\n"
            f"Limit: {limit_pct:.2%}\n\n"
            f"Trading has been paused."
        )

        self.send_email(subject, message, priority="critical")
        self.log_alert("critical", message)
        self.logger.critical(message)

    def alert_unusual_pnl(self, pnl_pct: float, threshold: float) -> None:
        """Alert on unusual P&L movement.

        Args:
            pnl_pct: P&L percentage change
            threshold: Threshold for unusual movement
        """
        subject = "Unusual P&L Movement Detected"
        message = (
            f"Unusual P&L movement detected!\n\nChange: {pnl_pct:.2%}\nThreshold: {threshold:.2%}"
        )

        self.send_email(subject, message, priority="high")
        self.log_alert("warning", message)
        self.logger.warning(message)


# Global alert manager instance
alert_manager = AlertManager()
