import os
import logging
from datetime import datetime
from flask import Flask, request, redirect, url_for, session, jsonify, render_template
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from src.core.alpaca_service import AlpacaService
from src.core.trading_bot import TradingBot
from src.utils.config import Config
from app import app, socketio

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key')
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Alpaca service and trading bot
alpaca_service = AlpacaService()
trading_bot = TradingBot(alpaca_service)

# Global state
bot_status = {
    'is_running': False,
    'market_status': 'unknown',
    'runtime': '00:00:00',
    'last_update': None,
    'metrics': {
        'initial_capital': 0,
        'current_capital': 0,
        'total_trades': 0,
        'win_rate': 0,
        'profit_factor': 0,
        'sharpe_ratio': 0,
        'active_positions': 0
    }
}

def update_bot_status():
    """Update bot status and emit updates to connected clients"""
    while True:
        try:
            # Get market status
            market_status = alpaca_service.get_market_status()
            bot_status['market_status'] = market_status['status']
            
            # Get account info
            account = alpaca_service.get_account()
            if account:
                bot_status['metrics']['current_capital'] = float(account.get('equity', 0))
                if not bot_status['metrics']['initial_capital']:
                    bot_status['metrics']['initial_capital'] = float(account.get('equity', 0))
            
            # Get positions
            positions = alpaca_service.get_positions()
            bot_status['metrics']['active_positions'] = len(positions) if positions else 0
            
            # Update runtime if bot is running
            if bot_status['is_running']:
                if bot_status['last_update']:
                    runtime = datetime.now() - bot_status['last_update']
                    bot_status['runtime'] = str(runtime).split('.')[0]
                else:
                    bot_status['last_update'] = datetime.now()
            
            # Emit update to all connected clients
            socketio.emit('bot_update', bot_status)
            
        except Exception as e:
            logger.error(f"Error updating bot status: {str(e)}")
            socketio.emit('bot_update', {
                'error': str(e),
                'is_running': bot_status['is_running'],
                'runtime': bot_status['runtime']
            })
        
        socketio.sleep(5)  # Update every 5 seconds

# Start status update thread
socketio.start_background_task(update_bot_status)

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == os.getenv('ADMIN_USERNAME', 'admin@admin.com') and \
           password == os.getenv('ADMIN_PASSWORD', 'admin'):
            session['username'] = username
            return redirect(url_for('index'))
        
        return render_template('index.html', error='Invalid credentials')
    
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/api/status')
def get_status():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(bot_status)

@app.route('/api/start', methods=['POST'])
def start_bot():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        if not bot_status['is_running']:
            trading_bot.start()
            bot_status['is_running'] = True
            bot_status['last_update'] = datetime.now()
            return jsonify({'status': 'success'})
        return jsonify({'status': 'already_running'})
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        if bot_status['is_running']:
            trading_bot.stop()
            bot_status['is_running'] = False
            bot_status['runtime'] = '00:00:00'
            return jsonify({'status': 'success'})
        return jsonify({'status': 'already_stopped'})
    except Exception as e:
        logger.error(f"Error stopping bot: {str(e)}")
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")
    emit('bot_update', bot_status)

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")

if __name__ == '__main__':
    # Get configuration from environment variables
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.getenv('FLASK_HOST', '127.0.0.1')  # Default to localhost
    port = int(os.getenv('FLASK_PORT', '5001'))
    
    # Start the Flask application with secure defaults
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug_mode,
        allow_unsafe_werkzeug=False  # Disable Werkzeug debugger in production
    ) 