"""Shared enum for marketing campaign types."""

from enum import Enum


class MarketingCampaignType(str, Enum):
    """Supported high-impact marketing campaign identifiers."""

    WELCOME_SERIES = "welcome_series"
    PRODUCT_UPDATE = "product_update"
    MARKET_BRIEFING = "market_briefing"
    EDUCATION_SERIES = "education_series"
    REENGAGEMENT = "reengagement"
