"""Flask application for the trading bot."""

import hashlib
import hmac
import logging
import os
import secrets
import sys
import threading
from datetime import datetime, timedelta
from typing import Any, TypeAlias

from authlib.integrations.flask_client import OAuth

# Load environment variables
from dotenv import load_dotenv
from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    request,
    session,
    url_for,
)
from flask_cors import CORS
from flask_session import Session
from flask_socketio import SocketIO, emit
from werkzeug.wrappers.response import Response as WerkzeugResponse

# Type alias for Flask route return types
FlaskResponse: TypeAlias = (
    Response | WerkzeugResponse | str | tuple[Response, int] | tuple[WerkzeugResponse, int]
)
from src.core.alpaca_service import AlpacaService
from src.core.bot import TradingBot
from src.core.portfolio_analytics import PortfolioAnalytics
from src.models.email_event import EmailEvent
from src.models.email_preference import EmailPreference
from src.models.email_send_log import EmailSendLog, EmailSendStatus
from src.models.email_token import TokenType
from src.strategies.moving_average import MovingAverageCrossover
from src.utils.config import Config
from src.utils.rbac import (
    login_required,
    require_email_verified,
    require_trading_enabled,
)

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Subclass Flask so mypy knows about trading_bot attribute
class TradingFlask(Flask):
    trading_bot: TradingBot | None = None


# Configure React frontend path
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
FRONTEND_DIST = os.path.abspath(FRONTEND_DIST)

# instantiate the app as TradingFlask so mypy recognizes trading_bot
# Serve React build from frontend/dist
app: TradingFlask = TradingFlask(
    __name__,
    static_folder=FRONTEND_DIST,
    static_url_path="",
    template_folder=FRONTEND_DIST,
)
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(32))

# Initialize database AFTER app creation
from src.database import init_db

init_db(app)

# Flag to track if auto-restart has been initialized (thread-safe)
_auto_restart_lock = threading.Lock()
_auto_restart_initialized = False


def initialize_bot_auto_restart_once():
    """Initialize bot auto-restart (only once, thread-safe).

    This is called on app startup and ensures bots are restarted
    after server restart if they were running before.
    """
    global _auto_restart_initialized
    with _auto_restart_lock:
        if _auto_restart_initialized:
            return

        _auto_restart_initialized = True
        from src.core.bot_auto_restart import auto_restart_bots

        auto_restart_bots(app)
        logger.info("Bot auto-restart initialized")


# Initialize auto-restart on first request (for gunicorn/production)
@app.before_request
def ensure_bot_auto_restart():
    """Ensure bot auto-restart is initialized (only runs once)."""
    initialize_bot_auto_restart_once()


# Configure session
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "flask_session"
)
app.config["SESSION_FILE_THRESHOLD"] = 100
from src.config.constants import (
    DEFAULT_TRADING_SYMBOLS,
    FRONTEND_URL,
    GITHUB_OAUTH_URL,
    GOOGLE_OAUTH_URL,
    LINKEDIN_OAUTH_URL,
    RESEND_WEBHOOK_SECRET,
    SESSION_LIFETIME_SECONDS,
)


def get_frontend_url() -> str:
    """Get the frontend URL dynamically.

    Tries multiple methods:
    1. Read .frontend.port file (created by isbot script)
    2. Use Origin/Referer header from request
    3. Fall back to FRONTEND_URL constant
    """
    # Try to read the frontend port from the file created by isbot script
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    frontend_port_file = os.path.join(project_root, ".frontend.port")

    if os.path.exists(frontend_port_file):
        try:
            with open(frontend_port_file, encoding="utf-8") as f:
                port = f.read().strip()
                if port and port.isdigit():
                    return f"http://localhost:{port}"
        except Exception as e:
            logger.debug(f"Could not read .frontend.port file: {e}")

    # Try to get from request headers (Origin or Referer)
    try:
        origin = request.headers.get("Origin") or request.headers.get("Referer")
        if origin:
            # Extract the base URL (protocol + host)
            from urllib.parse import urlparse

            parsed = urlparse(origin)
            if parsed.scheme and parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}"
    except Exception as exc:  # nosec B110 - best-effort parsing only
        logger.debug("Failed to infer frontend URL from headers: %s", exc)

    # Fall back to constant
    return FRONTEND_URL


def _verify_resend_signature(payload: bytes, signature: str) -> bool:
    """Verify Resend webhook signature using shared secret."""
    if not RESEND_WEBHOOK_SECRET:
        return True
    try:
        computed = hmac.new(
            RESEND_WEBHOOK_SECRET.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(computed, signature or "")
    except Exception as exc:
        logger.error("Failed to verify Resend signature: %s", exc)
        return False


app.config["PERMANENT_SESSION_LIFETIME"] = SESSION_LIFETIME_SECONDS
Session(app)

# Enable CORS for development
from src.config.constants import CORS_ORIGINS_DEV

cors_origins = []
if os.getenv("FLASK_ENV") != "production":
    # Development: Allow localhost on common Vite ports (5173-5180)
    cors_origins = CORS_ORIGINS_DEV
    CORS(
        app,
        supports_credentials=True,
        resources={r"/*": {"origins": cors_origins}},
        allow_headers=["Content-Type", "Authorization"],
    )
    socketio = SocketIO(app, cors_allowed_origins=cors_origins)
else:
    # Production: Use configured origins
    allowed_origins = (
        os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []
    )
    CORS(
        app,
        supports_credentials=True,
        resources={r"/*": {"origins": allowed_origins}},
        allow_headers=["Content-Type", "Authorization"],
    )
    socketio = SocketIO(app, cors_allowed_origins=allowed_origins if allowed_origins else ["*"])
oauth = OAuth(app)

# Register strategy API routes
from src.api.strategy_routes import register_strategy_routes

register_strategy_routes(app)

# Configuration data for strategy parameters only
# NOTE: Alpaca API credentials are now user-specific and stored in the database
# Users must configure their own credentials in Account Settings
# The ALPACA_API_KEY and ALPACA_API_SECRET env vars are deprecated and only used
# for backward compatibility or system-level operations (if needed)
config_data = {
    "alpaca_api_key_id": "",  # Not used - users provide their own credentials
    "alpaca_api_secret_key": "",  # Not used - users provide their own credentials
    "trading_mode": os.getenv("TRADING_MODE", "paper"),  # Default mode, users can override
    "trading_symbols": DEFAULT_TRADING_SYMBOLS,
    "strategy_symbols": ["AAPL", "MSFT", "GOOGL"],
    "strategy_timeframe": "1D",
    "short_window": 20,
    "long_window": 50,
    "lookback_days": 100,
    "log_level": "INFO",
    "log_file": "trading_bot.log",
    "peak_equity": 0.0,
    "risk_per_trade": 0.02,  # 2% risk per trade
    "risk_max_drawdown": 0.1,  # 10% maximum drawdown
    "risk_max_leverage": 2.0,  # Maximum 2x leverage
    "risk_max_position_size": 0.2,  # Maximum 20% of portfolio in single position
}

# Initialize configuration
config = Config.model_validate(config_data)

# Note: AlpacaService and TradingBot are now user-specific
# Each user must configure their own Alpaca API credentials in Account Settings
# Trading operations will use the user's own credentials from the database
# No global credentials are used for trading - all trading is user-specific
strategy = MovingAverageCrossover(
    short_window=config.short_window, long_window=config.long_window
)  # Strategy config only, no credentials
app.trading_bot = None  # Will be set per user session

# Cache for user-specific bot instances (user_id -> TradingBot instance)
_user_bot_cache: dict[int, TradingBot] = {}


# Helper function to get user-specific AlpacaService
def get_user_alpaca_service(user_id: int) -> AlpacaService | None:
    """Get AlpacaService instance for a specific user.

    Args:
        user_id: User ID.

    Returns:
        AlpacaService instance or None if user has no credentials.
    """
    try:
        return AlpacaService.from_user_credentials(user_id)
    except ValueError as e:
        app.logger.warning(f"Cannot create AlpacaService for user {user_id}: {e}")
        return None


# Helper function to get user-specific TradingBot
def get_user_trading_bot(user_id: int) -> TradingBot | None:
    """Get TradingBot instance for a specific user.
    Uses caching to ensure the same instance is returned across requests.

    Args:
        user_id: User ID.

    Returns:
        TradingBot instance or None if user cannot trade.
    """
    from src.models.user import User

    # Check cache first
    if user_id in _user_bot_cache:
        cached_bot = _user_bot_cache[user_id]
        # Verify the bot is still valid (user can still trade)
        user = User.query.get(user_id)
        if user and user.can_trade():
            return cached_bot
        # User can no longer trade, remove from cache
        del _user_bot_cache[user_id]
        return None

    user = User.query.get(user_id)
    if not user or not user.can_trade():
        return None

    try:
        alpaca_service = get_user_alpaca_service(user_id)
        if not alpaca_service:
            return None

        # Create user-specific trading bot with user's AlpacaService
        # TradingBot requires: config (strategy params), strategy, alpaca_service (user's credentials), user_id, and flask_app (for context)
        user_bot = TradingBot(config, strategy, alpaca_service, user_id, flask_app=app)

        # Cache the bot instance
        _user_bot_cache[user_id] = user_bot

        return user_bot
    except Exception as e:
        app.logger.error(f"Failed to create TradingBot for user {user_id}: {e}")
        return None


# WebSocket event handlers
@socketio.on("connect")
def handle_connect() -> None:
    """Handle client connection."""
    logger.info("Client connected")
    user_id = session.get("user_id")
    if user_id:
        try:
            trading_bot = get_user_trading_bot(user_id)
            if trading_bot:
                status = trading_bot.get_status()
                emit("status_update", status)
            else:
                emit("status_update", {"status": "stopped", "message": "Not configured"})
        except Exception as e:
            logger.error(f"Error emitting dashboard update: {e!s}")
            emit("error", {"message": str(e)})
    else:
        emit("status_update", {"status": "stopped", "message": "Not authenticated"})


@socketio.on("disconnect")
def handle_disconnect() -> None:
    """Handle client disconnection."""
    logger.info("Client disconnected")


@socketio.on("get_initial_status")
def handle_get_initial_status() -> None:
    """Handle initial status request."""
    logger.info("Client requested initial status")
    user_id = session.get("user_id")
    if user_id:
        try:
            trading_bot = get_user_trading_bot(user_id)
            if trading_bot:
                status = trading_bot.get_status()
                emit("status_update", status)
            else:
                emit("status_update", {"status": "stopped", "message": "Not configured"})
        except Exception as e:
            logger.error(f"Error getting initial status: {e}")
            emit("error", {"message": str(e)})
    else:
        emit("status_update", {"status": "stopped", "message": "Not authenticated"})


def emit_dashboard_update() -> None:
    """Emit dashboard update to all connected clients."""
    try:
        with app.app_context():
            # Note: This function is called globally, so we can't get user-specific data here
            # Individual clients should request their own dashboard data via the API
            # For now, emit a generic update
            socketio.emit("dashboard_update", {"status": "update_available"})
    except Exception as e:
        logger.error(f"Error emitting dashboard update: {e}")


# Start background task for periodic updates
def start_background_updates() -> None:
    """Start background task for periodic updates."""
    import threading
    import time

    def update_loop() -> None:
        while True:
            try:
                emit_dashboard_update()
                time.sleep(1)  # Update every second for more responsive UI
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                time.sleep(1)  # Wait before retrying

    thread = threading.Thread(target=update_loop, daemon=True)
    thread.start()
    logger.info("Background update thread started")


# Start background updates when the app starts
start_background_updates()


# React frontend is served by Vite dev server in development
# In production, Flask serves the built React app from frontend/dist
# All non-API routes are handled by React Router


# OAuth configurations
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url=GOOGLE_OAUTH_URL,
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    api_base_url="https://www.googleapis.com/oauth2/v1/",
    client_kwargs={"scope": "email profile"},
)

github = oauth.register(
    name="github",
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    access_token_url=GITHUB_OAUTH_URL,
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)

linkedin = oauth.register(
    name="linkedin",
    client_id=os.getenv("LINKEDIN_CLIENT_ID"),
    client_secret=os.getenv("LINKEDIN_CLIENT_SECRET"),
    access_token_url=LINKEDIN_OAUTH_URL,
    authorize_url="https://www.linkedin.com/oauth/v2/authorization",
    api_base_url="https://api.linkedin.com/v2/",
    client_kwargs={"scope": "r_liteprofile r_emailaddress"},
)


@app.route("/login", methods=["POST"])
@app.route("/api/login", methods=["POST"])
def login() -> FlaskResponse:
    """Handle login authentication (API only - React handles UI)."""
    try:
        from src.database import db
        from src.models.user import User

        # Only accept JSON
        if not request.is_json:
            return jsonify(
                {"status": "error", "message": "Content-Type must be application/json"}
            ), 400

        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        app.logger.debug(f"Login attempt for email: {email}")

        # Look up user in database
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            # Check if email is verified
            if not user.email_verified:
                app.logger.debug(f"Login attempt with unverified email: {email}")
                return jsonify(
                    {
                        "status": "error",
                        "message": "Please verify your email address before logging in. Check your inbox for the verification email.",
                        "email_verified": False,
                    }
                ), 403

            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()

            # Store user info in session
            user_data = user.to_dict()
            session["user_id"] = user.id
            session["user"] = user_data
            session["role"] = user.role
            session["email_verified"] = user.email_verified
            app.logger.debug(f"Login successful for user: {user_data}")

            return jsonify({"status": "success", "user": user_data})

        app.logger.debug("Invalid credentials")
        return jsonify({"status": "error", "message": "Invalid email or password"}), 401
    except Exception as e:
        app.logger.error(f"Login error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# Register page is handled by React Router - no Flask route needed


@app.route("/api/register", methods=["POST"])
def register() -> FlaskResponse:
    """Handle user registration."""
    try:
        from src.database import db
        from src.models.email_token import EmailToken
        from src.models.user import User
        from src.services.email_service import send_verification_email

        data = request.get_json()
        email = data.get("email")
        password = data.get("password")
        name = data.get("name")

        # Validate input
        if not email or not password or not name:
            return jsonify({"status": "error", "message": "All fields are required"}), 400

        # Validate email format
        import re

        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            return jsonify({"status": "error", "message": "Invalid email format"}), 400

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"status": "error", "message": "Email already registered"}), 400

        # Create new user with trader role
        new_user = User(
            email=email,
            name=name,
            avatar=f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&background=667eea&color=fff",
            role="trader",
            email_verified=False,
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.flush()  # Get user ID

        # Ensure default email preferences exist
        EmailPreference.ensure_for_user(new_user.id)

        # Create email verification token
        verification_token = EmailToken.create_verification_token(new_user.id)
        db.session.add(verification_token)
        db.session.commit()

        app.logger.info(f"New user registered: {email}")

        # Send verification email
        email_sent = send_verification_email(new_user, verification_token.token)
        if not email_sent:
            app.logger.warning(f"Failed to send verification email to {email}")

        # Return success but don't auto-login (user must verify email first)
        return jsonify(
            {
                "status": "success",
                "message": "Registration successful. Please check your email to verify your account.",
                "email_verified": False,
                "user": new_user.to_dict(),
            }
        )

    except Exception as e:
        app.logger.error(f"Registration error: {e}")
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/auth/status", methods=["GET"])
def auth_status() -> FlaskResponse:
    """Check current authentication status."""
    if session.get("user_id"):
        from src.models.user import User

        user = User.query.get(session.get("user_id"))
        if user:
            return jsonify({"isAuthenticated": True, "user": user.to_dict()})
    return jsonify({"isAuthenticated": False, "user": None}), 401


@app.route("/api/verify-email", methods=["GET"])
def verify_email() -> FlaskResponse:
    """Verify user email with token."""
    try:
        from src.database import db
        from src.models.email_token import EmailToken
        from src.models.user import User
        from src.services.email_service import send_welcome_email

        token = request.args.get("token")
        if not token:
            return jsonify({"status": "error", "message": "Verification token is required"}), 400

        # Find token
        email_token = EmailToken.query.filter_by(
            token=token, token_type=TokenType.VERIFICATION.value
        ).first()
        if not email_token:
            return jsonify({"status": "error", "message": "Invalid verification token"}), 400

        # Check if token is valid
        if not email_token.is_valid():
            return jsonify(
                {
                    "status": "error",
                    "message": "Verification token has expired or already been used",
                }
            ), 400

        # Get user
        user = User.query.get(email_token.user_id)
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        # Verify email
        user.email_verified = True
        email_token.mark_as_used()
        db.session.commit()

        app.logger.info(f"Email verified for user: {user.email}")

        # Send welcome email
        send_welcome_email(user)

        # Auto-login user
        session["user_id"] = user.id
        session["user"] = user.to_dict()
        session["role"] = user.role
        session["email_verified"] = True

        if request.is_json or request.headers.get("Accept") == "application/json":
            return jsonify(
                {
                    "status": "success",
                    "message": "Email verified successfully",
                    "user": user.to_dict(),
                }
            )

        # Redirect to React frontend with success message
        return redirect(f"{get_frontend_url()}/login?verified=true")

    except Exception as e:
        app.logger.error(f"Email verification error: {e}")
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/resend-verification", methods=["POST"])
def resend_verification() -> FlaskResponse:
    """Resend email verification."""
    try:
        from src.database import db
        from src.models.email_token import EmailToken
        from src.models.user import User
        from src.services.email_service import send_verification_email

        data = request.get_json()
        email = data.get("email")

        if not email:
            return jsonify({"status": "error", "message": "Email is required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            # Don't reveal if email exists for security
            return jsonify(
                {
                    "status": "success",
                    "message": "If an account exists with this email, a verification email has been sent.",
                }
            )

        if user.email_verified:
            return jsonify({"status": "error", "message": "Email is already verified"}), 400

        # Create new verification token
        verification_token = EmailToken.create_verification_token(user.id)
        db.session.add(verification_token)
        db.session.commit()

        # Send verification email
        email_sent = send_verification_email(user, verification_token.token)
        if not email_sent:
            app.logger.warning(f"Failed to send verification email to {email}")

        return jsonify(
            {"status": "success", "message": "Verification email sent. Please check your inbox."}
        )

    except Exception as e:
        app.logger.error(f"Resend verification error: {e}")
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/email/preferences", methods=["GET"])
@login_required
def get_email_preferences() -> FlaskResponse:
    """Return the authenticated user's email preferences."""
    try:
        from src.database import db

        user_id = session.get("user_id")
        if user_id is None:
            return jsonify({"status": "error", "message": "Not authenticated"}), 401
        preference = EmailPreference.ensure_for_user(int(user_id))
        db.session.commit()
        return jsonify({"status": "success", "data": preference.to_dict()})
    except Exception as e:
        logger.error("Failed to load email preferences: %s", e)
        return jsonify({"status": "error", "message": "Unable to fetch preferences"}), 500


@app.route("/api/email/preferences", methods=["PUT"])
@login_required
def update_email_preferences() -> FlaskResponse:
    """Update marketing opt-in for the authenticated user."""
    try:
        from src.database import db

        data = request.get_json() or {}
        if "marketing_opt_in" not in data:
            return jsonify({"status": "error", "message": "marketing_opt_in is required"}), 400

        user_id = session.get("user_id")
        if user_id is None:
            return jsonify({"status": "error", "message": "Not authenticated"}), 401
        preference = EmailPreference.ensure_for_user(int(user_id))

        if bool(data["marketing_opt_in"]):
            preference.resubscribe()
        else:
            preference.mark_unsubscribed("user_preferences")

        db.session.commit()
        return jsonify({"status": "success", "data": preference.to_dict()})
    except Exception as e:
        logger.error("Failed to update email preferences: %s", e)
        return jsonify({"status": "error", "message": "Unable to update preferences"}), 500


@app.route("/api/email/unsubscribe", methods=["GET"])
def unsubscribe_via_token() -> FlaskResponse:
    """One-click unsubscribe endpoint referenced from marketing emails."""
    try:
        from src.database import db

        token = request.args.get("token")
        if not token:
            return jsonify({"status": "error", "message": "Token is required"}), 400

        preference = EmailPreference.from_token(token)
        if not preference:
            return jsonify({"status": "error", "message": "Invalid unsubscribe token"}), 404

        preference.mark_unsubscribed("one-click")
        db.session.commit()
        redirect_url = (
            request.args.get("redirect")
            or f"{get_frontend_url()}/unsubscribe?status=success&token={token}"
        )
        return redirect(redirect_url)
    except Exception as e:
        logger.error("Unsubscribe link failed: %s", e)
        return jsonify({"status": "error", "message": "Unable to unsubscribe"}), 500


@app.route("/api/email/resubscribe", methods=["POST"])
def resubscribe_via_token() -> FlaskResponse:
    """Allow recipients to opt back in using the unsubscribe token."""
    try:
        from src.database import db

        data = request.get_json() or {}
        token = data.get("token")
        if not token:
            return jsonify({"status": "error", "message": "Token is required"}), 400

        preference = EmailPreference.from_token(token)
        if not preference:
            return jsonify({"status": "error", "message": "Invalid token"}), 404

        preference.resubscribe()
        db.session.commit()
        return jsonify({"status": "success", "data": preference.to_dict()})
    except Exception as e:
        logger.error("Resubscribe failed: %s", e)
        return jsonify({"status": "error", "message": "Unable to resubscribe"}), 500


@app.route("/api/email/webhooks/resend", methods=["POST"])
def resend_webhook() -> FlaskResponse:
    """Handle webhook callbacks from Resend for delivery/open/bounce events."""
    from src.database import db

    raw_payload = request.get_data()
    signature = request.headers.get("X-Resend-Signature", "")
    if RESEND_WEBHOOK_SECRET and not _verify_resend_signature(raw_payload, signature):
        logger.warning("Rejected Resend webhook with invalid signature")
        return jsonify({"status": "error", "message": "invalid signature"}), 400

    data = request.get_json(silent=True) or {}
    event_type = data.get("type") or data.get("event") or "unknown"
    email_id = (
        data.get("data", {}).get("email", {}).get("id")
        or data.get("data", {}).get("id")
        or data.get("email_id")
    )

    if not email_id:
        return jsonify({"status": "ignored", "reason": "missing email id"}), 200

    log = EmailSendLog.query.filter_by(provider_message_id=email_id).first()
    if not log:
        logger.info("Resend webhook for unknown message id %s", email_id)
        return jsonify({"status": "ignored", "reason": "unknown message"}), 200

    occurred_at = datetime.utcnow()
    event = EmailEvent(  # type: ignore[call-arg]
        send_log_id=log.id,
        event_type=event_type,
        occurred_at=occurred_at,
        payload=data,
    )
    db.session.add(event)

    log.last_event_type = event_type
    log.last_event_at = occurred_at

    if event_type in {"email.delivered", "email.opened", "email.clicked"}:
        log.status = EmailSendStatus.SENT.value
        log.error_message = None
    elif event_type in {"email.bounced", "email.dropped", "email.complained"}:
        log.status = EmailSendStatus.FAILED.value
        log.error_message = data.get("data", {}).get("error")

    db.session.commit()
    return jsonify({"status": "ok"})


@app.route("/api/forgot-password", methods=["POST"])
def forgot_password() -> FlaskResponse:
    """Request password reset."""
    try:
        from src.database import db
        from src.models.email_token import EmailToken
        from src.models.user import User
        from src.services.email_service import send_password_reset_email

        data = request.get_json()
        email = data.get("email")

        if not email:
            return jsonify({"status": "error", "message": "Email is required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            # Don't reveal if email exists for security
            return jsonify(
                {
                    "status": "success",
                    "message": "If an account exists with this email, a password reset link has been sent.",
                }
            )

        # Create password reset token
        reset_token = EmailToken.create_password_reset_token(user.id)
        db.session.add(reset_token)
        db.session.commit()

        # Send password reset email
        email_sent = send_password_reset_email(user, reset_token.token)
        if not email_sent:
            app.logger.warning(f"Failed to send password reset email to {email}")

        return jsonify(
            {
                "status": "success",
                "message": "If an account exists with this email, a password reset link has been sent.",
            }
        )

    except Exception as e:
        app.logger.error(f"Forgot password error: {e}")
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/reset-password", methods=["POST"])
def reset_password() -> FlaskResponse:
    """Reset password with token."""
    try:
        from src.database import db
        from src.models.email_token import EmailToken
        from src.models.user import User

        data = request.get_json()
        token = data.get("token")
        new_password = data.get("new_password")

        if not token or not new_password:
            return jsonify(
                {"status": "error", "message": "Token and new password are required"}
            ), 400

        if len(new_password) < 6:
            return jsonify(
                {"status": "error", "message": "Password must be at least 6 characters"}
            ), 400

        # Find token
        email_token = EmailToken.query.filter_by(
            token=token, token_type=TokenType.PASSWORD_RESET.value
        ).first()
        if not email_token:
            return jsonify({"status": "error", "message": "Invalid reset token"}), 400

        # Check if token is valid
        if not email_token.is_valid():
            return jsonify(
                {"status": "error", "message": "Reset token has expired or already been used"}
            ), 400

        # Get user
        user = User.query.get(email_token.user_id)
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        # Reset password
        user.set_password(new_password)
        email_token.mark_as_used()
        db.session.commit()

        app.logger.info(f"Password reset for user: {user.email}")

        return jsonify(
            {
                "status": "success",
                "message": "Password reset successfully. Please login with your new password.",
            }
        )

    except Exception as e:
        app.logger.error(f"Password reset error: {e}")
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/auth/<provider>", methods=["GET"])
def auth(provider: str) -> FlaskResponse:
    """Handle OAuth authentication."""
    if provider not in ["google", "github", "linkedin"]:
        return redirect(f"{get_frontend_url()}/login?error=invalid_provider")

    client = oauth.create_client(provider)
    if not client:
        return redirect(f"{get_frontend_url()}/login?error=provider_not_configured")

    # Use absolute URL for OAuth callback
    redirect_uri = url_for("auth_callback", provider=provider, _external=True)
    return redirect(client.authorize_redirect(redirect_uri))


@app.route("/auth/<provider>/callback", methods=["GET"])
def auth_callback(provider: str) -> FlaskResponse:
    """Handle OAuth callback."""
    if provider not in ["google", "github", "linkedin"]:
        return redirect(f"{get_frontend_url()}/login?error=invalid_provider")

    client = oauth.create_client(provider)
    if not client:
        return redirect(f"{get_frontend_url()}/login?error=provider_not_configured")

    try:
        client.authorize_access_token()
        user_info = client.get("userinfo").json()
        session["user"] = user_info
        return redirect(f"{get_frontend_url()}/dashboard")
    except Exception as e:
        app.logger.error(f"OAuth error: {e!s}")
        return redirect(f"{get_frontend_url()}/login?error=auth_failed")


@app.route("/logout", methods=["GET"])
def logout() -> FlaskResponse:
    """Handle user logout."""
    try:
        session.pop("user", None)
        session.pop("user_id", None)
        session.pop("role", None)
        session.pop("email_verified", None)
        return redirect(f"{get_frontend_url()}/login?logged_out=true")
    except Exception as e:
        app.logger.error(f"Logout error: {e!s}")
        return redirect(f"{get_frontend_url()}/login?error=logout_failed")


@app.route("/api/account/profile", methods=["GET", "PUT"])
@login_required
def account_profile() -> (
    Response | WerkzeugResponse | tuple[Response, int] | tuple[WerkzeugResponse, int]
):
    """Get or update user profile."""
    try:
        from src.database import db
        from src.utils.rbac import get_current_user

        user = get_current_user()
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        if request.method == "GET":
            return jsonify({"status": "success", "user": user.to_dict()})

        if request.method == "PUT":
            data = request.get_json()
            if data is None:
                return jsonify({"status": "error", "message": "Invalid JSON"}), 400

            # Update name if provided
            if data.get("name"):
                user.name = data["name"]

            # Update avatar if provided
            if "avatar" in data:
                user.avatar = data["avatar"]

            db.session.commit()

            # Update session
            user_data = user.to_dict()
            session["user"] = user_data
            session["role"] = user.role
            session["email_verified"] = user.email_verified

            app.logger.info(f"Profile updated for user: {user.email}")
            return jsonify({"status": "success", "user": user_data})

        # Should never reach here, but mypy needs it
        return jsonify({"status": "error", "message": "Method not allowed"}), 405

    except Exception as e:
        app.logger.error(f"Profile update error: {e}")
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/account/password", methods=["PUT"])
@login_required
def update_password() -> FlaskResponse:
    """Update user password."""
    try:
        from src.database import db
        from src.utils.rbac import get_current_user

        user = get_current_user()
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        data = request.get_json()
        current_password = data.get("current_password")
        new_password = data.get("new_password")

        # Validate input
        if not current_password or not new_password:
            return jsonify(
                {"status": "error", "message": "Current and new password are required"}
            ), 400

        if len(new_password) < 6:
            return jsonify(
                {"status": "error", "message": "Password must be at least 6 characters"}
            ), 400

        # Verify current password
        if not user.check_password(current_password):
            return jsonify({"status": "error", "message": "Current password is incorrect"}), 401

        # Update password
        user.set_password(new_password)
        db.session.commit()

        app.logger.info(f"Password updated for user: {user.email}")
        return jsonify({"status": "success", "message": "Password updated successfully"})

    except Exception as e:
        app.logger.error(f"Password update error: {e}")
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/account/credentials", methods=["GET", "POST", "DELETE"])
@login_required
@require_email_verified
def account_credentials() -> (
    Response | WerkzeugResponse | tuple[Response, int] | tuple[WerkzeugResponse, int]
):
    """Get, save, or delete user Alpaca credentials."""
    try:
        from src.database import db
        from src.models.user_credentials import UserCredentials
        from src.utils.rbac import get_current_user

        user = get_current_user()
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        if request.method == "GET":
            # Get credentials (without secrets unless explicitly requested)
            credentials = UserCredentials.get_by_user_id(user.id)
            if credentials:
                return jsonify(
                    {"status": "success", "credentials": credentials.to_dict(include_secrets=False)}
                )
            return jsonify(
                {"status": "success", "credentials": None, "message": "No credentials configured"}
            )

        if request.method == "POST":
            data = request.get_json()
            if data is None:
                return jsonify({"status": "error", "message": "Invalid JSON"}), 400
            api_key = data.get("alpaca_api_key")
            secret_key = data.get("alpaca_secret_key")
            trading_mode = data.get("trading_mode", "paper")

            if not api_key or not secret_key:
                return jsonify(
                    {"status": "error", "message": "API key and secret key are required"}
                ), 400

            if trading_mode not in ["paper", "live"]:
                return jsonify(
                    {"status": "error", "message": "Trading mode must be 'paper' or 'live'"}
                ), 400

            # Get or create credentials
            credentials = UserCredentials.get_by_user_id(user.id)
            if not credentials:
                credentials = UserCredentials()
                credentials.user_id = user.id
                db.session.add(credentials)

            # Set credentials (will be encrypted)
            credentials.set_credentials(api_key, secret_key, trading_mode)
            db.session.commit()

            app.logger.info(f"Credentials saved for user: {user.email}")
            return jsonify(
                {
                    "status": "success",
                    "message": "Credentials saved successfully",
                    "credentials": credentials.to_dict(include_secrets=False),
                }
            )

        if request.method == "DELETE":
            credentials = UserCredentials.get_by_user_id(user.id)
            if credentials:
                db.session.delete(credentials)
                db.session.commit()
                app.logger.info(f"Credentials deleted for user: {user.email}")
                return jsonify({"status": "success", "message": "Credentials deleted successfully"})
            return jsonify({"status": "error", "message": "No credentials found"}), 404

        # Should never reach here, but mypy needs it
        return jsonify({"status": "error", "message": "Method not allowed"}), 405

    except Exception as e:
        app.logger.error(f"Credentials error: {e}")
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/account/credentials/test", methods=["POST"])
@login_required
@require_email_verified
def test_credentials() -> FlaskResponse:
    """Test Alpaca API connection with user credentials."""
    try:
        from src.database import db
        from src.models.user_credentials import UserCredentials
        from src.utils.rbac import get_current_user

        user = get_current_user()
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        # Get credentials from request or database
        data = request.get_json()
        credentials_used: UserCredentials | None = None
        if data and data.get("alpaca_api_key") and data.get("alpaca_secret_key"):
            # Test with provided credentials
            api_key = data.get("alpaca_api_key")
            secret_key = data.get("alpaca_secret_key")
            trading_mode = data.get("trading_mode", "paper")
        else:
            # Test with saved credentials
            credentials = UserCredentials.get_by_user_id(user.id)
            if not credentials or not credentials.has_credentials():
                return jsonify(
                    {
                        "status": "error",
                        "message": "No credentials configured. Please save credentials first.",
                    }
                ), 400

            credentials_used = credentials
            api_key = credentials.get_api_key()
            secret_key = credentials.get_secret_key()
            trading_mode = credentials.trading_mode

        try:
            service = AlpacaService(
                api_key=api_key, secret_key=secret_key, trading_mode=trading_mode
            )
            account = service.get_account()

            # If credentials are from database and test succeeds, mark as verified
            if credentials_used is not None:
                credentials_used.mark_verified()
                db.session.commit()
            else:
                # If testing with provided credentials, save and mark as verified
                stored_credentials = UserCredentials.get_by_user_id(user.id)
                if not stored_credentials:
                    stored_credentials = UserCredentials()
                    stored_credentials.user_id = user.id
                    db.session.add(stored_credentials)

                stored_credentials.set_credentials(api_key, secret_key, trading_mode)
                stored_credentials.mark_verified()
                db.session.commit()

            return jsonify(
                {
                    "status": "success",
                    "message": "Connection successful",
                    "account_status": account.get("status"),
                    "trading_blocked": account.get("trading_blocked"),
                    "account_blocked": account.get("account_blocked"),
                }
            )

        except Exception as api_error:
            app.logger.error(f"Alpaca API test failed: {api_error}")
            return jsonify({"status": "error", "message": f"Connection failed: {api_error!s}"}), 400

    except Exception as e:
        app.logger.error(f"Test credentials error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/start", methods=["POST"])
@login_required
@require_trading_enabled
def start_bot() -> FlaskResponse:
    """Start the trading bot and persist state."""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"status": "error", "message": "Not authenticated"}), 401

        trading_bot = get_user_trading_bot(user_id)
        if trading_bot is None:
            return jsonify(
                {
                    "status": "error",
                    "message": "Trading bot not available. Please configure your Alpaca credentials.",
                }
            ), 400

        # Start the bot
        trading_bot.start()

        # Persist bot state to database
        from src.core.bot_state_manager import BotStateManager

        BotStateManager.set_bot_is_running(user_id, True)
        BotStateManager.set_bot_auto_start(user_id, True)  # Enable auto-start

        app.logger.info(f"Trading bot started for user {user_id} (persisted to database)")
        return jsonify({"status": "success", "message": "Trading bot started"})
    except Exception as e:
        app.logger.error(f"Error starting bot: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/stop", methods=["POST"])
@login_required
def stop_bot() -> FlaskResponse:
    """Stop the trading bot and persist state."""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"status": "error", "message": "Not authenticated"}), 401

        trading_bot = get_user_trading_bot(user_id)
        if trading_bot is None:
            return jsonify({"status": "error", "message": "Trading bot not running"}), 400

        # Stop the bot
        trading_bot.stop()

        # Persist bot state to database
        from src.core.bot_state_manager import BotStateManager

        BotStateManager.set_bot_is_running(user_id, False)
        BotStateManager.set_bot_auto_start(user_id, False)  # Disable auto-start

        app.logger.info(f"Trading bot stopped for user {user_id} (persisted to database)")
        return jsonify({"status": "success", "message": "Trading bot stopped"})
    except Exception as e:
        app.logger.error(f"Error stopping bot: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/status", methods=["GET"])
@login_required
def get_status() -> FlaskResponse:
    """Get bot status with market hours and next open time."""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"status": "error", "message": "Not authenticated"}), 401

        trading_bot = get_user_trading_bot(user_id)

        # Sync bot state with database
        from src.core.bot_state_manager import BotStateManager

        if trading_bot is not None:
            status = trading_bot.get_status()
            # Sync actual running state with database
            actual_is_running = trading_bot.is_running
            db_is_running = BotStateManager.get_bot_is_running(user_id)

            # If there's a mismatch, update database to match reality
            if actual_is_running != db_is_running:
                BotStateManager.set_bot_is_running(user_id, actual_is_running)

            # Add bot state from database
            bot_state = BotStateManager.get_bot_state(user_id)
            status["bot_auto_start"] = bot_state.get("bot_auto_start", False)
        else:
            status = {"status": "stopped", "message": "Trading bot not configured"}
            # Get bot state from database even if bot not created
            bot_state = BotStateManager.get_bot_state(user_id)
            status["bot_auto_start"] = bot_state.get("bot_auto_start", False)
            status["bot_is_running"] = False

        # Add market hours information
        alpaca_service = get_user_alpaca_service(user_id)
        if alpaca_service:
            try:
                clock = alpaca_service.get_clock()
                status["market_status"] = "open" if clock.get("is_open", False) else "closed"
                status["next_open"] = clock.get("next_open")
                status["next_close"] = clock.get("next_close")
                status["current_time"] = clock.get("timestamp")
            except Exception as e:
                logger.warning(f"Could not get market clock: {e}")
                status["market_status"] = "unknown"

        return jsonify(status)
    except Exception as e:
        app.logger.error(f"Error getting status: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/dashboard/data", methods=["GET"])
@login_required
@require_email_verified
def get_dashboard_data() -> FlaskResponse:
    """Get all dashboard data."""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"status": "error", "message": "Not authenticated"}), 401

        logger.debug(f"Getting dashboard data for user {user_id}...")

        # Get user-specific services
        alpaca_service = get_user_alpaca_service(user_id)
        trading_bot = get_user_trading_bot(user_id)

        # Get bot status
        if trading_bot is not None:
            status = trading_bot.get_status()
        else:
            status = {"status": "stopped", "message": "Trading bot not configured"}
        logger.debug(f"Bot status: {status}")

        # Get account information with safe defaults
        if alpaca_service:
            account = alpaca_service.get_account()
        else:
            account = {
                "portfolio_value": 0.0,
                "buying_power": 0.0,
                "equity": 0.0,
                "cash": 0.0,
                "initial_margin": 0.0,
                "last_equity": 0.0,
            }
        logger.debug(f"Account info: {account}")

        # Ensure all account values are floats with defaults
        account_data = {
            "portfolio_value": float(account.get("portfolio_value", 0)),
            "buying_power": float(account.get("buying_power", 0)),
            "equity": float(account.get("equity", 0)),
            "cash": float(account.get("cash", 0)),
            "initial_margin": float(account.get("initial_margin", 0)),
            "last_equity": float(account.get("last_equity", 0)),
        }

        # Get current positions
        positions = alpaca_service.get_positions() if alpaca_service else []
        logger.debug(f"Positions: {positions}")

        # Calculate performance metrics
        win_rate = trading_bot.get_win_rate() if trading_bot else 0.0
        performance: dict[str, Any] = {
            "total_pnl": account_data["portfolio_value"] - account_data["initial_margin"],
            "daily_pnl": account_data["portfolio_value"] - account_data["last_equity"],
            "win_rate": win_rate,
            "history": [],
        }
        logger.debug(f"Performance metrics: {performance}")

        # Get historical portfolio value from orders and account activity
        # This creates a portfolio history based on actual trading activity
        allowed_periods = {"1D", "1W", "1M", "3M", "6M", "1Y", "all"}
        allowed_timeframes = {"1Min", "5Min", "15Min", "1H", "1Hour", "1D", "1Day"}

        portfolio_period = request.args.get("portfolioPeriod", "1M")
        if portfolio_period not in allowed_periods:
            portfolio_period = "1M"
        portfolio_timeframe = request.args.get("portfolioTimeframe", "1D")
        if portfolio_timeframe not in allowed_timeframes:
            portfolio_timeframe = "1D"

        if alpaca_service:
            history_points = []
            # Try multiple periods to get any available history
            periods_to_try = [portfolio_period, "all", "1Y", "3M", "1M", "1W"]

            for period in periods_to_try:
                try:
                    history_points = alpaca_service.get_portfolio_history(
                        period=period,
                        timeframe=portfolio_timeframe,
                    )
                    if history_points and len(history_points) > 0:
                        logger.info(
                            f"Found {len(history_points)} portfolio history points for period {period}"
                        )
                        break
                except Exception as e:
                    logger.debug(f"Failed to get portfolio history for period {period}: {e}")
                    continue

            if history_points and len(history_points) > 0:
                try:
                    analytics = PortfolioAnalytics()
                    metrics = analytics.calculate_metrics(history_points)
                    performance["history"] = [
                        {
                            "timestamp": point["timestamp"],
                            "portfolio_value": point["equity"],
                            "daily_return": point["profit_loss_pct"],
                        }
                        for point in history_points
                    ]
                    performance["sharpe_ratio"] = metrics["sharpe"]
                    performance["max_drawdown"] = metrics["max_drawdown"]
                    performance["cumulative_return"] = metrics["cumulative_return"]
                except Exception as e:
                    logger.error(f"Error calculating portfolio analytics: {e}")
                    # Use raw history points even if analytics fail
                    performance["history"] = [
                        {
                            "timestamp": point["timestamp"],
                            "portfolio_value": point["equity"],
                            "daily_return": point.get("profit_loss_pct", 0.0),
                        }
                        for point in history_points
                    ]
            else:
                # Fallback: Generate a basic history from current account value
                logger.info("No portfolio history available from Alpaca, generating fallback data")
                current_value = account_data["portfolio_value"]
                if current_value > 0:
                    # Generate 30 days of history with current value
                    now = datetime.now()
                    history = []
                    for days_ago in range(30, -1, -1):
                        history.append(
                            {
                                "timestamp": (now - timedelta(days=days_ago)).strftime(
                                    "%Y-%m-%dT%H:%M:%S"
                                ),
                                "portfolio_value": current_value,  # Use current value for all points initially
                                "daily_return": 0.0,
                            }
                        )
                    performance["history"] = history
                else:
                    # No account value either, just use current timestamp
                    performance["history"] = [
                        {
                            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                            "portfolio_value": 0.0,
                            "daily_return": 0.0,
                        }
                    ]

        # Construct response
        response = {
            "status": "success",
            "account": account_data,
            "positions": positions,
            "performance": performance,
            **status,  # Include all status information
        }
        logger.debug(
            f"Sending dashboard data - portfolio_value: {account_data.get('portfolio_value')}, equity: {account_data.get('equity')}, cash: {account_data.get('cash')}"
        )
        logger.debug(f"Full response account keys: {list(account_data.keys())}")
        return jsonify(response)

    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check() -> FlaskResponse:
    """Health check endpoint for Railway."""
    return jsonify({"status": "healthy", "service": "trading-bot"}), 200


@app.route("/health/detailed", methods=["GET"])
def health_check_detailed() -> FlaskResponse:
    """Detailed health check endpoint."""
    health_status: dict[str, Any] = {"status": "healthy", "service": "trading-bot", "checks": {}}

    # Check database
    try:
        from src.database import db

        db.session.execute(db.text("SELECT 1"))
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["checks"]["database"] = f"error: {e!s}"
        health_status["status"] = "unhealthy"

    # Check encryption
    try:
        from src.utils.encryption import get_encryption_key

        get_encryption_key()
        health_status["checks"]["encryption"] = "ok"
    except Exception as e:
        health_status["checks"]["encryption"] = f"error: {e!s}"
        health_status["status"] = "unhealthy"

    # Check email service
    try:
        import os

        if os.getenv("RESEND_API_KEY"):
            health_status["checks"]["email"] = "configured"
        else:
            health_status["checks"]["email"] = "not_configured"
    except Exception as e:
        health_status["checks"]["email"] = f"error: {e!s}"

    status_code = 200 if health_status["status"] == "healthy" else 503
    return jsonify(health_status), status_code


@app.route("/api/features/status", methods=["GET"])
@login_required
def get_features_status() -> FlaskResponse:
    """Get comprehensive features status and market information."""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"status": "error", "message": "Not authenticated"}), 401

        alpaca_service = get_user_alpaca_service(user_id)

        # Check what features are implemented
        features = {
            "portfolio_history": {
                "implemented": True,
                "description": "Portfolio equity history (FREE Alpaca endpoint)",
                "ui_location": "Dashboard portfolio chart",
                "works_when_closed": True,
            },
            "account_activities": {
                "implemented": True,
                "description": "Account activities (fills, orders, etc.)",
                "ui_location": "Not exposed yet (backend only)",
                "works_when_closed": True,
            },
            "bracket_orders": {
                "implemented": True,
                "description": "Bracket orders (entry + TP + SL)",
                "ui_location": "Order form (may need order type selector)",
                "works_when_closed": True,  # Orders queue when market closed
            },
            "trailing_stop_orders": {
                "implemented": True,
                "description": "Trailing stop orders",
                "ui_location": "Order form",
                "works_when_closed": True,
            },
            "stop_orders": {
                "implemented": True,
                "description": "Stop and stop-limit orders",
                "ui_location": "Order form",
                "works_when_closed": True,
            },
            "websocket_streaming": {
                "implemented": True,
                "description": "Real-time market data streaming",
                "ui_location": "Background (automatic)",
                "works_when_closed": False,  # Only streams when market open
            },
            "data_cache": {
                "implemented": True,
                "description": "Market data caching system",
                "ui_location": "Transparent (backend only)",
                "works_when_closed": True,
            },
            "data_provider_fallbacks": {
                "implemented": True,
                "description": "Yahoo Finance, Alpha Vantage fallbacks",
                "ui_location": "Transparent (backend only)",
                "works_when_closed": True,
            },
            "ai_strategies": {
                "implemented": True,
                "description": "AI-enhanced trading strategies with ML models",
                "ui_location": "Strategy creation (type='ai')",
                "works_when_closed": True,  # Can create/config when closed
            },
            "portfolio_analytics": {
                "implemented": True,
                "description": "Portfolio performance analytics",
                "ui_location": "Dashboard",
                "works_when_closed": True,
            },
        }

        # Get market hours
        market_info = {}
        if alpaca_service:
            try:
                clock = alpaca_service.get_clock()
                market_info = {
                    "is_open": clock.get("is_open", False),
                    "next_open": clock.get("next_open"),
                    "next_close": clock.get("next_close"),
                    "current_time": clock.get("timestamp"),
                    "market_hours": "Monday-Friday, 9:30 AM - 4:00 PM Eastern Time",
                    "timezone": "ET (Eastern Time)",
                }
            except Exception as e:
                logger.warning(f"Could not get market clock: {e}")
                market_info = {"error": str(e)}

        return jsonify(
            {
                "status": "success",
                "features": features,
                "market": market_info,
                "summary": {
                    "total_features": len([f for f in features.values() if f["implemented"]]),
                    "features_available_when_closed": len(
                        [f for f in features.values() if f.get("works_when_closed", False)]
                    ),
                },
            }
        )
    except Exception as e:
        app.logger.error(f"Error getting features status: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/history", methods=["GET"])
@login_required
@require_email_verified
def get_history() -> FlaskResponse:
    """Get trade history."""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"status": "error", "message": "Not authenticated"}), 401

        alpaca_service = get_user_alpaca_service(user_id)
        if not alpaca_service:
            return jsonify(
                {"status": "error", "message": "Trading credentials not configured"}
            ), 400

        # Get closed orders
        orders = alpaca_service.get_orders(status="closed", limit=50)
        return jsonify({"status": "success", "orders": orders})
    except Exception as e:
        app.logger.error(f"Error getting history: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/settings", methods=["GET", "POST"])
def settings() -> Response | WerkzeugResponse | tuple[Response, int] | tuple[WerkzeugResponse, int]:
    """Get or update settings."""
    try:
        if request.method == "GET":
            # Return current config
            return jsonify({"status": "success", "settings": config.model_dump()})

        if request.method == "POST":
            data = request.get_json()
            if data is None:
                return jsonify({"status": "error", "message": "Invalid JSON"}), 400
            app.logger.info(f"Updating settings: {data}")

            # Update config object
            # Note: In a real app, we should validate these and persist to .env or DB
            if "trading_symbols" in data:
                # Handle comma-separated string or list
                if isinstance(data["trading_symbols"], str):
                    config.trading_symbols = [s.strip() for s in data["trading_symbols"].split(",")]
                else:
                    config.trading_symbols = data["trading_symbols"]

            if "trading_stop_loss" in data:
                config.trading_stop_loss = float(data["trading_stop_loss"])

            if "risk_max_drawdown" in data:
                config.risk_max_drawdown = float(data["risk_max_drawdown"])

            if "trading_mode" in data:
                config.trading_mode = data["trading_mode"]

            return jsonify(
                {
                    "status": "success",
                    "message": "Settings updated",
                    "settings": config.model_dump(),
                }
            )

        # Should never reach here, but mypy needs it
        return jsonify({"status": "error", "message": "Method not allowed"}), 405

    except Exception as e:
        app.logger.error(f"Error handling settings: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# Catch-all route for React Router (must be last)
# This serves the React app for all non-API routes
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react_app(path: str) -> FlaskResponse:
    """Serve React app for all non-API routes."""
    # Don't serve React for API routes
    if path.startswith(("api/", "auth/", "health")):
        return jsonify({"status": "error", "message": "Not found"}), 404

    # Allow static assets (JS, CSS, images, etc.) to be served normally
    if path and "." in path.split("/")[-1]:
        # This is likely a static file - let Flask handle it
        try:
            return app.send_static_file(path)
        except Exception as exc:  # nosec B110 - safe fallback to index.html
            logger.debug("Static file %s not found, falling back to index.html: %s", path, exc)

    # In development, React is served by Vite dev server
    # In production, serve index.html from React build
    if os.path.exists(os.path.join(FRONTEND_DIST, "index.html")):
        return app.send_static_file("index.html")

    # Development mode - redirect to Vite dev server or show message
    return jsonify(
        {
            "status": "info",
            "message": "React frontend not built. Please run 'npm run build' in src/frontend or use Vite dev server.",
        }
    ), 503


if __name__ == "__main__":
    try:
        # Note: Trading bot is now user-specific and will be started per user session
        # No global bot initialization needed

        # Start background updates
        start_background_updates()

        # Auto-restart bots for users with auto-start enabled
        from src.core.bot_auto_restart import auto_restart_bots

        auto_restart_bots(app)
        logger.info("Bot auto-restart initialized - bots will restart on server startup if enabled")

        run_host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
        run_port = int(os.getenv("FLASK_RUN_PORT", "5002"))
        debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
        allow_unsafe = os.getenv("ALLOW_UNSAFE_WERKZEUG", "false").lower() == "true"

        socketio.run(
            app,
            host=run_host,
            port=run_port,
            debug=debug_mode,
            allow_unsafe_werkzeug=allow_unsafe,
        )
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        sys.exit(1)
