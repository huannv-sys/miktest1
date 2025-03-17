import os
from datetime import timedelta

class Config:
    # Flask configuration
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        if DEBUG:
            SECRET_KEY = "dev_secret_key_not_secure"
            print("WARNING: Using insecure default SECRET_KEY. This should be set in production.")
        else:
            import secrets
            SECRET_KEY = secrets.token_hex(32)
            print("WARNING: No SECRET_KEY set. Generated a random one for this session.")
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///instance/mikrotik_monitor.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # JWT configuration
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    if not JWT_SECRET_KEY:
        if DEBUG:
            JWT_SECRET_KEY = "jwt_dev_secret_key_not_secure"
            print("WARNING: Using insecure default JWT_SECRET_KEY. This should be set in production.")
        else:
            import secrets
            JWT_SECRET_KEY = secrets.token_hex(32)
            print("WARNING: No JWT_SECRET_KEY set. Generated a random one for this session.")
    
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "60")))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.environ.get("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "30")))
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    
    # Security: Use secure cookies in production
    JWT_COOKIE_SECURE = os.environ.get("JWT_COOKIE_SECURE", "0") == "1" or not DEBUG
    
    # Security: Enable CSRF protection by default
    JWT_COOKIE_CSRF_PROTECT = os.environ.get("JWT_COOKIE_CSRF_PROTECT", "1") == "1"
    
    JWT_ACCESS_COOKIE_PATH = "/"
    JWT_REFRESH_COOKIE_PATH = "/"
    
    # Security: CSRF settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get("WTF_CSRF_SECRET_KEY", SECRET_KEY)
    
    # Monitoring configuration
    MONITORING_INTERVAL = 60  # seconds
    ALERT_CHECK_INTERVAL = 30  # seconds
    
    # MikroTik API configuration
    MIKROTIK_CONNECTION_TIMEOUT = int(os.environ.get("MIKROTIK_CONNECTION_TIMEOUT", "10"))
    MIKROTIK_COMMAND_TIMEOUT = int(os.environ.get("MIKROTIK_COMMAND_TIMEOUT", "15"))
    
    # Email configuration
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")
    
    # Telegram configuration
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
