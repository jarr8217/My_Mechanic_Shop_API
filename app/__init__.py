from flask import Flask
from .extensions import ma, limiter, cache
from .models import db
from .blueprints.customers import customers_bp
from .blueprints.mechanics import mechanics_bp
from .blueprints.service_tickets import service_tickets_bp
from .blueprints.inventory import inventory_bp
from .blueprints.auth import auth_bp
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from config import DevelopmentConfig, TestingConfig, ProductionConfig
from dotenv import load_dotenv
import os

load_dotenv()

config_map = {
    'DevelopmentConfig': DevelopmentConfig,
    'TestingConfig': TestingConfig,
    'ProductionConfig': ProductionConfig
}


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    # Enable CORS for all routes
    CORS(app)

    # initialize extensions
    ma.init_app(app)
    db.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)

    # Swagger UI setup
    SWAGGER_URL = '/api/docs'
    API_URL = '/static/swagger.yaml'
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            "app_name": "My Mechanic Shop API"
        }
    )

    # register Blueprints
    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(mechanics_bp, url_prefix='/mechanics')
    app.register_blueprint(service_tickets_bp, url_prefix='/service_tickets')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    return app


# Create app instance for Gunicorn
config_name = os.getenv('CONFIG_NAME', 'ProductionConfig')
app = create_app(config_name)

# Create database tables
with app.app_context():
    db.create_all()
