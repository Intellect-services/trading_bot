import logging
import os
import threading
import time
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, Optional, Union

from authlib.integrations.flask_client import OAuth  # type: ignore
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_socketio import SocketIO, emit  # type: ignore

from .core.alpaca_client import AlpacaClient
from .core.alpaca_service import AlpacaService
from .core.data_feed import DataFeed
from .core.portfolio import Portfolio
from .core.risk_manager import RiskManager
from .core.trading_bot import TradingBot
from .strategies.moving_average import MovingAverageCrossover
from .utils.config import Config
from .utils.logger import setup_logger

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key")
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize configuration
config = Config({})  # Initialize with empty config

# Initialize services
try:
    alpaca_service = AlpacaService()
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
bot_status = {
    "status": "stopped",
    "market_status": "closed",
    "runtime": 0,
    "last_update": None,
    "error": None,
    "demo_mode": demo_mode,
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


def format_runtime(seconds: int) -> str:
    """Format runtime in HH:MM:SS"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def update_bot_status():
    """Update bot status and emit updates to connected clients."""
    start_time = time.time()

    while True:
        try:
            # Calculate runtime
            runtime = int(time.time() - start_time)

            if not demo_mode:
                # Get market status
                market_status = alpaca_service.get_market_status()
                is_market_open = market_status.get("is_open", False)

                # Get account information
                account = alpaca_service.get_account()

                # Get positions
                positions = alpaca_service.get_positions()

                # Get portfolio history for the last 30 days
                portfolio_history = alpaca_service.get_portfolio_history(
                    period="30D", timeframe="1D"
                )

                # Update bot status
                bot_status.update(
                    {
                        "status": "RUNNING" if trading_bot.is_running else "STOPPED",
                        "market_status": "open" if is_market_open else "closed",
                        "runtime": format_runtime(runtime),
                        "account": {
                            "account_id": account.get("id"),
                            "buying_power": float(account.get("buying_power", 0)),
                            "equity": float(account.get("equity", 0)),
                            "cash": float(account.get("cash", 0)),
                            "status": account.get("status"),
                            "daytrade_count": account.get("daytrade_count", 0),
                            "trading_blocked": account.get("trading_blocked", False),
                            "transfers_blocked": account.get("transfers_blocked", False),
                            "account_blocked": account.get("account_blocked", False),
                            "shorting_enabled": account.get("shorting_enabled", False),
                            "multiplier": account.get("multiplier", 1),
                            "regt_buying_power": float(account.get("regt_buying_power", 0)),
                            "daytrading_buying_power": float(
                                account.get("daytrading_buying_power", 0)
                            ),
                            "non_marginable_buying_power": float(
                                account.get("non_marginable_buying_power", 0)
                            ),
                            "maintenance_margin": float(account.get("maintenance_margin", 0)),
                            "last_equity": float(account.get("last_equity", 0)),
                            "last_maintenance_margin": float(
                                account.get("last_maintenance_margin", 0)
                            ),
                        },
                        "positions": positions,
                        "portfolio_history": portfolio_history,
                        "metrics": {
                            "initial_capital": float(account.get("equity", 0)),
                            "current_capital": float(account.get("equity", 0)),
                            "active_positions": len(positions),
                            "total_trades": trading_bot.get_total_trades(),
                            "win_rate": trading_bot.get_win_rate(),
                            "avg_return": trading_bot.get_average_return(),
                            "daily_pnl": float(account.get("equity", 0))
                            - float(account.get("last_equity", 0)),
                            "unrealized_pl": sum(
                                float(pos.get("unrealized_pl", 0)) for pos in positions
                            ),
                            "realized_pl": float(account.get("equity", 0))
                            - float(account.get("last_equity", 0))
                            - sum(float(pos.get("unrealized_pl", 0)) for pos in positions),
                        },
                    }
                )
            else:
                # Demo mode with mock data
                market_open = datetime.now().hour >= 9 and datetime.now().hour < 16
                positions = {}  # No positions in demo mode
                account_info = {
                    "equity": config.get("initial_balance", 10000.0),
                    "cash": config.get("initial_balance", 10000.0),
                    "buying_power": config.get("initial_balance", 10000.0) * 2,
                }

                bot_status.update(
                    {
                        "status": "DEMO",
                        "market_status": "open" if market_open else "closed",
                        "runtime": format_runtime(runtime),
                        "account": account_info,
                        "positions": positions,
                        "portfolio_history": {
                            "equity": [account_info["equity"], account_info["equity"]],
                            "timestamp": [
                                datetime.now().isoformat(),
                                datetime.now().isoformat(),
                            ],
                            "profit_loss": [0, 0],
                            "profit_loss_pct": [0, 0],
                            "base_value": account_info["equity"],
                        },
                        "metrics": {
                            "initial_capital": account_info["equity"],
                            "current_capital": account_info["equity"],
                            "active_positions": 0,
                            "total_trades": 0,
                            "win_rate": 0,
                            "avg_return": 0,
                            "daily_pnl": 0,
                            "unrealized_pl": 0,
                            "realized_pl": 0,
                        },
                    }
                )

            # Emit update to all connected clients
            socketio.emit("status_update", bot_status)

        except Exception as e:
            logger.error(f"Error updating bot status: {str(e)}")
            bot_status["status"] = "ERROR"
            bot_status["error"] = str(e)
            socketio.emit("status_update", bot_status)

        time.sleep(5)  # Update every 5 seconds


def initialize_bot(config_data: Dict[str, Any]) -> TradingBot:
    """Initialize the trading bot with configuration.

    Args:
        config_data: Configuration data dictionary

    Returns:
        Initialized trading bot instance
    """
    try:
        # Set environment variables for Alpaca API
        os.environ["ALPACA_API_KEY"] = config_data.get("ALPACA_API_KEY", "")
        os.environ["ALPACA_API_SECRET"] = config_data.get("ALPACA_SECRET_KEY", "")

        # Initialize services
        alpaca_service = AlpacaService()
        bot = TradingBot(alpaca_service)
        return bot
    except Exception as e:
        logger.error(f"Error initializing bot: {e}")
        raise


def run_bot():
    """Start the trading bot"""
    if not demo_mode and trading_bot:
        try:
            trading_bot.start()
            logger.info("Bot started successfully")
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
    else:
        logger.info("Bot not initialized. Running in demo mode.")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        # Add your authentication logic here
        if email and password:  # Replace with actual authentication
            session["username"] = email
            return redirect(url_for("index"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")


@app.route("/login/<provider>")
def oauth_login(provider):
    if provider == "google":
        return google.authorize_redirect(url_for("google_authorize", _external=True))
    elif provider == "github":
        return github.authorize_redirect(url_for("github_authorize", _external=True))
    elif provider == "linkedin":
        return linkedin.authorize_redirect(url_for("linkedin_authorize", _external=True))
    return redirect(url_for("login"))


@app.route("/authorize/google")
def google_authorize():
    google.authorize_access_token()
    resp = google.get("userinfo")
    user_info = resp.json()
    session["username"] = user_info["email"]
    return redirect(url_for("index"))


@app.route("/authorize/github")
def github_authorize():
    github.authorize_access_token()
    resp = github.get("user")
    user_info = resp.json()
    session["username"] = user_info["email"]
    return redirect(url_for("index"))


@app.route("/authorize/linkedin")
def linkedin_authorize():
    linkedin.authorize_access_token()
    resp = linkedin.get("me")
    user_info = resp.json()
    session["username"] = user_info["emailAddress"]
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    """Render the dashboard"""
    return render_template(
        "index.html",
        default_symbol=config.get("DEFAULT_SYMBOL", "AAPL"),
        demo_mode=demo_mode,
    )


@app.route("/api/status")
@login_required
def get_status():
    """Get current bot status"""
    return jsonify(bot_status)


@app.route("/api/start", methods=["POST"])
@login_required
def start_bot():
    """Start the trading bot"""
    if demo_mode:
        return jsonify({"status": "error", "message": "Cannot start bot in demo mode"})

    try:
        run_bot()
        return jsonify({"status": "success", "message": "Bot started successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/api/stop", methods=["POST"])
@login_required
def stop_bot():
    """Stop the trading bot"""
    if demo_mode:
        return jsonify({"status": "error", "message": "Cannot stop bot in demo mode"})

    try:
        trading_bot.stop()
        return jsonify({"status": "success", "message": "Bot stopped successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/api/positions")
@login_required
def get_positions():
    """Get current positions"""
    if demo_mode:
        return jsonify([])

    try:
        positions = alpaca_service.get_positions()
        return jsonify(positions)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/api/portfolio-history")
@login_required
def get_portfolio_history():
    """Get portfolio history"""
    if demo_mode:
        return jsonify(
            {
                "equity": [10000.0, 10000.0],
                "timestamp": [datetime.now().isoformat(), datetime.now().isoformat()],
                "profit_loss": [0, 0],
                "profit_loss_pct": [0, 0],
                "base_value": 10000.0,
            }
        )

    try:
        history = alpaca_service.get_portfolio_history(period="30D", timeframe="1D")
        return jsonify(history)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/api/market-status")
@login_required
def get_market_status():
    """Get current market status"""
    if demo_mode:
        market_open = datetime.now().hour >= 9 and datetime.now().hour < 16
        return jsonify(
            {
                "is_open": market_open,
                "next_open": None,
                "next_close": None,
            }
        )

    try:
        status = alpaca_service.get_market_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@socketio.on("connect")
def handle_connect():
    """Handle WebSocket connection"""
    logger.info("Client connected")
    emit("status_update", bot_status)


@socketio.on("disconnect")
def handle_disconnect():
    """Handle WebSocket disconnection"""
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
