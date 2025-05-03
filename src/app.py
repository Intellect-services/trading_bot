# … earlier imports unchanged …
import logging
import os
import secrets
from typing import TYPE_CHECKING, Optional, Union

from authlib.integrations.flask_client import OAuth
from flask import (
    Flask,
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_socketio import SocketIO
from werkzeug.wrappers.response import Response as WerkzeugResponse

from flask_session import Session
from src import Config
from src.core.bot import TradingBot
from src.core.strategy import Strategy
from src.strategies.moving_average import MovingAverageCrossover

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static")
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(32))

# Configure session
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "flask_session"
)
app.config["SESSION_FILE_THRESHOLD"] = 100
app.config["PERMANENT_SESSION_LIFETIME"] = 3600  # 1 hour
Session(app)

socketio = SocketIO(app)
oauth = OAuth(app)

# Initialize configuration
config = Config(
    {
        "ALPACA_API_KEY": os.getenv("ALPACA_API_KEY", ""),
        "ALPACA_SECRET_KEY": os.getenv("ALPACA_SECRET_KEY", ""),
        "ALPACA_PAPER": os.getenv("ALPACA_PAPER", "True").lower() == "true",
        "INITIAL_CAPITAL": float(os.getenv("INITIAL_CAPITAL", "100000")),
        "RISK_MAX_POSITION_SIZE": float(os.getenv("RISK_MAX_POSITION_SIZE", "0.1")),
        "RISK_PER_TRADE": float(os.getenv("RISK_PER_TRADE", "0.01")),
        "RISK_STOP_LOSS_PCT": float(os.getenv("RISK_STOP_LOSS_PCT", "0.02")),
        "RISK_TAKE_PROFIT_PCT": float(os.getenv("RISK_TAKE_PROFIT_PCT", "0.04")),
    }
)

# OAuth configurations
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

# initialize trading_bot under mypy stub
app.trading_bot = None  # type: ignore[attr-defined]


@app.route("/", methods=["GET"])
def index() -> Union[Response, WerkzeugResponse, str]:
    """Render the main trading dashboard."""
    try:
        if not session.get("user"):
            app.logger.debug("No user in session, redirecting to login")
            return redirect(url_for("login"))

        app.logger.debug(f"User in session: {session.get('user')}")
        return render_template("index.html")
    except Exception as e:
        app.logger.error(f"Index route error: {e}")
        flash("An error occurred. Please try again.", "danger")
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login() -> Union[Response, WerkzeugResponse, str]:
    """Handle login page and authentication."""
    if request.method == "POST":
        try:
            email = request.form.get("email")
            password = request.form.get("password")

            app.logger.debug(f"Login attempt for email: {email}")

            # For demo purposes, accept admin@admin.com/admin
            if email == "admin@admin.com" and password == "admin":
                user_data = {"name": "Admin User", "email": email, "id": "admin"}
                session["user"] = user_data
                app.logger.debug(f"Login successful for user: {user_data}")
                flash("Successfully logged in!", "success")
                return redirect(url_for("index"))

            app.logger.debug("Invalid credentials")
            flash("Invalid email or password", "danger")
            return redirect(url_for("login"))
        except Exception as e:
            app.logger.error(f"Login error: {e}")
            flash("An error occurred during login. Please try again.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/auth/<provider>", methods=["GET"])
def auth(provider: str) -> Union[Response, WerkzeugResponse]:
    """Handle OAuth authentication."""
    if provider not in ["google", "github", "linkedin"]:
        flash("Invalid authentication provider", "danger")
        return redirect(url_for("login"))

    client = oauth.create_client(provider)
    if not client:
        flash("Authentication provider not configured", "danger")
        return redirect(url_for("login"))

    redirect_uri = url_for("auth_callback", provider=provider, _external=True)
    return redirect(client.authorize_redirect(redirect_uri))


@app.route("/auth/<provider>/callback", methods=["GET"])
def auth_callback(provider: str) -> Union[Response, WerkzeugResponse]:
    """Handle OAuth callback."""
    if provider not in ["google", "github", "linkedin"]:
        flash("Invalid authentication provider", "danger")
        return redirect(url_for("login"))

    client = oauth.create_client(provider)
    if not client:
        flash("Authentication provider not configured", "danger")
        return redirect(url_for("login"))

    try:
        token = client.authorize_access_token()
        user_info = client.get("userinfo").json()
        session["user"] = user_info
        flash("Successfully logged in!", "success")
        return redirect(url_for("index"))
    except Exception as e:
        app.logger.error(f"OAuth error: {str(e)}")
        flash("Authentication failed. Please try again.", "danger")
        return redirect(url_for("login"))


@app.route("/logout", methods=["GET"])
def logout() -> Union[Response, WerkzeugResponse]:
    """Handle user logout."""
    try:
        session.pop("user", None)
        flash("Successfully logged out!", "success")
        return redirect(url_for("index"))
    except Exception as e:
        app.logger.error(f"Logout error: {str(e)}")
        flash("An error occurred during logout.", "danger")
        return redirect(url_for("index"))


@app.route("/api/start", methods=["POST"])
def start_bot() -> Union[Response, WerkzeugResponse]:
    """Start the trading bot."""
    try:
        if app.trading_bot is None:
            strategy = MovingAverageCrossover(config)
            app.trading_bot = TradingBot(config=config, strategy=strategy)

        app.trading_bot.start()
        response = jsonify({"status": "success"})
        response.status_code = 200
        return response
    except Exception as e:
        app.logger.error(f"Error starting bot: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.status_code = 500
        return response


@app.route("/api/stop", methods=["POST"])
def stop_bot() -> Union[Response, WerkzeugResponse]:
    """Stop the trading bot."""
    try:
        if app.trading_bot is not None:
            app.trading_bot.stop()
        response = jsonify({"status": "success"})
        response.status_code = 200
        return response
    except Exception as e:
        app.logger.error(f"Error stopping bot: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.status_code = 500
        return response


@app.route("/api/status", methods=["GET"])
def get_status() -> Union[Response, WerkzeugResponse]:
    """Get bot status."""
    try:
        if app.trading_bot is not None:
            status = app.trading_bot.get_status()
        else:
            status = {"status": "stopped"}
        response = jsonify(status)
        response.status_code = 200
        return response
    except Exception as e:
        app.logger.error(f"Error getting status: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.status_code = 500
        return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
