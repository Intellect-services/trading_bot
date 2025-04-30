"""REST API for bot control."""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple, Union
import time

from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from werkzeug.wrappers.response import Response as WerkzeugResponse

from src.core.alpaca_service import AlpacaService
from src.core.bot_service import BotService, BotStatus
from src.core.trading_bot import TradingBot
from src.utils.config import Config
from src.utils.logger import setup_logger
from types import BotMetrics, BotStatusDict

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key")
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Alpaca service and trading bot
alpaca_service = AlpacaService()
trading_bot = TradingBot(alpaca_service)

# Initialize bot status
bot_status: BotStatusDict = {
    "is_running": False,
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


def update_bot_status() -> None:
    """Update bot status periodically."""
    while True:
        try:
            # Get market status
            status = trading_bot.get_status()
            bot_status["market_status"] = status["status"]
            bot_status["metrics"]["current_capital"] = status["current_capital"]
            bot_status["metrics"]["active_positions"] = status["active_positions"]

            # Update runtime if bot is running
            if bot_status["is_running"]:
                last_update = bot_status["last_update"]
                if last_update:
                    runtime = datetime.now() - last_update
                    bot_status["runtime"] = str(runtime).split(".")[0]
                else:
                    bot_status["last_update"] = datetime.now()

            # Emit update to all connected clients
            socketio.emit("bot_update", bot_status)

        except Exception as e:
            logger.error(f"Error updating bot status: {e}")
            socketio.emit("error", {"message": str(e)})
        time.sleep(5)


# Start status update thread
socketio.start_background_task(update_bot_status)


def create_app(bot_service: BotService) -> Flask:
    """Create Flask application.

    Args:
        bot_service: Bot service instance

    Returns:
        Flask application
    """
    CORS(app)

    @app.route("/api/status", methods=["GET"])
    def get_status() -> Union[Response, Tuple[Response, int]]:
        """Get current bot status."""
        try:
            return jsonify(bot_status)
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/start", methods=["POST"])
    def start_bot() -> Union[Response, Tuple[Response, int]]:
        """Start the trading bot."""
        try:
            if bot_service.start():
                bot_status["is_running"] = True
                bot_status["last_update"] = datetime.now()
                return jsonify({"status": "success"})
            return jsonify({"error": "Failed to start bot"}), 500
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/stop", methods=["POST"])
    def stop_bot() -> Union[Response, Tuple[Response, int]]:
        """Stop the trading bot."""
        try:
            if bot_service.stop():
                bot_status["is_running"] = False
                return jsonify({"status": "success"})
            return jsonify({"error": "Failed to stop bot"}), 500
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/config", methods=["GET"])
    def get_config() -> Union[Response, Tuple[Response, int]]:
        """Get current bot configuration."""
        try:
            return jsonify(bot_service.config.get_all())
        except Exception as e:
            logger.error(f"Error getting config: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/config", methods=["PUT"])
    def update_config() -> Union[Response, Tuple[Response, int]]:
        """Update bot configuration."""
        try:
            config_data = request.get_json()
            if not config_data:
                return jsonify({"error": "No configuration data provided"}), 400
            bot_service.config.update(config_data)
            return jsonify({"status": "success"})
        except Exception as e:
            logger.error(f"Error updating config: {e}")
            return jsonify({"error": str(e)}), 500

    @socketio.on("connect")
    def handle_connect() -> None:
        """Handle WebSocket connection."""
        emit("bot_update", bot_status)

    @socketio.on("disconnect")
    def handle_disconnect() -> None:
        """Handle WebSocket disconnection."""
        pass

    return app
