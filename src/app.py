from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import time
from datetime import datetime
from main import TradingBot
from config import DEFAULT_SYMBOL

app = Flask(__name__)
socketio = SocketIO(app)
bot = None
bot_thread = None

def format_runtime(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def run_bot():
    global bot
    bot = TradingBot()
    bot.run()

@app.route('/')
def index():
    return render_template('index.html', default_symbol=DEFAULT_SYMBOL)

def emit_updates():
    while True:
        if bot:
            # Get current state
            runtime = format_runtime((datetime.now() - bot.start_time).seconds)
            market_open = bot.is_market_open()
            
            account_info = bot.get_account_info() or {
                'equity': 0,
                'cash': 0,
                'buying_power': 0
            }
            
            latest_price = bot.data_handler.get_latest_price()
            price_change = 0
            if latest_price and bot.last_price:
                price_change = ((latest_price - bot.last_price) / bot.last_price) * 100
            
            # Emit update
            socketio.emit('update', {
                'runtime': runtime,
                'market_open': market_open,
                'account_info': account_info,
                'positions': bot.positions,
                'latest_price': latest_price or 0,
                'price_change': price_change
            })
        
        time.sleep(1)

if __name__ == '__main__':
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Start update emitter in a separate thread
    update_thread = threading.Thread(target=emit_updates)
    update_thread.daemon = True
    update_thread.start()
    
    # Start Flask app
    socketio.run(app, host='0.0.0.0', port=5000) 