"""Application constants and default configuration values."""

import os

# API Configuration
DEFAULT_API_PORT = int(os.getenv("FLASK_RUN_PORT", "5002"))
DEFAULT_FRONTEND_PORT = int(os.getenv("VITE_PORT", "5173"))
DEFAULT_BACKEND_HOST = os.getenv("FLASK_HOST", "127.0.0.1")

# Frontend API URL (build-time variable for Vite)
API_URL = os.getenv("VITE_API_URL", os.getenv("API_URL", f"http://localhost:{DEFAULT_API_PORT}"))

# Application URL
APP_URL = os.getenv("APP_URL", f"http://localhost:{DEFAULT_API_PORT}")

# Frontend URL (for redirects)
FRONTEND_URL = os.getenv("FRONTEND_URL", f"http://localhost:{DEFAULT_FRONTEND_PORT}")

# CORS Configuration
CORS_ORIGINS_DEV = [f"http://localhost:{port}" for port in range(5173, 5181)] + [
    f"http://127.0.0.1:{port}" for port in range(5173, 5181)
]

# Trading Configuration
DEFAULT_TRADING_SYMBOLS: list[str] = os.getenv("DEFAULT_TRADING_SYMBOLS", "AAPL,MSFT,GOOGL").split(
    ","
)

DEFAULT_STRATEGY_SYMBOLS: list[str] = os.getenv(
    "DEFAULT_STRATEGY_SYMBOLS", "AAPL,MSFT,GOOGL"
).split(",")

# OAuth Configuration
GOOGLE_OAUTH_URL = os.getenv("GOOGLE_OAUTH_URL", "https://accounts.google.com/o/oauth2/token")
GITHUB_OAUTH_URL = os.getenv("GITHUB_OAUTH_URL", "https://github.com/login/oauth/access_token")
LINKEDIN_OAUTH_URL = os.getenv(
    "LINKEDIN_OAUTH_URL", "https://www.linkedin.com/oauth/v2/accessToken"
)

# Session Configuration
SESSION_LIFETIME_SECONDS = int(os.getenv("SESSION_LIFETIME_SECONDS", "3600"))  # 1 hour

# Email Configuration
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@intellectscout.com")

# Brand & Marketing Configuration
BRAND_NAME = os.getenv("BRAND_NAME", "IntellectScout")
BRAND_PRIMARY_COLOR = os.getenv("BRAND_PRIMARY_COLOR", "#4338CA")
BRAND_SECONDARY_COLOR = os.getenv("BRAND_SECONDARY_COLOR", "#14B8A6")
BRAND_LOGO_URL = os.getenv("BRAND_LOGO_URL", f"{FRONTEND_URL}/assets/email-logo.svg")
BRAND_SUPPORT_EMAIL = os.getenv("BRAND_SUPPORT_EMAIL", "support@intellectscout.com")
BRAND_FOOTER_ADDRESS = os.getenv(
    "BRAND_FOOTER_ADDRESS", "500 Market Street, San Francisco, CA 94105"
)
MARKETING_EMAIL_PERSONA_NAME = os.getenv("MARKETING_EMAIL_PERSONA_NAME", "Andrew")
MARKETING_EMAIL_PERSONA_TITLE = os.getenv("MARKETING_EMAIL_PERSONA_TITLE", "Customer Success Lead")
MARKETING_EMAIL_PERSONA_EMAIL = os.getenv(
    "MARKETING_EMAIL_PERSONA_EMAIL", "andrew@intellectscout.com"
)
MARKETING_EMAIL_REPLY_TO = os.getenv("MARKETING_EMAIL_REPLY_TO", BRAND_SUPPORT_EMAIL)
MARKETING_EMAIL_FROM_FORMAT = os.getenv(
    "MARKETING_EMAIL_FROM_FORMAT", "{persona_name} from {brand_name} <{persona_email}>"
)
MARKETING_EMAIL_UNSUBSCRIBE_URL = os.getenv(
    "MARKETING_EMAIL_UNSUBSCRIBE_URL", f"{APP_URL}/api/email/unsubscribe"
)
RESEND_WEBHOOK_SECRET = os.getenv("RESEND_WEBHOOK_SECRET", "")

# Alpaca API URLs
ALPACA_PAPER_API_URL = "https://paper-api.alpaca.markets"
ALPACA_LIVE_API_URL = "https://api.alpaca.markets"
ALPACA_DATA_API_URL = "https://data.alpaca.markets"
