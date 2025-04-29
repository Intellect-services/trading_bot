"""REST API for bot control."""

from flask import Flask, jsonify, request
from flask_cors import CORS
from typing import Dict, Any

from src.core.bot_service import BotService, BotStatus
from src.core.strategy import Strategy
from src.utils.config import get_config
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
    
    @app.route('/api/status', methods=['GET'])
    def get_status() -> Dict[str, Any]:
        """Get bot status.
        
        Returns:
            JSON response with bot status
        """
        return jsonify(bot_service.get_status())
        
    @app.route('/api/start', methods=['POST'])
    def start_bot() -> Dict[str, Any]:
        """Start the bot.
        
        Returns:
            JSON response with operation result
        """
        success = bot_service.start()
        return jsonify({
            "success": success,
            "status": bot_service.status.name,
            "error": bot_service.error_message
        })
        
    @app.route('/api/stop', methods=['POST'])
    def stop_bot() -> Dict[str, Any]:
        """Stop the bot.
        
        Returns:
            JSON response with operation result
        """
        success = bot_service.stop()
        return jsonify({
            "success": success,
            "status": bot_service.status.name,
            "error": bot_service.error_message
        })
        
    @app.route('/api/config', methods=['GET'])
    def get_config() -> Dict[str, Any]:
        """Get bot configuration.
        
        Returns:
            JSON response with bot configuration
        """
        return jsonify({
            "symbols": bot_service.symbols,
            "initial_capital": bot_service.initial_capital,
            "strategy": str(bot_service.strategy)
        })
        
    @app.route('/api/config', methods=['PUT'])
    def update_config() -> Dict[str, Any]:
        """Update bot configuration.
        
        Returns:
            JSON response with operation result
        """
        if bot_service.status != BotStatus.STOPPED:
            return jsonify({
                "success": False,
                "error": "Cannot update config while bot is running"
            }), 400
            
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
                    "initial_capital": bot_service.initial_capital
                }
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 400
            
    return app 