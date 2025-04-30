import logging
import os
import threading
import time
from datetime import datetime
from functools import wraps

from authlib.integrations.flask_client import OAuth
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_socketio import SocketIO, emit

from .core.alpaca_service import AlpacaService
from .core.trading_bot import TradingBot
from .utils.logger import setup_logger

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key")
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize services
try:
    alpaca_service = AlpacaService()
    trading_bot = TradingBot(alpaca_service)
    logger.info("Successfully initialized AlpacaService and TradingBot")
except Exception as e:
    logger.error(f"Failed to initialize services: {e}")
    raise

# Global state
bot_status = {
    "status": "stopped",
    "market_status": "closed",
    "runtime": 0,
    "last_update": None,
    "error": None,
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


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def update_bot_status():
    """Update bot status and emit updates to connected clients."""
    while True:
        try:
            # Get market status
            market_status = alpaca_service.get_market_status()
            is_market_open = market_status.get("is_open", False)

            # Get account information
            account = alpaca_service.get_account()

            # Get positions
            positions = alpaca_service.get_positions()

            # Get portfolio history for the last 30 days
            portfolio_history = alpaca_service.get_portfolio_history(period="30D", timeframe="1D")

            # Update bot status
            bot_status.update(
                {
                    "status": "RUNNING" if trading_bot.is_running else "STOPPED",
                    "market_status": "open" if is_market_open else "closed",
                    "runtime": trading_bot.get_runtime(),
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
                        "daytrading_buying_power": float(account.get("daytrading_buying_power", 0)),
                        "non_marginable_buying_power": float(
                            account.get("non_marginable_buying_power", 0)
                        ),
                        "maintenance_margin": float(account.get("maintenance_margin", 0)),
                        "last_equity": float(account.get("last_equity", 0)),
                        "last_maintenance_margin": float(account.get("last_maintenance_margin", 0)),
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

            # Emit update to all connected clients
            socketio.emit("status_update", bot_status)

        except Exception as e:
            logger.error(f"Error updating bot status: {str(e)}")
            bot_status["status"] = "ERROR"
            bot_status["error"] = str(e)
            socketio.emit("status_update", bot_status)

        time.sleep(5)  # Update every 5 seconds


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
    token = google.authorize_access_token()
    resp = google.get("userinfo")
    user_info = resp.json()
    session["username"] = user_info["email"]
    return redirect(url_for("index"))


@app.route("/authorize/github")
def github_authorize():
    token = github.authorize_access_token()
    resp = github.get("user")
    user_info = resp.json()
    session["username"] = user_info["email"]
    return redirect(url_for("index"))


@app.route("/authorize/linkedin")
def linkedin_authorize():
    token = linkedin.authorize_access_token()
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
    return render_template("index.html")


@app.route("/api/status")
@login_required
def get_status():
    try:
        # Get current account info
        account_info = alpaca_service.get_account()
        if account_info:
            logger.debug(f"Current account info: {account_info}")
            return jsonify(
                {
                    "success": True,
                    "status": bot_status["status"],
                    "market_status": bot_status["market_status"],
                    "runtime": bot_status["runtime"],
                    "last_update": bot_status["last_update"],
                    "error": bot_status["error"],
                    "account": {
                        "account_id": account_info.get("id"),
                        "buying_power": float(account_info.get("buying_power", 0)),
                        "equity": float(account_info.get("equity", 0)),
                        "cash": float(account_info.get("cash", 0)),
                        "status": account_info.get("status"),
                        "daytrade_count": account_info.get("daytrade_count", 0),
                        "trading_blocked": account_info.get("trading_blocked", False),
                        "transfers_blocked": account_info.get("transfers_blocked", False),
                        "account_blocked": account_info.get("account_blocked", False),
                        "shorting_enabled": account_info.get("shorting_enabled", False),
                        "multiplier": account_info.get("multiplier", 1),
                        "regt_buying_power": float(account_info.get("regt_buying_power", 0)),
                        "daytrading_buying_power": float(
                            account_info.get("daytrading_buying_power", 0)
                        ),
                        "non_marginable_buying_power": float(
                            account_info.get("non_marginable_buying_power", 0)
                        ),
                        "maintenance_margin": float(account_info.get("maintenance_margin", 0)),
                        "last_equity": float(account_info.get("last_equity", 0)),
                        "last_maintenance_margin": float(
                            account_info.get("last_maintenance_margin", 0)
                        ),
                    },
                    "metrics": {
                        "initial_capital": float(account_info.get("equity", 0)),
                        "current_capital": float(account_info.get("equity", 0)),
                        "active_positions": len(alpaca_service.get_positions()),
                        "total_trades": trading_bot.get_total_trades(),
                        "win_rate": trading_bot.get_win_rate(),
                        "avg_return": trading_bot.get_average_return(),
                        "daily_pnl": float(account_info.get("equity", 0))
                        - float(account_info.get("last_equity", 0)),
                        "unrealized_pl": sum(
                            float(pos.get("unrealized_pl", 0))
                            for pos in alpaca_service.get_positions()
                        ),
                        "realized_pl": float(account_info.get("equity", 0))
                        - float(account_info.get("last_equity", 0))
                        - sum(
                            float(pos.get("unrealized_pl", 0))
                            for pos in alpaca_service.get_positions()
                        ),
                    },
                }
            )
        return jsonify({"success": False, "error": "Failed to get account information"})
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/start", methods=["POST"])
def start_bot():
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        if bot_status["status"] == "stopped":
            # Get detailed market status
            market_status = alpaca_service.get_market_status()
            if not market_status.get("is_open", False):
                next_open = market_status.get("next_open")
                next_close = market_status.get("next_close")
                return (
                    jsonify(
                        {
                            "error": "Market is closed",
                            "market_status": {
                                "is_open": False,
                                "next_open": next_open,
                                "next_close": next_close,
                            },
                        }
                    ),
                    400,
                )

            bot_status["status"] = "running"
            bot_status["runtime"] = 0
            bot_status["last_update"] = datetime.now().isoformat()
            bot_status["error"] = None
            trading_bot.start()
            logger.info("Bot started successfully")
            return jsonify({"success": True})
        return jsonify({"error": "Bot already running"}), 400
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        bot_status["error"] = str(e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/stop", methods=["POST"])
def stop_bot():
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        if bot_status["status"] == "running":
            bot_status["status"] = "stopped"
            bot_status["last_update"] = datetime.now().isoformat()
            bot_status["error"] = None
            trading_bot.stop()
            logger.info("Bot stopped successfully")
            return jsonify({"success": True})
        return jsonify({"error": "Bot not running"}), 400
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        bot_status["error"] = str(e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/positions")
def get_positions():
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        positions = alpaca_service.get_positions()
        return jsonify({"success": True, "positions": positions})
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/portfolio-history")
def get_portfolio_history():
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        history = alpaca_service.get_portfolio_history(period="30D", timeframe="1D")
        return jsonify({"success": True, "history": history})
    except Exception as e:
        logger.error(f"Error getting portfolio history: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/market-status")
def get_market_status():
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        market_status = alpaca_service.get_market_status()
        # Format dates to ISO string if they exist
        if market_status.get("next_open"):
            market_status["next_open"] = market_status["next_open"].isoformat()
        if market_status.get("next_close"):
            market_status["next_close"] = market_status["next_close"].isoformat()

        return jsonify({"success": True, "market_status": market_status})
    except Exception as e:
        logger.error(f"Error getting market status: {e}")
        return jsonify({"success": False, "error": str(e)})


@socketio.on("connect")
def handle_connect():
    if "username" in session:
        logger.info(f"Client connected: {request.sid}")
        try:
            # Send initial status
            emit("status_update", bot_status)

            # Send initial account info
            account_info = alpaca_service.get_account()
            if account_info:
                logger.debug(f"Sending initial account info: {account_info}")
                emit("alpaca_account_update", account_info)

            # Send initial positions
            positions = alpaca_service.get_positions()
            if positions:
                logger.debug(f"Sending initial positions: {positions}")
                emit("positions_update", positions)

            # Send initial metrics
            metrics = trading_bot.get_metrics()
            if metrics:
                logger.debug(f"Sending initial metrics: {metrics}")
                emit("metrics_update", metrics)
        except Exception as e:
            logger.error(f"Error sending initial data to client: {e}")


@socketio.on("disconnect")
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")


if __name__ == "__main__":
    # Get configuration from environment variables
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    host = os.getenv("FLASK_HOST", "127.0.0.1")  # Default to localhost
    port = int(os.getenv("FLASK_PORT", "5001"))

    # Start the status update thread
    status_thread = threading.Thread(target=update_bot_status)
    status_thread.daemon = True
    status_thread.start()

    # Start the Flask application with secure defaults
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug_mode,
        allow_unsafe_werkzeug=False,  # Disable Werkzeug debugger in production
    )
