import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Application configuration"""
    
    # SECRET KEY
    SECRET_KEY = "6d9c59de09478b9c81bb9bf2190a702bc566f56b0c54eafbbcf735d11edb3882"
    print(f"✅ SECRET_KEY loaded successfully (length: {len(SECRET_KEY)})")
    
    # DATABASE
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL.replace(
            "postgres://", "postgresql://", 1
        )
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "finance_app.db")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    
    # ========================================================================
    # ✅ FIXED: Session / Cookies (RAILWAY COMPATIBLE)
    # ========================================================================
    # CRITICAL: Don't use SESSION_COOKIE_SECURE=True on Railway!
    # Railway's load balancer terminates SSL, so the app sees HTTP
    SESSION_COOKIE_SECURE = False  # ← CHANGED FROM True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    
    REMEMBER_COOKIE_SECURE = False  # ← CHANGED FROM True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Don't force HTTPS scheme (Railway handles this)
    # PREFERRED_URL_SCHEME = "https"  # ← REMOVED
    
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Flask
    DEBUG = False
