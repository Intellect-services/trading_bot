# … earlier imports unchanged …

# Initialize configuration
config = Config(
    ALPACA_API_KEY=os.getenv("ALPACA_API_KEY", ""),
    ALPACA_SECRET_KEY=os.getenv("ALPACA_SECRET_KEY", ""),
    ALPACA_PAPER=os.getenv("ALPACA_PAPER", "True").lower() == "true",
    INITIAL_CAPITAL=float(os.getenv("INITIAL_CAPITAL", "100000")),
    RISK_MAX_POSITION_SIZE=float(os.getenv("RISK_MAX_POSITION_SIZE", "0.1")),
    RISK_PER_TRADE=float(os.getenv("RISK_PER_TRADE", "0.01")),
    RISK_STOP_LOSS_PCT=float(os.getenv("RISK_STOP_LOSS_PCT", "0.02")),
    RISK_TAKE_PROFIT_PCT=float(os.getenv("RISK_TAKE_PROFIT_PCT", "0.04")),
)

# … later, OAuth registrations …

google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url="https://accounts.google.com/o/oauth2/token",
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    api_base_url="https://www.googleapis.com/oauth2/v1/",
    client_kwargs={"scope": "email profile"},
)

github = oauth.register(
    name="github",
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)

linkedin = oauth.register(
    name="linkedin",
    client_id=os.getenv("LINKEDIN_CLIENT_ID"),
    client_secret=os.getenv("LINKEDIN_CLIENT_SECRET"),
    access_token_url="https://www.linkedin.com/oauth/v2/accessToken",
    authorize_url="https://www.linkedin.com/oauth/v2/authorization",
    api_base_url="https://api.linkedin.com/v2/",
    client_kwargs={"scope": "r_liteprofile r_emailaddress"},
)

# … and so on through the rest of the file …
