"""Main entry point for the My Mechanic Shop Flask application."""

from app import create_app
from app.models import db

flask_app = create_app('ProductionConfig')

with flask_app.app_context():
    db.create_all()

flask_app.run(debug=True)
