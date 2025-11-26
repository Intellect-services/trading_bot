"""Background scheduler that dispatches recurring marketing campaigns."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Iterable, Mapping
from datetime import datetime, timedelta
from typing import Any, cast

from sqlalchemy import or_

from src.database import db
from src.models.email_campaign import EmailCampaign
from src.models.email_preference import EmailPreference
from src.models.email_send_log import EmailSendLog
from src.models.user import User
from src.services.marketing_campaign_types import MarketingCampaignType
from src.services.marketing_email_service import MarketingEmailService

logger = logging.getLogger(__name__)


class EmailMarketingScheduler:
    """Simple polling scheduler that keeps campaigns running."""

    def __init__(
        self,
        marketing_service: MarketingEmailService | None = None,
    ) -> None:
        self.service = marketing_service or MarketingEmailService()

    def run_once(self) -> dict[str, int]:
        """Evaluate all due campaigns once and dispatch sends."""
        EmailCampaign.ensure_seed_campaigns()
        due_campaigns = EmailCampaign.due_campaigns()
        summary: dict[str, int] = {}

        for campaign in due_campaigns:
            sent = self._dispatch_campaign(campaign)
            campaign.schedule_next_run()
            db.session.add(campaign)
            summary[campaign.slug] = sent

        if due_campaigns:
            db.session.commit()
        return summary

    def _dispatch_campaign(self, campaign: EmailCampaign) -> int:
        """Select recipients and send the campaign."""
        try:
            campaign_type = MarketingCampaignType(campaign.campaign_type)
        except ValueError:
            logger.warning("Skipping unknown campaign type %s", campaign.campaign_type)
            return 0

        audience = self._select_audience(campaign)
        sends = 0
        for user in audience:
            if EmailSendLog.sent_within(
                campaign_id=campaign.id,
                user_id=user.id,
                window=_recent_window_for(campaign_type),
            ):
                continue
            success = self.service.send_campaign(campaign_type, user, {})
            if success:
                sends += 1
            if sends >= campaign.max_emails_per_run:
                break

        logger.info("Campaign %s dispatched to %s users", campaign.slug, sends)
        return sends

    def _select_audience(
        self,
        campaign: EmailCampaign,
    ) -> Iterable[User]:
        """Return candidate users respecting preferences."""
        base_query = (
            User.query.outerjoin(EmailPreference, EmailPreference.user_id == User.id)
            .filter(User.email_verified.is_(True))
            .filter(
                or_(
                    EmailPreference.marketing_opt_in.is_(True),
                    EmailPreference.id.is_(None),
                )
            )
        )

        now = datetime.utcnow()
        rules = _extract_rules(campaign)
        query = _apply_audience_rules(base_query, rules, now)

        result = query.limit(campaign.max_emails_per_run * 2).all()
        return cast("Iterable[User]", result)


def run_scheduler_forever(poll_interval_seconds: int = 300) -> None:
    """Long-running loop that continuously runs campaigns."""
    scheduler = EmailMarketingScheduler()
    while True:
        summary = scheduler.run_once()
        if summary:
            logger.info("Marketing scheduler summary: %s", summary)
        time.sleep(poll_interval_seconds)


def _recent_window_for(campaign_type: MarketingCampaignType) -> timedelta:
    mapping = {
        MarketingCampaignType.WELCOME_SERIES: timedelta(days=3),
        MarketingCampaignType.PRODUCT_UPDATE: timedelta(days=30),
        MarketingCampaignType.MARKET_BRIEFING: timedelta(days=5),
        MarketingCampaignType.EDUCATION_SERIES: timedelta(days=14),
        MarketingCampaignType.REENGAGEMENT: timedelta(days=14),
    }
    return mapping.get(campaign_type, timedelta(days=7))


def _extract_rules(campaign: EmailCampaign) -> Mapping[str, Any]:
    rules = campaign.audience_rules or {}
    if isinstance(rules, str):
        try:
            loaded = json.loads(rules)
        except json.JSONDecodeError:
            return {}
        if isinstance(loaded, dict):
            return loaded
        return {}
    if isinstance(rules, dict):
        return rules
    return {}


def _apply_audience_rules(query: Any, rules: Mapping[str, Any], now: datetime) -> Any:
    if not rules:
        return query

    min_days = rules.get("min_days_since_signup")
    if isinstance(min_days, (int, float)):
        threshold = now - timedelta(days=float(min_days))
        query = query.filter(User.created_at <= threshold)

    max_days = rules.get("max_days_since_signup")
    if isinstance(max_days, (int, float)):
        floor = now - timedelta(days=float(max_days))
        query = query.filter(User.created_at >= floor)

    inactive_days = rules.get("inactive_days")
    if isinstance(inactive_days, (int, float)):
        cutoff = now - timedelta(days=float(inactive_days))
        query = query.filter(
            or_(
                User.last_login.is_(None),
                User.last_login < cutoff,
            )
        )

    require_verified = rules.get("require_email_verified")
    if require_verified is False:
        query = query.filter(User.email_verified.is_(False))

    allowed_roles = rules.get("roles")
    if isinstance(allowed_roles, Iterable):
        roles = [str(role) for role in allowed_roles if role]
        if roles:
            query = query.filter(User.role.in_(roles))

    return query
