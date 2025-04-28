"""Script to run the trading bot in mocked mode with web interface."""

import os
import sys
from pathlib import Path
import threading
import time
from datetime import datetime
import logging

# Add the project root directory to the Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO
from dotenv import load_dotenv
from src.core.bot import TradingBot
from src.core.strategy import Strategy
from src.utils.config import get_config
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger(__name__)

# Initialize Flask app with template folder
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
socketio = SocketIO(app)

# Initialize bot with mocked configuration
config = get_config()
strategy = Strategy(config)

# Set up mock environment variables
os.environ['ALPACA_API_KEY'] = 'mock_key'  # nosec
os.environ['ALPACA_SECRET_KEY'] = 'mock_secret'  # nosec
os.environ['ALPACA_PAPER'] = 'true'

bot = TradingBot(
    strategy=strategy,
    symbols=[config['DEFAULT_SYMBOL']],
    initial_capital=float(config.get('INITIAL_BALANCE', 100000.0))
)

def format_runtime(seconds):
    """Format runtime in HH:MM:SS"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def run_bot():
    """Start the trading bot"""
    try:
        logger.info("Starting mocked trading bot...")
        bot.start()
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

@app.route('/')
def index():
    """Render the dashboard"""
    return render_template('index.html', default_symbol=config['DEFAULT_SYMBOL'])

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory(static_dir, filename)

def emit_updates():
    """Continuously emit updates to the web interface"""
    start_time = time.time()
    
    while True:
        try:
            # Calculate runtime
            runtime = int(time.time() - start_time)
            
            # Get market status and data
            market_open = datetime.now().hour >= 9 and datetime.now().hour < 16
            latest_price = 150.0  # Mock price
            positions = bot.portfolio.get_all_positions()
            account_info = {
                'equity': bot.portfolio.get_value(),
                'cash': bot.portfolio.get_balance(),
                'buying_power': bot.portfolio.get_balance() * 2
            }
            
            # Emit update
            socketio.emit('update', {
                'runtime': format_runtime(runtime),
                'market_open': market_open,
                'account_info': account_info,
                'positions': positions,
                'latest_price': latest_price,
                'price_change': 0.0  # Mock value
            })
            
            # Sleep for 1 second
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error in emit_updates: {e}")
            time.sleep(5)

def main():
    """Run the trading bot in mocked mode with web interface."""
    try:
        # Start bot in a separate thread
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()
        
        # Start update emitter in a separate thread
        update_thread = threading.Thread(target=emit_updates)
        update_thread.daemon = True
        update_thread.start()
        
        # Start web server
        logger.info("Starting web server on http://127.0.0.1:5050")
        debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
        socketio.run(app, host='127.0.0.1', port=5050, debug=debug_mode)
        
    except KeyboardInterrupt:
        logger.info("Stopping mocked trading bot...")
        bot.stop()
    except Exception as e:
        logger.error(f"Error running mocked bot: {e}")

if __name__ == "__main__":
    main() 