from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from app import db
import logging

# Configure logger
logger = logging.getLogger(__name__)

def get_session():
    """Get a database session"""
    return db.session

def initialize_db(app):
    """Initialize database with default settings"""
    try:
        from app.database.models import Setting
        from app.database.crud import get_setting, update_settings
        
        # Initial settings
        default_settings = {
            # Email settings
            'email_enabled': 'False',
            'mail_server': '',
            'mail_port': '587',
            'mail_use_tls': 'True',
            'mail_username': '',
            'mail_password': '',
            'mail_from': '',
            
            # Telegram settings
            'telegram_enabled': 'False',
            'telegram_bot_token': '',
            'telegram_chat_id': '',
            
            # Monitoring settings
            'monitoring_interval': '60',  # seconds
            'alert_check_interval': '30',  # seconds
            'discovery_enabled': 'False',
            'discovery_schedule': '0 0 * * *',  # cron format (midnight)
            'discovery_subnets': '',  # comma-separated subnets
            
            # Backup settings
            'auto_backup_enabled': 'False',
            'backup_schedule': '0 0 * * 0',  # cron format (weekly on Sunday)
            'backup_retention_days': '30'
        }
        
        # Check if settings exist, if not create default ones
        for key, value in default_settings.items():
            if get_setting(key) is None:
                logger.info(f"Creating default setting: {key}={value}")
                setting = Setting(key=key, value=value)
                db.session.add(setting)
        
        db.session.commit()
        logger.info("Database initialized with default settings")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error initializing database: {str(e)}")
