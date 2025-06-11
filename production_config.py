import os

class ProductionConfig:
    """Production configuration for CVLatex application"""
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'cvlatex-production-secret-key-change-this'
    DEBUG = False
    TESTING = False
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'
    OUTPUT_FOLDER = 'output'
    
    # Security headers
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
    
    # CORS settings (if needed)
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'cvlatex.log'
    
    # Rate limiting (requests per minute)
    RATELIMIT_DEFAULT = "100/minute"
    
    # Environment
    ENV = 'production' 