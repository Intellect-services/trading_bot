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

# Alpaca API URLs
ALPACA_PAPER_API_URL = "https://paper-api.alpaca.markets"
ALPACA_LIVE_API_URL = "https://api.alpaca.markets"
ALPACA_DATA_API_URL = "https://data.alpaca.markets"
