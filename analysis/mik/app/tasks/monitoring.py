import logging
from datetime import datetime, timedelta
from app import app, scheduler, db
from app.database.crud import get_all_devices, save_device_metrics, get_setting
from app.core.mikrotik import get_device_metrics
from app.config import Config
from app.database.models import Metric

# Configure logger
logger = logging.getLogger(__name__)

def collect_metrics():
    """Collect metrics from all devices"""
    with app.app_context():
        try:
            logger.debug("Starting metrics collection task")
            devices = get_all_devices()
            
            for device in devices:
                try:
                    # Get metrics from device
                    metrics = get_device_metrics(device)
                    
                    # Save metrics to database
                    if metrics.get('online', False):
                        save_device_metrics(device.id, metrics)
                    else:
                        logger.warning(f"Device {device.name} is offline, skipping metrics collection")
                except Exception as e:
                    logger.error(f"Error collecting metrics for device {device.name}: {str(e)}")
            
            logger.debug("Metrics collection task completed")
        except Exception as e:
            logger.error(f"Error in metrics collection task: {str(e)}")

def schedule_metrics_collection():
    """Schedule periodic metrics collection"""
    try:
        interval = Config.MONITORING_INTERVAL
        
        # Add job to scheduler
        scheduler.add_job(
            func=collect_metrics,
            trigger='interval',
            seconds=interval,
            id='collect_metrics',
            replace_existing=True
        )
        
        logger.info(f"Scheduled metrics collection every {interval} seconds")
    except Exception as e:
        logger.error(f"Error scheduling metrics collection: {str(e)}")

def clear_old_metrics():
    """Clear old metrics data to prevent database bloat"""
    with app.app_context():
        try:
            # Get retention period from settings (default 30 days)
            retention_days = int(get_setting('metrics_retention_days', '30'))
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Delete old metrics
            deleted = Metric.query.filter(Metric.timestamp < cutoff_date).delete()
            db.session.commit()
            
            logger.info(f"Cleared {deleted} old metrics records older than {retention_days} days")
        except Exception as e:
            logger.error(f"Error clearing old metrics: {str(e)}")
            db.session.rollback()

def initialize_monitoring_tasks():
    """Initialize all monitoring tasks"""
    # Schedule metrics collection
    schedule_metrics_collection()
    
    # Schedule old metrics cleanup (daily at 1 AM)
    scheduler.add_job(
        func=clear_old_metrics,
        trigger='cron',
        hour=1,
        minute=0,
        id='clear_old_metrics',
        replace_existing=True
    )
    
    logger.info("Monitoring tasks initialized")
