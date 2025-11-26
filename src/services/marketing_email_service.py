"""Branded, personalized marketing email system backed by Resend."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from src.config.constants import (
    APP_URL,
    BRAND_FOOTER_ADDRESS,
    BRAND_LOGO_URL,
    BRAND_NAME,
    BRAND_PRIMARY_COLOR,
    BRAND_SECONDARY_COLOR,
    BRAND_SUPPORT_EMAIL,
    FRONTEND_URL,
    MARKETING_EMAIL_FROM_FORMAT,
    MARKETING_EMAIL_PERSONA_EMAIL,
    MARKETING_EMAIL_PERSONA_NAME,
    MARKETING_EMAIL_PERSONA_TITLE,
    MARKETING_EMAIL_REPLY_TO,
    MARKETING_EMAIL_UNSUBSCRIBE_URL,
)
from src.database import db
from src.models.email_campaign import EmailCampaign
from src.models.email_preference import EmailPreference
from src.models.email_send_log import EmailSendLog, EmailSendStatus
from src.services.email_service import SendParams, emails_client
from src.services.marketing_campaign_types import MarketingCampaignType

if TYPE_CHECKING:
    from src.models.user import User

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class BrandTheme:
    """Brand styling primitives shared across templates."""

    name: str
    logo_url: str
    primary_color: str
    secondary_color: str
    support_email: str
    footer_address: str


@dataclass(slots=True)
class EmailPersona:
    """Persona representing a human sender for marketing emails."""

    first_name: str
    title: str
    email: str

    def formatted_from(self) -> str:
        """Return humanized From header."""
        return MARKETING_EMAIL_FROM_FORMAT.format(
            persona_name=self.first_name,
            brand_name=BRAND_NAME,
            persona_email=self.email,
        )

    def signature_block(self) -> str:
        """Return HTML signature block."""
        return (
            f"{self.first_name} — {self.title}<br />" f"{BRAND_NAME}<br />" f"{BRAND_SUPPORT_EMAIL}"
        )


@dataclass(slots=True)
class Palette:
    """Palette for specific campaign."""

    hero_start: str
    hero_end: str
    accent: str
    badge_bg: str


@dataclass(slots=True)
class EmailSection:
    """Structured content section used inside templates."""

    title: str
    body: str
    eyebrow: str | None = None
    bullets: Sequence[str] = field(default_factory=list)
    cta_label: str | None = None
    cta_url: str | None = None
    highlight: bool = False
    icon: str | None = None


@dataclass(slots=True)
class MarketingTemplate:
    """Fully-rendered marketing email payload prior to HTML generation."""

    subject: str
    preview_text: str
    hero_title: str
    hero_subtitle: str
    hero_badge: str
    sections: Sequence[EmailSection]
    primary_cta_label: str | None = None
    primary_cta_url: str | None = None
    palette: Palette = field(
        default_factory=lambda: Palette(
            hero_start=BRAND_PRIMARY_COLOR,
            hero_end=BRAND_SECONDARY_COLOR,
            accent=BRAND_SECONDARY_COLOR,
            badge_bg="#000000",
        )
    )
    testimonial: str | None = None
    testimonial_author: str | None = None


BRAND_THEME = BrandTheme(
    name=BRAND_NAME,
    logo_url=BRAND_LOGO_URL,
    primary_color=BRAND_PRIMARY_COLOR,
    secondary_color=BRAND_SECONDARY_COLOR,
    support_email=BRAND_SUPPORT_EMAIL,
    footer_address=BRAND_FOOTER_ADDRESS,
)
DEFAULT_PERSONA = EmailPersona(
    first_name=MARKETING_EMAIL_PERSONA_NAME,
    title=MARKETING_EMAIL_PERSONA_TITLE,
    email=MARKETING_EMAIL_PERSONA_EMAIL,
)


class MarketingEmailService:
    """High-level orchestrator for branded marketing campaigns."""

    def __init__(self, client: Any | None = None) -> None:
        self.client = client if client is not None else emails_client

    def send_campaign(
        self,
        campaign: MarketingCampaignType,
        user: User,
        context: Mapping[str, Any] | None = None,
    ) -> bool:
        """Render and send a marketing email for the given campaign."""
        if not self.client:
            logger.error("Marketing email client is not configured.")
            return False

        context_data = dict(context or {})
        persona = self._resolve_persona(context_data)
        campaign_row = EmailCampaign.ensure_for_type(campaign)
        preference = EmailPreference.ensure_for_user(user.id)
        unsubscribe_url = _build_unsubscribe_url(preference, context_data)
        preferences_url = (
            context_data.get("preferences_url") or f"{FRONTEND_URL}/settings/notifications"
        )
        context_data["unsubscribe_url"] = unsubscribe_url
        context_data["preferences_url"] = preferences_url

        if not preference.marketing_opt_in:
            EmailSendLog.record(
                campaign_id=campaign_row.id,
                user_id=user.id,
                status=EmailSendStatus.SUPPRESSED,
                context=_sanitize_context(context_data),
                error_message="User opted out of marketing emails.",
            )
            db.session.commit()
            logger.info(
                "Skipped campaign %s for %s because user opted out.",
                campaign.value,
                user.email,
            )
            return False

        template = self._build_template(campaign, user, context_data)
        html = self._render_html(
            template,
            persona,
            preferences_url=preferences_url,
            unsubscribe_url=unsubscribe_url,
        )

        params: SendParams = {
            "from": persona.formatted_from(),
            "reply_to": MARKETING_EMAIL_REPLY_TO,
            "to": [user.email],
            "subject": template.subject,
            "html": html,
        }

        send_log = EmailSendLog.record(
            campaign_id=campaign_row.id,
            user_id=user.id,
            status=EmailSendStatus.QUEUED,
            context=_sanitize_context(context_data),
        )

        try:
            result = self.client.send(params)
            email_id = getattr(result, "id", "unknown")
            send_log.mark_sent(email_id)
            preference.last_sent_at = datetime.utcnow()
            db.session.commit()
            logger.info(
                "Marketing campaign %s sent to %s (id=%s)",
                campaign.value,
                user.email,
                email_id,
            )
            return True
        except Exception as exc:
            send_log.mark_failed(str(exc))
            db.session.commit()
            logger.exception(
                "Failed to send marketing campaign %s to %s: %s",
                campaign.value,
                user.email,
                exc,
            )
            return False

    def send_bulk(
        self,
        campaign: MarketingCampaignType,
        users: Iterable[User],
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, bool]:
        """Send campaign to multiple users, returning delivery map."""
        results: dict[str, bool] = {}
        for user in users:
            results[user.email] = self.send_campaign(campaign, user, context)
        return results

    def _resolve_persona(self, context: Mapping[str, Any]) -> EmailPersona:
        candidate = context.get("persona")
        if isinstance(candidate, EmailPersona):
            return candidate
        if isinstance(candidate, Mapping):
            return EmailPersona(
                first_name=str(candidate.get("first_name", DEFAULT_PERSONA.first_name)),
                title=str(candidate.get("title", DEFAULT_PERSONA.title)),
                email=str(candidate.get("email", DEFAULT_PERSONA.email)),
            )
        return DEFAULT_PERSONA

    def _build_template(
        self,
        campaign: MarketingCampaignType,
        user: User,
        context: Mapping[str, Any],
    ) -> MarketingTemplate:
        builders = {
            MarketingCampaignType.WELCOME_SERIES: self._build_welcome_series,
            MarketingCampaignType.PRODUCT_UPDATE: self._build_product_update,
            MarketingCampaignType.MARKET_BRIEFING: self._build_market_briefing,
            MarketingCampaignType.EDUCATION_SERIES: self._build_education_series,
            MarketingCampaignType.REENGAGEMENT: self._build_reengagement,
        }
        builder = builders.get(campaign)
        if not builder:
            raise ValueError(f"Unsupported campaign type: {campaign}")
        return builder(user, context)

    def _build_welcome_series(
        self,
        user: User,
        context: Mapping[str, Any],
    ) -> MarketingTemplate:
        first_name = _first_name(context, user)
        primary_cta = context.get("primary_cta_url") or f"{FRONTEND_URL}/onboarding"
        sections: list[EmailSection] = [
            EmailSection(
                eyebrow="Step 1",
                title="Secure your trading identity",
                body="Finish verification so we can unlock live trading and advanced capital protections.",
                bullets=[
                    "Enable MFA & device alerts",
                    "Confirm brokerage ownership",
                    "Set risk guardrails",
                ],
                cta_label="Complete verification",
                cta_url=f"{FRONTEND_URL}/settings/security",
                icon="🛡️",
                highlight=True,
            ),
            EmailSection(
                eyebrow="Step 2",
                title="Connect Alpaca or paper account",
                body="Plug in your brokerage keys once and monitor usage centrally within IntellectScout.",
                bullets=[
                    "OAuth hand-off for live accounts",
                    "Automatic paper-trading sandbox",
                    "Credential vault with rotation alerts",
                ],
                cta_label="Connect account",
                cta_url=f"{FRONTEND_URL}/settings/brokerage",
                icon="🔌",
            ),
            EmailSection(
                eyebrow="Step 3",
                title="Launch your first automated strategy",
                body="Pick a ready-made playbook or customize signals—either way, you keep full control.",
                bullets=[
                    "Curated starter strategies",
                    "Visual performance sandboxes",
                    "Live guardrails & pause control",
                ],
                cta_label="Explore strategies",
                cta_url=f"{FRONTEND_URL}/strategies",
                icon="🚀",
            ),
        ]
        return MarketingTemplate(
            subject=f"Welcome aboard, {first_name}! Your launch plan is ready 🚀",
            preview_text="Three guided steps to go from signup to automated trading hero.",
            hero_title=f"You're in, {first_name}. Let's launch intelligently.",
            hero_subtitle="Follow the playbook below to get trading-ready in under 10 minutes.",
            hero_badge="Welcome Series · Day 1",
            sections=sections,
            primary_cta_label="Continue onboarding",
            primary_cta_url=primary_cta,
            palette=Palette(
                hero_start="#312E81",
                hero_end="#5B21B6",
                accent="#F472B6",
                badge_bg="#4C1D95",
            ),
            testimonial="“IntellectScout had us live on paper trading in one afternoon.”",
            testimonial_author="Lena Ortiz · Quant Research Lead",
        )

    def _build_product_update(
        self,
        user: User,
        context: Mapping[str, Any],
    ) -> MarketingTemplate:
        first_name = _first_name(context, user)
        features = context.get(
            "new_features",
            [
                "Per-position volatility throttles",
                "AI anomaly explanations",
                "Portfolio moments feed",
            ],
        )
        sections = [
            EmailSection(
                eyebrow="What's new",
                title="Fresh intelligence inside your command center",
                body="We focused this release on transparency and faster iteration loops.",
                bullets=[str(item) for item in features][:4],
                cta_label="View release notes",
                cta_url=context.get("changelog_url", f"{FRONTEND_URL}/changelog"),
                icon="✨",
            ),
            EmailSection(
                eyebrow="Featured workflow",
                title="One-click playbook cloning",
                body="Duplicate any live strategy, sandbox the change set, and compare risk deltas instantly.",
                bullets=[
                    "Version tree with rollback",
                    "Automatic KPI regression tests",
                    "Shareable diffs for your desk",
                ],
                highlight=True,
                icon="⚙️",
            ),
        ]
        return MarketingTemplate(
            subject=f"{first_name}, we just shipped your most requested upgrades",
            preview_text="Fresh AI transparency tools, volatility throttles, and faster playbooks.",
            hero_title=f"New power-ups for you, {first_name}",
            hero_subtitle="Your dashboard just leveled up with explainable AI and quicker experimentation.",
            hero_badge="Product Update · Release 24.11",
            sections=sections,
            primary_cta_label="Try the new tools",
            primary_cta_url=context.get("feature_url", f"{FRONTEND_URL}/dashboard"),
            palette=Palette(
                hero_start="#0F172A",
                hero_end="#1E3A8A",
                accent="#22D3EE",
                badge_bg="#0284C7",
            ),
        )

    def _build_market_briefing(
        self,
        user: User,
        context: Mapping[str, Any],
    ) -> MarketingTemplate:
        first_name = _first_name(context, user)
        macro_theme = context.get(
            "macro_theme",
            "Rates stay sticky while AI earnings accelerate.",
        )
        watchlist = context.get(
            "watchlist",
            ["SMH", "MSFT", "NVDA", "XLK"],
        )
        levels = context.get(
            "critical_levels",
            ["S&P 500 · 5,050", "NASDAQ · 17,000", "VIX · 16 handle"],
        )
        sections = [
            EmailSection(
                eyebrow="Macro pulse",
                title="This week's dominant theme",
                body=macro_theme,
                icon="🌐",
                bullets=[f"Focus: {macro_theme}", "Liquidity: Improving", "Volatility: Contained"],
            ),
            EmailSection(
                eyebrow="Signals on deck",
                title="Top watchlist with actionable levels",
                body="We've highlighted asymmetric entries with guardrails for each symbol.",
                bullets=[str(item) for item in watchlist],
                cta_label="Open live dashboard",
                cta_url=f"{FRONTEND_URL}/dashboard",
                icon="📊",
            ),
            EmailSection(
                eyebrow="Risk guardrails",
                title="Levels where we pivot",
                body="Have alerts fire when the market touches any of these inflection points.",
                bullets=[str(level) for level in levels],
                highlight=True,
                icon="🚨",
            ),
        ]
        return MarketingTemplate(
            subject=f"Weekly market briefing for you, {first_name}",
            preview_text="Macro pulse, asymmetric watchlist, and risk guardrails curated by IntellectScout.",
            hero_title="Stay ahead of the move.",
            hero_subtitle="Your institutional-grade cheat sheet ships every Monday before the bell.",
            hero_badge="Market Briefing · Monday 8AM",
            sections=sections,
            primary_cta_label="See live signals",
            primary_cta_url=context.get("insights_url", f"{FRONTEND_URL}/insights"),
            palette=Palette(
                hero_start="#022C22",
                hero_end="#064E3B",
                accent="#34D399",
                badge_bg="#065F46",
            ),
        )

    def _build_education_series(
        self,
        user: User,
        context: Mapping[str, Any],
    ) -> MarketingTemplate:
        first_name = _first_name(context, user)
        curriculum = context.get(
            "curriculum",
            [
                "Design a volatility-aware position sizing ladder",
                "Automate drawdown halts with sentiment overlays",
                "Measure alpha decay with sandbox backtests",
            ],
        )
        sections = [
            EmailSection(
                eyebrow="Lesson plan",
                title="Today's pro playbook",
                body="We curated the most effective automation drills based on real fund workflows.",
                bullets=[str(item) for item in curriculum],
                icon="📘",
                highlight=True,
            ),
            EmailSection(
                eyebrow="Live coaching",
                title="Join a small-room strategy teardown",
                body="Bring your own bot, get direct feedback from IntellectScout strategists.",
                cta_label="Reserve a spot",
                cta_url=context.get("coaching_url", f"{APP_URL}/api/book-coaching"),
                icon="🧑‍🏫",
            ),
        ]
        return MarketingTemplate(
            subject=f"{first_name}, master the next automation tactic today",
            preview_text="Deep-dive curriculum plus live coaching to keep your edge sharp.",
            hero_title="Elite automation curriculum · Cohort 12",
            hero_subtitle="Bite-sized lessons engineered to compound your edge week over week.",
            hero_badge="Education Series · Playbook Drop",
            sections=sections,
            primary_cta_label="Open the lesson",
            primary_cta_url=context.get("lesson_url", f"{FRONTEND_URL}/academy"),
            palette=Palette(
                hero_start="#1D4ED8",
                hero_end="#9333EA",
                accent="#F59E0B",
                badge_bg="#3730A3",
            ),
        )

    def _build_reengagement(
        self,
        user: User,
        context: Mapping[str, Any],
    ) -> MarketingTemplate:
        first_name = _first_name(context, user)
        last_activity = context.get("last_activity", "a few weeks ago")
        sections = [
            EmailSection(
                eyebrow="Saved progress",
                title="Your workspace is on pause",
                body=f"You last checked in {last_activity}. Your bots, guardrails, and insights are waiting.",
                bullets=[
                    "All strategies paused safely",
                    "Historical performance preserved",
                    "Alerts resume the moment you return",
                ],
                icon="💾",
            ),
            EmailSection(
                eyebrow="New since you left",
                title="What you missed",
                body="We quietly shipped improvements you asked for—here's the highlight reel.",
                bullets=[
                    "Intraday anomaly detective",
                    "Client-ready PDF reporting",
                    "On-chain sentiment overlay",
                ],
                icon="✨",
                highlight=True,
            ),
        ]
        return MarketingTemplate(
            subject=f"We saved your desk, {first_name}. Ready to pick up?",
            preview_text="Paused bots, saved analytics, and fresh upgrades the moment you log back in.",
            hero_title="Step back into a smarter cockpit.",
            hero_subtitle="We preserved every tweak—you just press resume.",
            hero_badge="Re-engagement · Win-back",
            sections=sections,
            primary_cta_label="Resume trading plan",
            primary_cta_url=context.get("resume_url", f"{FRONTEND_URL}/dashboard"),
            palette=Palette(
                hero_start="#7F1D1D",
                hero_end="#9F1239",
                accent="#F97316",
                badge_bg="#B91C1C",
            ),
        )

    def _render_html(
        self,
        template: MarketingTemplate,
        persona: EmailPersona,
        preferences_url: str,
        unsubscribe_url: str,
    ) -> str:
        sections_html = "".join(
            _render_section(section, template.palette) for section in template.sections
        )
        testimonial_html = ""
        if template.testimonial and template.testimonial_author:
            testimonial_html = f"""
                <div class="testimonial">
                    <p>“{template.testimonial}”</p>
                    <span>{template.testimonial_author}</span>
                </div>
            """
        primary_cta_html = ""
        if template.primary_cta_label and template.primary_cta_url:
            primary_cta_html = (
                f'<a class="cta-button" href="{template.primary_cta_url}">'
                f"{template.primary_cta_label}</a>"
            )

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>{template.subject}</title>
            <style>
                body {{ margin:0; font-family:'Inter', 'Segoe UI', sans-serif; background:#0b0c10; color:#1f2933; }}
                .wrapper {{ background:#0b0c10; padding:24px; }}
                .container {{ max-width:640px; margin:0 auto; background:#ffffff; border-radius:18px; overflow:hidden; }}
                .preheader {{ display:none; max-height:0; overflow:hidden; }}
                .hero {{
                    background: linear-gradient(135deg, {template.palette.hero_start}, {template.palette.hero_end});
                    padding:48px 40px 56px;
                    color:#fff;
                    position:relative;
                }}
                .hero-badge {{
                    display:inline-block;
                    background:{template.palette.badge_bg};
                    color:#fff;
                    padding:6px 14px;
                    border-radius:999px;
                    font-size:12px;
                    letter-spacing:0.06em;
                    margin-bottom:18px;
                }}
                .hero h1 {{ margin:0 0 16px; font-size:32px; line-height:1.15; }}
                .hero p {{ margin:0; font-size:16px; color:#f5f3ff; }}
                .cta-button {{
                    display:inline-block;
                    margin-top:32px;
                    background:{template.palette.accent};
                    color:#050505 !important;
                    text-decoration:none;
                    padding:14px 24px;
                    border-radius:999px;
                    font-weight:600;
                }}
                .logo {{ padding:32px 40px 0; }}
                .sections {{ padding:32px 40px 40px; background:#ffffff; }}
                .section {{
                    border-radius:16px;
                    padding:24px;
                    margin-bottom:20px;
                    border:1px solid #eef2ff;
                }}
                .section.highlight {{ background:#f8fafc; border-color:{template.palette.accent}33; }}
                .section-eyebrow {{ text-transform:uppercase; letter-spacing:0.08em; font-size:11px; color:#475569; margin-bottom:8px; }}
                .section h3 {{ margin:0 0 12px; font-size:20px; color:#0f172a; }}
                .section p {{ margin:0 0 12px; color:#334155; }}
                .section ul {{ padding-left:20px; margin:0; color:#1e293b; }}
                .section li {{ margin-bottom:6px; }}
                .testimonial {{
                    border-radius:16px;
                    background:#0f172a;
                    color:#f8fafc;
                    padding:24px;
                    margin-top:24px;
                    font-style:italic;
                }}
                .testimonial span {{ display:block; margin-top:8px; font-style:normal; font-size:14px; color:#cbd5f5; }}
                .signature {{ padding:0 40px 32px; color:#0f172a; }}
                .footer {{
                    text-align:center;
                    padding:32px 24px 40px;
                    font-size:12px;
                    color:#94a3b8;
                }}
                .footer a {{ color:{BRAND_THEME.primary_color}; text-decoration:none; }}
            </style>
        </head>
        <body>
            <div class="preheader">{template.preview_text}</div>
            <div class="wrapper">
                <div class="container">
                    <div class="logo">
                        <img src="{BRAND_THEME.logo_url}" alt="{BRAND_THEME.name} logo" height="32" style="display:block;" />
                    </div>
                    <div class="hero">
                        <span class="hero-badge">{template.hero_badge}</span>
                        <h1>{template.hero_title}</h1>
                        <p>{template.hero_subtitle}</p>
                        {primary_cta_html}
                    </div>
                    <div class="sections">
                        {sections_html}
                        {testimonial_html}
                    </div>
                    <div class="signature">
                        <p>Let me know where you want to focus first.</p>
                        <p>{persona.signature_block()}</p>
                    </div>
                    <div class="footer">
                        <p>
                            Sent by {BRAND_THEME.name} · {BRAND_THEME.footer_address}<br/>
                            <a href="mailto:{BRAND_THEME.support_email}">{BRAND_THEME.support_email}</a>
                            · <a href="{preferences_url}">Manage preferences</a><br/>
                            <a href="{unsubscribe_url}">Unsubscribe instantly</a>
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """


def _render_section(section: EmailSection, palette: Palette) -> str:
    eyebrow = (
        f'<div class="section-eyebrow">{section.icon or ""} {section.eyebrow}</div>'
        if section.eyebrow
        else ""
    )
    bullets_html = ""
    if section.bullets:
        bullet_items = "".join(f"<li>{item}</li>" for item in section.bullets)
        bullets_html = f"<ul>{bullet_items}</ul>"
    cta_html = ""
    if section.cta_label and section.cta_url:
        cta_html = (
            f'<a href="{section.cta_url}" '
            f'style="display:inline-block;margin-top:14px;color:{palette.accent};font-weight:600;">'
            f"{section.cta_label}</a>"
        )
    highlight_class = "section highlight" if section.highlight else "section"
    return f"""
        <div class="{highlight_class}">
            {eyebrow}
            <h3>{section.title}</h3>
            <p>{section.body}</p>
            {bullets_html}
            {cta_html}
        </div>
    """


def _first_name(context: Mapping[str, Any], user: User) -> str:
    if "first_name" in context:
        return str(context["first_name"])
    name = getattr(user, "name", "") or ""
    if name.strip():
        return name.strip().split(" ")[0]
    email = getattr(user, "email", "")
    return email.split("@")[0] if email else "there"


def _build_unsubscribe_url(preference: EmailPreference, context: Mapping[str, Any]) -> str:
    custom = context.get("unsubscribe_url")
    if custom:
        return str(custom)
    base = MARKETING_EMAIL_UNSUBSCRIBE_URL
    separator = "&" if "?" in base else "?"
    return f"{base}{separator}token={preference.unsubscribe_token}"


def _sanitize_context(context: Mapping[str, Any]) -> dict[str, Any]:
    allowed_types = (str, int, float, bool, type(None))
    safe: dict[str, Any] = {}
    for key, value in context.items():
        if isinstance(value, allowed_types):
            safe[str(key)] = value
    return safe
