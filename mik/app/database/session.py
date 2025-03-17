from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from mik.app import db
import logging
import os
import time

# Configure logger
logger = logging.getLogger(__name__)

def wait_for_db(app, max_retries=5, retry_interval=2):
    """Wait for database to be available with retry mechanism"""
    from sqlalchemy import text
    
    retries = 0
    while retries < max_retries:
        try:
            # Try to execute a simple query within app context
            with app.app_context():
                db.session.execute(text("SELECT 1"))
                db.session.commit()
                logger.info("Database connection successful")
                return True
        except Exception as e:
            retries += 1
            logger.warning(f"Database connection attempt {retries}/{max_retries} failed: {str(e)}")
            if retries >= max_retries:
                logger.error(f"Failed to connect to database after {max_retries} attempts")
                return False
            time.sleep(retry_interval)
    return False

def get_session():
    """Get a database session"""
    return db.session

def initialize_db(app):
    """Initialize database with default settings"""
    # Wait for database to be ready
    if not wait_for_db(app, max_retries=5, retry_interval=2):
        logger.error("Could not connect to database after multiple attempts")
        # Continue anyway - the app might still work with a late-connecting database
    
    try:
        # Ensure we have the instance directory
        instance_path = app.instance_path
        os.makedirs(instance_path, exist_ok=True)
        logger.info(f"Using instance path: {instance_path}")
        
        # Create database tables if they don't exist
        with app.app_context():
            db.create_all()
            logger.info("Database tables created")
            
            # Load models and crud functions within app context
            from mik.app.database.models import Setting
            from mik.app.database.crud import get_setting
            
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
                try:
                    if get_setting(key) is None:
                        logger.info(f"Creating default setting: {key}={value}")
                        setting = Setting(key=key, value=value)
                        db.session.add(setting)
                except Exception as setting_error:
                    logger.warning(f"Error setting '{key}': {str(setting_error)}")
            
            try:
                db.session.commit()
                logger.info("Database initialized with default settings")
            except Exception as commit_error:
                db.session.rollback()
                logger.error(f"Error committing settings: {str(commit_error)}")
                
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        # Don't rollback here - it might fail if session is invalid
