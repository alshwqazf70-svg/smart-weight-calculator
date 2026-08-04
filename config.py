import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'smart-iron-calculator-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///smart_iron.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123'
    ITEMS_PER_PAGE = 20
