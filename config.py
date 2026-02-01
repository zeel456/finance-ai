import os
from datetime import timedelta

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Application configuration"""
    
    # Secret key for sessions
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    # Render provides DATABASE_URL for PostgreSQL
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # Fix for PostgreSQL URL (Render uses 'postgres://' but SQLAlchemy needs 'postgresql://')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or \
        'sqlite:///' + os.path.join(BASE_DIR, 'finance_app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload configuration
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 10 * 1024 * 1024))
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # Tesseract path (auto-detected on deployment platforms)
    TESSERACT_PATH = os.environ.get('TESSERACT_PATH', 'tesseract')
    
    # Environment detection
    ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = ENV == 'development'