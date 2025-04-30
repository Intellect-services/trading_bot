"""REST API for bot control."""

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, Union

from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO

from src.core.alpaca_service import AlpacaService
from src.core.bot_service import BotService, BotStatus
from src.core.trading_bot import TradingBot
from src.utils.config import Config
from src.utils.logger import setup_logger

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key")
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Alpaca service and trading bot
alpaca_service = AlpacaService()
trading_bot = TradingBot(alpaca_service)

# Global state
bot_status = {
    "is_running": False,
    "market_status": "unknown",
    "runtime": "00:00:00",
    "last_update": None,
    "metrics": {
        "initial_capital": 0,
        "current_capital": 0,
        "total_trades": 0,
        "win_rate": 0,
        "profit_factor": 0,
        "sharpe_ratio": 0,
        "active_positions": 0,
    },
}


def update_bot_status() -> None:
    """Update bot status and emit updates to connected clients"""
    while True:
        try:
            # Get market status
            market_status = alpaca_service.get_market_status()
            bot_status["market_status"] = market_status["status"]

            # Get account info
            account = alpaca_service.get_account()
            if account:
                bot_status["metrics"]["current_capital"] = float(account.get("equity", 0))
                if not bot_status["metrics"]["initial_capital"]:
                    bot_status["metrics"]["initial_capital"] = float(account.get("equity", 0))

            # Get positions
            positions = alpaca_service.get_positions()
            bot_status["metrics"]["active_positions"] = len(positions) if positions else 0

            # Update runtime if bot is running
            if bot_status["is_running"]:
                if bot_status["last_update"]:
                    runtime = datetime.now() - bot_status["last_update"]
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
    def start_bot() -> Union[Response, Tuple[Response, int]]:
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
    def stop_bot() -> Union[Response, Tuple[Response, int]]:
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
    def get_config() -> Union[Response, Tuple[Response, int]]:
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
    def update_config() -> Union[Response, Tuple[Response, int]]:
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

    return app
