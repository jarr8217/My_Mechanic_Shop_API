"""Main entry point for the My Mechanic Shop Flask application."""

from app import create_app
from app.models import db

app = create_app(config_name='DevelopmentConfig')

with app.app_context():
    db.create_all()

app.run(debug=True)
