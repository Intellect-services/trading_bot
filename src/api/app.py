"""REST API for bot control."""

from typing import Any, Dict, Tuple, Union

from flask import Flask, jsonify, request, Response
from flask_cors import CORS

from src.core.bot_service import BotService, BotStatus
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def create_app(bot_service: BotService) -> Flask:
    """Create Flask application.

    Args:
        bot_service: Bot service instance

    Returns:
        Flask application
    """
    app = Flask(__name__)
    CORS(app)

    @app.route("/api/status", methods=["GET"])
    def get_status() -> Response:
        """Get bot status."""
        return jsonify(bot_service.get_status())

    @app.route("/api/start", methods=["POST"])
    def start_bot() -> Response:
        """Start the bot."""
        success = bot_service.start()
        return jsonify({
            "success": success,
            "status": bot_service.status.name,
            "error": bot_service.error_message,
        })

    @app.route("/api/stop", methods=["POST"])
    def stop_bot() -> Response:
        """Stop the bot."""
        success = bot_service.stop()
        return jsonify({
            "success": success,
            "status": bot_service.status.name,
            "error": bot_service.error_message,
        })

    @app.route("/api/config", methods=["GET"])
    def get_config() -> Response:
        """Get bot configuration."""
        return jsonify({
            "symbols": bot_service.symbols,
            "initial_capital": bot_service.initial_capital,
            "strategy": str(bot_service.strategy),
        })

    @app.route("/api/config", methods=["PUT"])
    def update_config() -> Union[Response, Tuple[Response, int]]:
        """Update bot configuration."""
        if bot_service.status != BotStatus.STOPPED:
            return (
                jsonify({
                    "success": False,
                    "error": "Cannot update config while bot is running"
                }),
                400,
            )

        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No configuration provided"
            }), 400

        try:
            if "symbols" in data:
                bot_service.symbols = data["symbols"]
            if "initial_capital" in data:
                bot_service.initial_capital = float(data["initial_capital"])

            return jsonify({
                "success": True,
                "config": {
                    "symbols": bot_service.symbols,
                    "initial_capital": bot_service.initial_capital,
                },
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 400

    return app
