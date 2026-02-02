import os
from datetime import timedelta

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Application configuration"""
    
    # ✅ FIXED: Proper SECRET_KEY handling with validation
    SECRET_KEY = os.environ.get("SECRET_KEY")
    
    # Debug output to verify SECRET_KEY is loaded
    if SECRET_KEY:
        print(f"✅ SECRET_KEY loaded successfully (length: {len(SECRET_KEY)})")
    else:
        print("❌ WARNING: SECRET_KEY not found in environment variables!")
        print("❌ Available environment variables:")
        for key in os.environ.keys():
            if 'SECRET' in key.upper() or 'KEY' in key.upper():
                print(f"   - {key}")
        
        # Use a fallback for development, but warn loudly
        SECRET_KEY = "dev-fallback-key-DO-NOT-USE-IN-PRODUCTION"
        print(f"⚠️  Using fallback SECRET_KEY: {SECRET_KEY[:20]}...")
    
    # Database
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or \
        "sqlite:///" + os.path.join(BASE_DIR, "finance_app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    
    # ✅ SESSION / COOKIE FIX (CRITICAL)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    PREFERRED_URL_SCHEME = "https"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    DEBUG = False
