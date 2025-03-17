import logging
from app import app, scheduler
from app.core.alerts import check_alerts
from app.config import Config

# Configure logger
logger = logging.getLogger(__name__)

def alert_check_task():
    """Task to check alert conditions"""
    with app.app_context():
        try:
            logger.debug("Starting alert check task")
            check_alerts()
            logger.debug("Alert check task completed")
        except Exception as e:
            logger.error(f"Error in alert check task: {str(e)}")

def schedule_alert_checks():
    """Schedule periodic alert checks"""
    try:
        interval = Config.ALERT_CHECK_INTERVAL
        
        # Add job to scheduler
        scheduler.add_job(
            func=alert_check_task,
            trigger='interval',
            seconds=interval,
            id='check_alerts',
            replace_existing=True
        )
        
        logger.info(f"Scheduled alert checks every {interval} seconds")
    except Exception as e:
        logger.error(f"Error scheduling alert checks: {str(e)}")

def initialize_alert_tasks():
    """Initialize all alert-related tasks"""
    # Schedule alert checks
    schedule_alert_checks()
