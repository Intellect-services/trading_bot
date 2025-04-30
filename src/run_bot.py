import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, TypedDict, Union, cast

from dotenv import load_dotenv
from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_socketio import SocketIO, emit
from werkzeug.wrappers import Response as WerkzeugResponse

from app import app, socketio
from src.core.alpaca_service import AlpacaService
from src.core.trading_bot import TradingBot
from src.utils.config import Config


class BotMetrics(TypedDict):
    initial_capital: float
    current_capital: float
    total_trades: int
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    active_positions: int


class BotStatus(TypedDict):
    is_running: bool
    market_status: str
    runtime: str
    last_update: Optional[datetime]
    metrics: BotMetrics


# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler("trading_bot.log")],
    )


def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    config = {
        "api_key": os.environ["ALPACA_API_KEY"],
        "api_secret": os.environ["ALPACA_API_SECRET"],
        "base_url": os.environ.get("ALPACA_API_BASE_URL", "https://paper-api.alpaca.markets"),
        "data_feed": os.environ.get("DATA_FEED", "iex"),
    }
    return config


def setup_bot(config: Dict[str, Any]) -> TradingBot:
    """Set up the trading bot with the given configuration."""
    # Initialize components
    alpaca_service = AlpacaService()

    # Create and return the bot
    return TradingBot(alpaca_service)


def run_bot(bot: TradingBot) -> None:
    """Run the trading bot."""
    try:
        bot.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, stopping bot...")
        bot.stop()
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        bot.stop()
        raise


def main() -> None:
    """Main function to run the trading bot."""
    try:
        # Set up logging
        setup_logging()

        # Load configuration
        config = load_config()

        # Set up and run the bot
        bot = setup_bot(config)
        run_bot(bot)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key")
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Alpaca service and trading bot
alpaca_service = AlpacaService()
trading_bot = TradingBot(alpaca_service)

# Global state
bot_status: BotStatus = {
    "is_running": False,
    "market_status": "unknown",
    "runtime": "00:00:00",
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


def update_bot_status() -> None:
    """Update bot status and emit updates to connected clients"""
    while True:
        try:
            # Get market status
            market_status = alpaca_service.get_market_status()
            bot_status["market_status"] = cast(str, market_status["status"])

            # Get account info
            account = alpaca_service.get_account()
            if account:
                metrics = cast(BotMetrics, bot_status["metrics"])
                metrics["current_capital"] = float(account.get("equity", 0))
                if not metrics["initial_capital"]:
                    metrics["initial_capital"] = float(account.get("equity", 0))

            # Get positions
            positions = alpaca_service.get_positions()
            bot_status["metrics"]["active_positions"] = len(positions) if positions else 0

            # Update runtime if bot is running
            if bot_status["is_running"]:
                if bot_status["last_update"]:
                    runtime = datetime.now() - cast(datetime, bot_status["last_update"])
                    bot_status["runtime"] = str(runtime).split(".")[0]
                else:
                    bot_status["last_update"] = datetime.now()

            # Emit update to all connected clients
            socketio.emit("bot_update", bot_status)

        except Exception as e:
            logger.error(f"Error updating bot status: {str(e)}")
            socketio.emit(
                "bot_update",
                {
                    "error": str(e),
                    "is_running": bot_status["is_running"],
                    "runtime": bot_status["runtime"],
                },
            )

        socketio.sleep(5)  # Update every 5 seconds


# Start status update thread
socketio.start_background_task(update_bot_status)


@app.route("/")
def index() -> WerkzeugResponse:
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login() -> Union[WerkzeugResponse, str]:
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == os.getenv("ADMIN_USERNAME", "admin@admin.com") and password == os.getenv(
            "ADMIN_PASSWORD", "admin"
        ):
            session["username"] = username
            return redirect(url_for("index"))

        return render_template("index.html", error="Invalid credentials")

    return render_template("index.html")


@app.route("/logout")
def logout() -> WerkzeugResponse:
    session.pop("username", None)
    return redirect(url_for("login"))


@app.route("/api/status", methods=["GET"])
def get_status() -> Union[WerkzeugResponse, Tuple[WerkzeugResponse, int]]:
    """Get the current status of the trading bot."""
    try:
        bot = app.config.get("bot")
        if not bot:
            return jsonify({"error": "Bot not initialized"}), 500

        status = bot.get_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/start", methods=["POST"])
def start_bot() -> Union[WerkzeugResponse, Tuple[WerkzeugResponse, int]]:
    """Start the trading bot."""
    try:
        bot = app.config.get("bot")
        if not bot:
            return jsonify({"error": "Bot not initialized"}), 500

        bot.start()
        return jsonify({"message": "Bot started successfully"})
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/stop", methods=["POST"])
def stop_bot() -> Union[WerkzeugResponse, Tuple[WerkzeugResponse, int]]:
    """Stop the trading bot."""
    try:
        bot = app.config.get("bot")
        if not bot:
            return jsonify({"error": "Bot not initialized"}), 500

        bot.stop()
        return jsonify({"message": "Bot stopped successfully"})
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/config", methods=["GET"])
def get_config() -> Union[WerkzeugResponse, Tuple[WerkzeugResponse, int]]:
    """Get the current configuration of the trading bot."""
    try:
        bot = app.config.get("bot")
        if not bot:
            return jsonify({"error": "Bot not initialized"}), 500

        config = bot.get_config()
        return jsonify(config)
    except Exception as e:
        logger.error(f"Error getting bot configuration: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/config", methods=["PUT"])
def update_config() -> Union[WerkzeugResponse, Tuple[WerkzeugResponse, int]]:
    """Update the configuration of the trading bot."""
    try:
        bot = app.config.get("bot")
        if not bot:
            return jsonify({"error": "Bot not initialized"}), 500

        new_config = request.get_json()
        if not new_config:
            return jsonify({"error": "No configuration data provided"}), 400

        bot.update_config(new_config)
        return jsonify({"message": "Configuration updated successfully"})
    except Exception as e:
        logger.error(f"Error updating bot configuration: {e}")
        return jsonify({"error": str(e)}), 500


@socketio.on("connect")
def handle_connect() -> None:
    """Handle WebSocket connection."""
    if hasattr(request, "sid"):
        logger.info(f"Client connected: {request.sid}")
    else:
        logger.info("Client connected (no session ID available)")


@socketio.on("disconnect")
def handle_disconnect() -> None:
    """Handle WebSocket disconnection."""
    if hasattr(request, "sid"):
        logger.info(f"Client disconnected: {request.sid}")
    else:
        logger.info("Client disconnected (no session ID available)")


if __name__ == "__main__":
    main()
