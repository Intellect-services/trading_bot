"""Configuration module."""

import os

from src.config.development import DevelopmentConfig
from src.config.production import ProductionConfig
from src.config.staging import StagingConfig


def get_config() -> type[DevelopmentConfig] | type[ProductionConfig] | type[StagingConfig]:
    """Get configuration based on environment."""
    env = os.getenv("FLASK_ENV", "development")

    if env == "production":
        return ProductionConfig
    if env == "staging":
        return StagingConfig
    return DevelopmentConfig
