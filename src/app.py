"""Flask application for trading bot."""

import logging
import os
import threading
import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, TypeVar, Union, cast

from authlib.integrations.flask_client import OAuth
from flask import Flask, redirect, render_template, request, session, url_for
from flask_socketio import SocketIO
from werkzeug.wrappers.response import Response as WerkzeugResponse

from .core.alpaca_service import AlpacaService
from .core.bot_service import BotService
from .core.trading_bot import TradingBot
from .strategies.moving_average import MovingAverageCrossover
from .utils.config import Config

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key")
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize configuration
config = Config()

# Initialize services
try:
    alpaca_service = AlpacaService(config)
    bot_service = BotService(config)
    logger.info("Successfully initialized AlpacaService and BotService")
except Exception as e:
    logger.error(f"Failed to initialize services: {e}")
    # Initialize in demo mode if services fail
    demo_mode = True
    logger.info("Running in demo mode")
else:
    demo_mode = False

# Global state
bot_status: Dict[str, Any] = {
    "status": "stopped",
    "market_status": "closed",
    "runtime": "0:00:00",
    "last_update": None,
    "metrics": {
        "initial_capital": 0.0,
        "current_capital": 0.0,
        "total_trades": 0,
        "win_rate": 0.0,
        "profit_factor": 0.0,
        "sharpe_ratio": 0.0,
        "active_positions": 0,
    },
}

# OAuth configuration
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url="https://accounts.google.com/o/oauth2/token",
    access_token_params=None,
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params=None,
    api_base_url="https://www.googleapis.com/oauth2/v1/",
    client_kwargs={"scope": "email profile"},
)

github = oauth.register(
    name="github",
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    access_token_url="https://github.com/login/oauth/access_token",
    access_token_params=None,
    authorize_url="https://github.com/login/oauth/authorize",
    authorize_params=None,
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)

linkedin = oauth.register(
    name="linkedin",
    client_id=os.getenv("LINKEDIN_CLIENT_ID"),
    client_secret=os.getenv("LINKEDIN_CLIENT_SECRET"),
    access_token_url="https://www.linkedin.com/oauth/v2/accessToken",
    access_token_params=None,
    authorize_url="https://www.linkedin.com/oauth/v2/authorization",
    authorize_params=None,
    api_base_url="https://api.linkedin.com/v2/",
    client_kwargs={"scope": "r_liteprofile r_emailaddress"},
)

# Type variable for decorators
F = TypeVar("F", bound=Callable[..., Any])


def format_runtime(seconds: int) -> str:
    """Format runtime in seconds to HH:MM:SS format."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def login_required(f: F) -> F:
    """Decorator to require login for routes."""

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return cast(F, decorated_function)


def update_bot_status() -> None:
    """Update bot status periodically."""
    while True:
        try:
            if not demo_mode:
                status = bot_service.get_status()
                bot_status.update(status)
            else:
                # Simulate status updates in demo mode
                bot_status["runtime"] = format_runtime(
                    int(
                        (
                            datetime.now() - bot_status.get("start_time", datetime.now())
                        ).total_seconds()
                    )
                )
                bot_status["last_update"] = datetime.now().isoformat()
        except Exception as e:
            logger.error(f"Error updating bot status: {e}")
        time.sleep(5)


def initialize_bot(config_data: Dict[str, Any]) -> TradingBot:
    """Initialize trading bot with configuration."""
    try:
        config = Config(config_data)
        alpaca_service = AlpacaService(config)
        strategy = MovingAverageCrossover(config_data)
        return TradingBot(alpaca_service, strategy)
    except Exception as e:
        logger.error(f"Error initializing bot: {e}")
        raise


def run_bot() -> None:
    """Run the trading bot."""
    try:
        if not demo_mode:
            bot_service.start()
        else:
            bot_status["status"] = "running"
            bot_status["start_time"] = datetime.now()
    except Exception as e:
        logger.error(f"Error running bot: {e}")


@app.route("/login", methods=["GET", "POST"])
def login() -> Union[WerkzeugResponse, str]:
    """Handle login requests."""
    if request.method == "POST":
        username = request.form.get("username")
        if username == os.getenv("ADMIN_USERNAME", "admin@admin.com"):
            session["username"] = username
            return redirect(url_for("index"))

        return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")


@app.route("/login/<provider>")
def oauth_login(provider: str) -> WerkzeugResponse:
    """Handle OAuth login requests."""
    if provider == "google":
        return google.authorize_redirect(redirect_uri=url_for("google_authorize", _external=True))
    elif provider == "github":
        return github.authorize_redirect(redirect_uri=url_for("github_authorize", _external=True))
    elif provider == "linkedin":
        return linkedin.authorize_redirect(
            redirect_uri=url_for("linkedin_authorize", _external=True)
        )
    return redirect(url_for("login"))


@app.route("/authorize/google")
def google_authorize() -> WerkzeugResponse:
    """Handle Google OAuth callback."""
    google.authorize_access_token()
    resp = google.get("userinfo")
    user_info = resp.json()
    session["username"] = user_info["email"]
    return redirect(url_for("index"))


@app.route("/authorize/github")
def github_authorize() -> WerkzeugResponse:
    """Handle GitHub OAuth callback."""
    github.authorize_access_token()
    resp = github.get("user")
    user_info = resp.json()
    session["username"] = user_info["login"]
    return redirect(url_for("index"))


@app.route("/authorize/linkedin")
def linkedin_authorize() -> WerkzeugResponse:
    """Handle LinkedIn OAuth callback."""
    linkedin.authorize_access_token()
    resp = linkedin.get("me")
    user_info = resp.json()
    session["username"] = user_info["id"]
    return redirect(url_for("index"))


@app.route("/logout")
def logout() -> WerkzeugResponse:
    """Handle logout requests."""
    session.pop("username", None)
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index() -> str:
    """Render main page."""
    return render_template("index.html")


@app.route("/status", methods=["GET"])
@login_required
def get_status() -> Dict[str, str]:
    """Get bot status."""
    return {"status": bot_status["status"]}


@app.route("/positions", methods=["GET"])
@login_required
def get_positions() -> Dict[str, List[Dict[str, Union[str, float]]]]:
    """Get current positions."""
    if not demo_mode:
        positions = bot_service.active_positions()
        return {"positions": positions}
    return {"positions": []}


@app.route("/portfolio", methods=["GET"])
@login_required
def get_portfolio() -> Dict[str, Dict[str, float]]:
    """Get portfolio information."""
    if not demo_mode:
        portfolio = bot_service.portfolio()
        return {"portfolio": portfolio}
    return {"portfolio": {"value": 0.0, "cash": 0.0}}


@app.route("/market", methods=["GET"])
@login_required
def get_market_status() -> Dict[str, bool]:
    """Get market status."""
    if not demo_mode:
        is_open = bot_service.market_is_open()
        return {"is_open": is_open}
    return {"is_open": False}


@socketio.on("connect")
def handle_connect() -> None:
    """Handle WebSocket connection."""
    logger.info("Client connected")


@socketio.on("disconnect")
def handle_disconnect() -> None:
    """Handle WebSocket disconnection."""
    logger.info("Client disconnected")


if __name__ == "__main__":
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Start update emitter in a separate thread
    update_thread = threading.Thread(target=update_bot_status)
    update_thread.daemon = True
    update_thread.start()

    # Start web server
    logger.info("Starting web server on http://127.0.0.1:5050")
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    socketio.run(app, host="127.0.0.1", port=5050, debug=debug_mode)
