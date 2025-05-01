"""API application for trading bot."""

import logging
import os
from datetime import datetime
from typing import Optional

from flask import Flask, Response, jsonify
from flask_cors import CORS

from ..core.alpaca_service import AlpacaService
from ..core.trading_bot import TradingBot
from ..utils.config import Config
from ..utils.logger import setup_logger

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = setup_logger(__name__)

app = Flask(__name__)
CORS(app)

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


@app.route("/api/status", methods=["GET"])
def get_status() -> Response:
    """Get bot status."""
    try:
        status = trading_bot.get_status() if not demo_mode else {"status": "demo"}
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/start", methods=["POST"])
def start_bot() -> Response:
    """Start the trading bot."""
    try:
        if not demo_mode:
            trading_bot.start()
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/stop", methods=["POST"])
def stop_bot() -> Response:
    """Stop the trading bot."""
    try:
        if not demo_mode:
            trading_bot.stop()
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/positions", methods=["GET"])
def get_positions() -> Response:
    """Get current positions."""
    try:
        if demo_mode:
            return jsonify([])
        positions = alpaca_service.get_positions()
        return jsonify(positions)
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/portfolio-history", methods=["GET"])
def get_portfolio_history() -> Response:
    """Get portfolio history."""
    try:
        if demo_mode:
            return jsonify(
                {
                    "equity": [10000.0, 10000.0],
                    "timestamp": [
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                    ],
                    "profit_loss": [0, 0],
                    "profit_loss_pct": [0, 0],
                    "base_value": 10000.0,
                }
            )
        history = alpaca_service.get_portfolio_history(period="30D", timeframe="1D")
        return jsonify(history)
    except Exception as e:
        logger.error(f"Error getting portfolio history: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/market-status", methods=["GET"])
def get_market_status() -> Response:
    """Get current market status."""
    try:
        if demo_mode:
            market_open = datetime.now().hour >= 9 and datetime.now().hour < 16
            return jsonify(
                {
                    "is_open": market_open,
                    "next_open": None,
                    "next_close": None,
                }
            )
        status = alpaca_service.get_market_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting market status: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    # Start web server
    logger.info("Starting API server on http://127.0.0.1:5051")
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="127.0.0.1", port=5051, debug=debug_mode)
