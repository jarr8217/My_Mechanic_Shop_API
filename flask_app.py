"""Main entry point for the My Mechanic Shop Flask application."""

from app import create_app
from app.models import db
import os

# Create app instance - use environment variable or default to ProductionConfig
config_name = os.getenv('CONFIG_NAME', 'ProductionConfig')
app = create_app(config_name)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
