"""Script to run the trading bot in mocked mode with web interface."""

import eventlet
eventlet.monkey_patch()

import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# Add the project root directory to the Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from flask import Flask, render_template, send_from_directory, request, jsonify
from flask_socketio import SocketIO
from dotenv import load_dotenv

from src.core.bot_service import BotService
from src.core.data_feed import MockDataFeed
from src.core.strategy import Strategy
from src.core.portfolio import Portfolio
from src.core.risk_manager import RiskManager
from src.utils.config import Config
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger(__name__)

# Initialize bot with mocked configuration
config = Config()
strategy = Strategy(config)

# Set up mock environment variables
os.environ['ALPACA_API_KEY'] = 'mock_key'  # nosec
os.environ['ALPACA_SECRET_KEY'] = 'mock_secret'  # nosec
os.environ['ALPACA_PAPER'] = 'true'

# Initialize bot components
data_feed = MockDataFeed()
portfolio = Portfolio(initial_capital=float(config.get('INITIAL_BALANCE', 100000.0)))
risk_manager = RiskManager()

# Initialize bot service with required components
bot_service = BotService(
    strategy=strategy,
    symbols=['AAPL', 'GOOGL', 'MSFT'],  # Default symbols
    initial_capital=float(config.get('INITIAL_BALANCE', 100000.0))
)

# Track bot state
bot_state = {
    'status': 'stopped',
    'start_time': None,
    'runtime': '00:00:00'
}

# Initialize Flask app
app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

def format_runtime(seconds):
    """Format runtime in HH:MM:SS"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def update_runtime():
    """Update the runtime based on start time"""
    if bot_state['status'] == 'running' and bot_state['start_time']:
        elapsed = int((datetime.now() - bot_state['start_time']).total_seconds())
        bot_state['runtime'] = format_runtime(elapsed)
    else:
        bot_state['runtime'] = '00:00:00'

@app.route('/')
def index():
    """Render the dashboard"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get bot status"""
    try:
        update_runtime()
        return jsonify({
            'success': True,
            'status': bot_state['status'],
            'runtime': bot_state['runtime'],
            'market_status': 'open',  # Mock market is always open
            'metrics': {
                'initial_capital': bot_service.initial_capital,
                'current_capital': bot_service.initial_capital,  # Mock value
                'active_positions': 0  # Mock value
            }
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/start', methods=['POST'])
def start_bot():
    """Start the bot"""
    try:
        if bot_state['status'] != 'running':
            bot_service.start()
            bot_state['status'] = 'running'
            bot_state['start_time'] = datetime.now()
            update_runtime()
            logger.info("Bot started successfully")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    """Stop the bot"""
    try:
        if bot_state['status'] == 'running':
            bot_service.stop()
            bot_state['status'] = 'stopped'
            bot_state['start_time'] = None
            update_runtime()
            logger.info("Bot stopped successfully")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# SocketIO event handlers
@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

# Background task to send updates
def send_updates():
    while True:
        try:
            update_runtime()
            socketio.emit('status_update', {
                'status': bot_state['status'],
                'runtime': bot_state['runtime'],
                'market_status': 'open',  # Mock market is always open
                'metrics': {
                    'initial_capital': bot_service.initial_capital,
                    'current_capital': bot_service.initial_capital,  # Mock value
                    'active_positions': 0  # Mock value
                },
                'log': f"Bot {bot_state['status']} - Runtime: {bot_state['runtime']}"
            })
            eventlet.sleep(1)  # Send updates every second
        except Exception as e:
            logger.error(f"Error sending updates: {e}")
            eventlet.sleep(1)

def main():
    """Run the trading bot in mocked mode with web interface."""
    try:
        # Start the background task
        socketio.start_background_task(send_updates)
        
        # Start web server
        logger.info("Starting web server on http://0.0.0.0:5051")
        # Run the Flask application
        app.run(
            # Default to localhost for security, only bind to all interfaces when explicitly configured
            host=os.getenv('FLASK_HOST', '127.0.0.1'),  # nosec
            port=5051,
            debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
            use_reloader=False,
            log_output=True
        )
        
    except KeyboardInterrupt:
        logger.info("Stopping mocked trading bot...")
        bot_service.stop()
    except Exception as e:
        logger.error(f"Error running mocked bot: {e}")
        logger.exception("Full traceback:")

if __name__ == "__main__":
    main() 