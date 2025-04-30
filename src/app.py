"""Flask application for trading bot."""

import logging
import os
import threading
import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast

from authlib.integrations.flask_client import OAuth
from flask import (Flask, Response, jsonify, redirect, render_template,
                   request, session, url_for)
from flask_socketio import SocketIO, emit
from werkzeug.wrappers.response import Response as WerkzeugResponse

from .core.alpaca_service import AlpacaService
from .core.trading_bot import TradingBot
from .strategies.moving_average import MovingAverageCrossover
from .utils.config import Config
from .utils.logger import setup_logger

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key")
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize configuration
config = Config({})  # Initialize with empty config

# Initialize services
try:
    alpaca_service = AlpacaService(config)
    trading_bot = TradingBot(alpaca_service)
    logger.info("Successfully initialized AlpacaService and TradingBot")
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
                status = trading_bot.get_status()
                bot_status.update(status)
            else:
                # Simulate status updates in demo mode
                bot_status["runtime"] = format_runtime(
                    int(
                        (
                            datetime.now()
                            - bot_status.get("start_time", datetime.now())
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
        strategy = MovingAverageCrossover()
        return TradingBot(alpaca_service, strategy)
    except Exception as e:
        logger.error(f"Error initializing bot: {e}")
        raise


def run_bot() -> None:
    """Run the trading bot."""
    try:
        if not demo_mode:
            trading_bot.start()
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
        password = request.form.get("password")

        if username == os.getenv(
            "ADMIN_USERNAME", "admin@admin.com"
        ) and password == os.getenv("ADMIN_PASSWORD", "admin"):
            session["username"] = username
            return redirect(url_for("index"))

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


@app.route("/login/<provider>")
def oauth_login(provider: str) -> WerkzeugResponse:
    """Handle OAuth login requests."""
    if provider not in ["google", "github", "linkedin"]:
        return redirect(url_for("login"))

    redirect_uri = url_for(f"authorize_{provider}", _external=True)
    return oauth.create_client(provider).authorize_redirect(redirect_uri)


@app.route("/authorize/google")
def google_authorize() -> WerkzeugResponse:
    """Handle Google OAuth authorization."""
    token = oauth.google.authorize_access_token()
    user = oauth.google.get("userinfo").json()
    session["username"] = user["email"]
    return redirect(url_for("index"))


@app.route("/authorize/github")
def github_authorize() -> WerkzeugResponse:
    """Handle GitHub OAuth authorization."""
    token = oauth.github.authorize_access_token()
    user = oauth.github.get("user").json()
    session["username"] = user["email"]
    return redirect(url_for("index"))


@app.route("/authorize/linkedin")
def linkedin_authorize() -> WerkzeugResponse:
    """Handle LinkedIn OAuth authorization."""
    token = oauth.linkedin.authorize_access_token()
    user = oauth.linkedin.get("me").json()
    session["username"] = user["emailAddress"]
    return redirect(url_for("index"))


@app.route("/logout")
def logout() -> WerkzeugResponse:
    """Handle logout requests."""
    session.pop("username", None)
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index() -> str:
    """Render the main page."""
    return render_template("index.html")


@app.route("/api/status")
@login_required
def get_status() -> Response:
    """Get bot status."""
    return jsonify(bot_status)


@app.route("/api/start", methods=["POST"])
@login_required
def start_bot() -> Response:
    """Start the trading bot."""
    try:
        if not demo_mode:
            trading_bot.start()
        else:
            bot_status["status"] = "running"
            bot_status["start_time"] = datetime.now()
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/stop", methods=["POST"])
@login_required
def stop_bot() -> Response:
    """Stop the trading bot."""
    try:
        if not demo_mode:
            trading_bot.stop()
        else:
            bot_status["status"] = "stopped"
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/positions")
@login_required
def get_positions() -> Response:
    """Get current positions."""
    try:
        if not demo_mode:
            positions = trading_bot.get_positions()
        else:
            positions = []
        return jsonify(positions)
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/portfolio-history")
@login_required
def get_portfolio_history() -> Response:
    """Get portfolio history."""
    try:
        if not demo_mode:
            history = trading_bot.get_portfolio_history()
        else:
            history = {
                "timestamp": [datetime.now().isoformat()],
                "equity": [10000.0],
                "profit_loss": [0.0],
                "profit_loss_pct": [0.0],
            }
        return jsonify(history)
    except Exception as e:
        logger.error(f"Error getting portfolio history: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/market-status")
@login_required
def get_market_status() -> Response:
    """Get market status."""
    try:
        if not demo_mode:
            status = trading_bot.get_market_status()
        else:
            status = {
                "is_open": True,
                "next_open": None,
                "next_close": None,
                "timestamp": datetime.now().isoformat(),
            }
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting market status: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


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
