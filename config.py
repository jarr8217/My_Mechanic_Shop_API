import os


class Config:
    # Default for tests/dev
    SECRET_KEY = str(os.environ.get('SECRET_KEY', 'dev_secret_key'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:root1234!@localhost:3306/mechanic_shop_db'
    DEBUG = True


class TestingConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///testing.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    DEBUG = True
    CACHE_TYPE = 'SimpleCache'


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = str(os.environ.get(
        'SQLALCHEMY_DATABASE_URI', 'sqlite:///production.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
