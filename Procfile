web: gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 --worker-class eventlet --worker-connections 1000 src.app:app
release: python -c "from src.database import db, init_db; from src.app import app; init_db(app); db.create_all()"
scheduler: python scripts/run_marketing_scheduler.py
