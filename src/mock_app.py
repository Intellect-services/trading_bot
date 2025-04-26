from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import time
from datetime import datetime
from mock_bot import MockTradingBot

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
    bot = MockTradingBot()
    bot.run()


@app.route("/")
def index():
    return render_template("index.html", default_symbol="AAPL")


def emit_updates():
    while True:
        if bot:
            # Get current state
            runtime = format_runtime((datetime.now() - bot.start_time).seconds)
            market_open = bot.is_market_open()

            account_info = bot.get_account_info()
            positions = bot.get_positions()
            latest_price = bot.get_latest_price()
            price_change = bot.get_price_change()

            # Emit update
            socketio.emit(
                "update",
                {
                    "runtime": runtime,
                    "market_open": market_open,
                    "account_info": account_info,
                    "positions": positions,
                    "latest_price": latest_price,
                    "price_change": price_change,
                },
            )

        time.sleep(1)


if __name__ == "__main__":
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Start update emitter in a separate thread
    update_thread = threading.Thread(target=emit_updates)
    update_thread.daemon = True
    update_thread.start()

    # Start Flask app
    socketio.run(app, host="127.0.0.1", port=5050)
