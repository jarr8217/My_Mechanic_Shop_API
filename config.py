import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS =False

class DevelopmentConfig:
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:root1234!@localhost:3306/mechanic_shop_db'
    DEBUG=True

class TestingConfig:
    pass

class ProductionConfig:
    pass