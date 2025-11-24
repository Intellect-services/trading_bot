import os
import sys

from src.app import app, socketio

if __name__ == "__main__":
    try:
        # Get port from environment variable or use default
        port = int(os.getenv("FLASK_RUN_PORT", 5002))
        print(f"Starting server on http://localhost:{port}")
        socketio.run(app, host="0.0.0.0", port=port, debug=True)
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        sys.exit(1)
