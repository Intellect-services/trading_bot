"""Database model for marketing email campaigns."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, cast

from src.database import SQLAlchemyModel, db
from src.services.marketing_campaign_types import MarketingCampaignType


class ScheduleStrategy(str, Enum):
    """Scheduling strategy for campaigns."""

    MANUAL = "manual"
    RECURRING = "recurring"
    EVENT_DRIVEN = "event_driven"


class EmailCampaign(SQLAlchemyModel):
    """Persisted marketing campaign definition and scheduling metadata."""

    __tablename__ = "email_campaigns"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    campaign_type = db.Column(db.String(60), nullable=False)
    schedule_strategy = db.Column(
        db.String(20), nullable=False, default=ScheduleStrategy.RECURRING.value
    )
    cadence_minutes = db.Column(db.Integer, nullable=True, default=1440)
    max_emails_per_run = db.Column(db.Integer, nullable=False, default=500)
    last_run_at = db.Column(db.DateTime, nullable=True)
    next_run_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    audience_rules = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    sends = db.relationship("EmailSendLog", backref="campaign", lazy=True)

    @classmethod
    def ensure_for_type(cls, campaign_type: MarketingCampaignType) -> EmailCampaign:
        """Ensure a campaign row exists for the enum type."""
        slug = campaign_type.value
        campaign = cls.query.filter_by(slug=slug).first()
        if campaign:
            return cast("EmailCampaign", campaign)

        defaults = _DEFAULT_CAMPAIGNS.get(
            slug,
            {
                "name": slug.replace("_", " ").title(),
                "description": f"Automated flow for {slug}",
                "cadence_minutes": 1440,
                "max_emails_per_run": 500,
            },
        )
        if not campaign:
            creator: Any = cls
            campaign = creator(
                slug=slug,
                name=defaults["name"],
                description=defaults["description"],
                campaign_type=slug,
                cadence_minutes=defaults.get("cadence_minutes"),
                max_emails_per_run=defaults.get("max_emails_per_run", 500),
                next_run_at=datetime.utcnow(),
                audience_rules=defaults.get("audience_rules"),
            )
            db.session.add(campaign)
            db.session.flush()
        else:
            # backfill defaults for previously created campaigns
            if not campaign.audience_rules and defaults.get("audience_rules"):
                campaign.audience_rules = defaults.get("audience_rules")
            if not campaign.description:
                campaign.description = defaults.get("description")
        return cast("EmailCampaign", campaign)

    @classmethod
    def ensure_seed_campaigns(cls) -> list[EmailCampaign]:
        """Ensure all default campaigns exist."""
        campaigns: list[EmailCampaign] = []
        for campaign_type in MarketingCampaignType:
            campaigns.append(cls.ensure_for_type(campaign_type))
        db.session.commit()
        return campaigns

    @classmethod
    def due_campaigns(cls, now: datetime | None = None) -> list[EmailCampaign]:
        """Return active campaigns that should run."""
        now = now or datetime.utcnow()
        campaigns = (
            cls.query.filter(
                cls.is_active.is_(True),
                cls.schedule_strategy == ScheduleStrategy.RECURRING.value,
                cls.next_run_at.isnot(None),
                cls.next_run_at <= now,
            )
            .order_by(cls.next_run_at.asc())
            .all()
        )
        return cast("list[EmailCampaign]", campaigns)

    def schedule_next_run(self) -> None:
        """Update next_run_at/last_run_at after execution."""
        now = datetime.utcnow()
        self.last_run_at = now
        cadence = self.cadence_minutes or 1440
        self.next_run_at = now + timedelta(minutes=cadence)


_DEFAULT_CAMPAIGNS: dict[str, dict[str, Any]] = {
    MarketingCampaignType.WELCOME_SERIES.value: {
        "name": "Welcome Series",
        "description": "Guided onboarding series for new verified users.",
        "cadence_minutes": 1440,
        "max_emails_per_run": 200,
        "audience_rules": {
            "max_days_since_signup": 7,
            "require_email_verified": True,
        },
    },
    MarketingCampaignType.PRODUCT_UPDATE.value: {
        "name": "Product Pulse",
        "description": "Monthly product release highlights for engaged traders.",
        "cadence_minutes": 10080,
        "max_emails_per_run": 1000,
        "audience_rules": {
            "min_days_since_signup": 7,
        },
    },
    MarketingCampaignType.MARKET_BRIEFING.value: {
        "name": "Market Briefing",
        "description": "Weekly macro and signal digest sent Monday mornings.",
        "cadence_minutes": 10080,
        "max_emails_per_run": 750,
        "audience_rules": {
            "min_days_since_signup": 1,
        },
    },
    MarketingCampaignType.EDUCATION_SERIES.value: {
        "name": "Education Series",
        "description": "Curriculum drops and coaching invites.",
        "cadence_minutes": 20160,
        "max_emails_per_run": 750,
        "audience_rules": {
            "min_days_since_signup": 3,
        },
    },
    MarketingCampaignType.REENGAGEMENT.value: {
        "name": "Re-engagement",
        "description": "Win-back automations for inactive desks.",
        "cadence_minutes": 4320,
        "max_emails_per_run": 250,
        "audience_rules": {
            "inactive_days": 21,
        },
    },
}
