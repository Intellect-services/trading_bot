"""API application for trading bot."""

import logging
import os
from datetime import datetime
from typing import Optional, Tuple

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
config_data = {
    "ALPACA_API_KEY": os.getenv("ALPACA_API_KEY", ""),
    "ALPACA_SECRET_KEY": os.getenv("ALPACA_SECRET_KEY", ""),
    "ALPACA_PAPER": os.getenv("ALPACA_PAPER", "True").lower() == "true",
    "RISK_MAX_POSITION_SIZE": float(os.getenv("RISK_MAX_POSITION_SIZE", "0.1")),
    "RISK_PER_TRADE": float(os.getenv("RISK_PER_TRADE", "0.01")),
    "RISK_STOP_LOSS": float(os.getenv("RISK_STOP_LOSS", "0.02")),
    "RISK_TAKE_PROFIT": float(os.getenv("RISK_TAKE_PROFIT", "0.04")),
}
config = Config(config_data)

# Initialize services
try:
    alpaca_service = AlpacaService(config_data)
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
def get_status() -> Tuple[Response, int]:
    """Get bot status."""
    try:
        status = trading_bot.get_status() if not demo_mode else {"status": "demo"}
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/start", methods=["POST"])
def start_bot() -> Tuple[Response, int]:
    """Start the trading bot."""
    try:
        if not demo_mode:
            trading_bot.start()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/stop", methods=["POST"])
def stop_bot() -> Tuple[Response, int]:
    """Stop the trading bot."""
    try:
        if not demo_mode:
            trading_bot.stop()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/positions", methods=["GET"])
def get_positions() -> Tuple[Response, int]:
    """Get current positions."""
    try:
        if demo_mode:
            return jsonify([]), 200
        positions = alpaca_service.get_positions()
        return jsonify(positions), 200
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/portfolio-history", methods=["GET"])
def get_portfolio_history() -> Tuple[Response, int]:
    """Get portfolio history."""
    try:
        if demo_mode:
            return (
                jsonify(
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
                ),
                200,
            )
        history = alpaca_service.get_portfolio_history(period="30D", timeframe="1D")
        return jsonify(history), 200
    except Exception as e:
        logger.error(f"Error getting portfolio history: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/market-status", methods=["GET"])
def get_market_status() -> Tuple[Response, int]:
    """Get current market status."""
    try:
        if demo_mode:
            market_open = datetime.now().hour >= 9 and datetime.now().hour < 16
            return (
                jsonify(
                    {
                        "is_open": market_open,
                        "next_open": None,
                        "next_close": None,
                    }
                ),
                200,
            )
        status = alpaca_service.get_market_clock()
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Error getting market status: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    # Start web server
    logger.info("Starting API server on http://127.0.0.1:5051")
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="127.0.0.1", port=5051, debug=debug_mode)
