"""Web server for monitoring the trading bot."""

from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import time
from datetime import datetime
import logging
import os
from src.core.bot import TradingBot
from src.utils.config import Config
from src.utils.logger import setup_logger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app with template folder
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)
socketio = SocketIO(app)

# Initialize configuration
config = Config()

# Initialize bot with configuration
bot = None
if config.get('alpaca_api_key') and config.get('alpaca_secret_key'):
    bot = TradingBot(
        config={
            'API_KEY': config.get('alpaca_api_key'),
            'SECRET_KEY': config.get('alpaca_secret_key'),
            'PAPER': config.get('paper_trading', True),
            'INITIAL_BALANCE': config.get('initial_balance', 10000.0)
        }
    )
    # Add default symbol
    bot.add_symbol(config.get('DEFAULT_SYMBOL', 'AAPL'))
else:
    logger.warning("API keys not found in configuration. Running in demo mode.")

def format_runtime(seconds):
    """Format runtime in HH:MM:SS"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def run_bot():
    """Start the trading bot"""
    if bot:
        try:
            bot.start()
            logger.info("Bot started successfully")
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
    else:
        logger.info("Bot not initialized. Running in demo mode.")

@app.route('/')
def index():
    """Render the dashboard"""
    return render_template('index.html', default_symbol=config.get('DEFAULT_SYMBOL', 'AAPL'))

def emit_updates():
    """Continuously emit updates to the web interface"""
    start_time = time.time()
    
    while True:
        try:
            # Calculate runtime
            runtime = int(time.time() - start_time)
            
            # Get market status and data
            if bot and bot.data_feed:
                market_open = bot.data_feed.is_market_open()
                latest_price = bot.data_feed.get_latest_price('AAPL')
                positions = bot.portfolio.get_all_positions()
                account_info = {
                    'equity': bot.portfolio.get_value(),
                    'cash': bot.portfolio.get_balance(),
                    'buying_power': bot.portfolio.get_balance() * 2  # Assuming 2x margin
                }
            else:
                # Demo mode with mock data
                market_open = datetime.now().hour >= 9 and datetime.now().hour < 16
                latest_price = 150.0  # Mock price
                positions = {}  # No positions in demo mode
                account_info = {
                    'equity': config.get('initial_balance', 10000.0),
                    'cash': config.get('initial_balance', 10000.0),
                    'buying_power': config.get('initial_balance', 10000.0) * 2
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
            time.sleep(5)  # Wait longer on error

if __name__ == '__main__':
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