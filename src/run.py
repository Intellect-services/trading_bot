import os

from app import app, socketio

if __name__ == "__main__":
    # Get configuration from environment variables
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    host = os.getenv("FLASK_HOST", "127.0.0.1")  # Default to localhost
    port = int(os.getenv("FLASK_PORT", "5001"))

    # Start the Flask application with secure defaults
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug_mode,
        allow_unsafe_werkzeug=False,  # Disable Werkzeug debugger in production
    )
