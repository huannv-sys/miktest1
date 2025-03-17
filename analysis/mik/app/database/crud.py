import logging
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from app import db
from app.database.models import User, Device, Metric, AlertRule, Alert, Setting

# Configure logger
logger = logging.getLogger(__name__)

# User operations
def get_user_by_username(username):
    """Get a user by username"""
    try:
        return User.query.filter_by(username=username).first()
    except SQLAlchemyError as e:
        logger.error(f"Database error getting user by username: {str(e)}")
        return None

def get_user_by_id(user_id):
    """Get a user by ID"""
    try:
        return User.query.get(user_id)
    except SQLAlchemyError as e:
        logger.error(f"Database error getting user by ID: {str(e)}")
        return None

def get_all_users():
    """Get all users"""
    try:
        return User.query.all()
    except SQLAlchemyError as e:
        logger.error(f"Database error getting all users: {str(e)}")
        return []

def create_user(username, password, email, role='user'):
    """Create a new user"""
    try:
        user = User(
            username=username,
            password_hash=password,
            email=email,
            role=role
        )
        db.session.add(user)
        db.session.commit()
        return user
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error creating user: {str(e)}")
        raise

def update_user(user_id, username=None, password=None, email=None, role=None):
    """Update user details"""
    try:
        user = User.query.get(user_id)
        if not user:
            return None
        
        if username:
            user.username = username
        if password:
            user.password_hash = password
        if email:
            user.email = email
        if role:
            user.role = role
        
        db.session.commit()
        return user
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error updating user: {str(e)}")
        return None

def delete_user(user_id):
    """Delete a user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return False
        
        db.session.delete(user)
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error deleting user: {str(e)}")
        return False

def update_user_last_login(username):
    """Update user's last login timestamp"""
    try:
        user = get_user_by_username(username)
        if user:
            user.last_login = datetime.utcnow()
            db.session.commit()
            return True
        return False
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error updating last login: {str(e)}")
        return False

# Device operations
def get_all_devices():
    """Get all devices"""
    try:
        return Device.query.all()
    except SQLAlchemyError as e:
        logger.error(f"Database error getting all devices: {str(e)}")
        return []

def get_device_by_id(device_id):
    """Get a device by ID"""
    try:
        return Device.query.get(device_id)
    except SQLAlchemyError as e:
        logger.error(f"Database error getting device by ID: {str(e)}")
        return None

def create_device(name, ip_address, username, password, api_port=8728, use_ssl=False, model=None, location=None, notes=None):
    """Create a new device"""
    try:
        device = Device(
            name=name,
            ip_address=ip_address,
            username=username,
            password=password,
            api_port=api_port,
            use_ssl=use_ssl,
            model=model,
            location=location,
            notes=notes
        )
        db.session.add(device)
        db.session.commit()
        return device
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error creating device: {str(e)}")
        raise

def update_device(device_id, name=None, ip_address=None, username=None, password=None, api_port=None, use_ssl=None, model=None, location=None, notes=None):
    """Update device details"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return None
        
        if name:
            device.name = name
        if ip_address:
            device.ip_address = ip_address
        if username:
            device.username = username
        if password:
            device.password = password
        if api_port is not None:
            device.api_port = api_port
        if use_ssl is not None:
            device.use_ssl = use_ssl
        if model:
            device.model = model
        if location is not None:  # Allow empty location
            device.location = location
        if notes is not None:  # Allow empty notes
            device.notes = notes
        
        device.updated_at = datetime.utcnow()
        db.session.commit()
        return device
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error updating device: {str(e)}")
        return None

def delete_device(device_id):
    """Delete a device"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return False
        
        db.session.delete(device)
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error deleting device: {str(e)}")
        return False

def get_devices_count():
    """Get count of devices"""
    try:
        return Device.query.count()
    except SQLAlchemyError as e:
        logger.error(f"Database error getting devices count: {str(e)}")
        return 0

# Metrics operations
def save_device_metrics(device_id, metrics_data):
    """Save device metrics to database"""
    try:
        # Extract metrics from data
        metrics_to_save = []
        
        # CPU metrics
        if 'cpu_load' in metrics_data:
            metrics_to_save.append(Metric(
                device_id=device_id,
                metric_type='cpu',
                metric_name='load',
                value=metrics_data['cpu_load']
            ))
        
        # Memory metrics
        if 'memory_usage' in metrics_data:
            metrics_to_save.append(Metric(
                device_id=device_id,
                metric_type='memory',
                metric_name='usage',
                value=metrics_data['memory_usage']
            ))
        
        # Disk metrics
        if 'disk_usage' in metrics_data:
            metrics_to_save.append(Metric(
                device_id=device_id,
                metric_type='disk',
                metric_name='usage',
                value=metrics_data['disk_usage']
            ))
        
        # Add more metrics as needed
        
        # Save metrics to database
        if metrics_to_save:
            db.session.add_all(metrics_to_save)
            db.session.commit()
            return True
        return False
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error saving metrics: {str(e)}")
        return False

def get_metrics_for_device(device_id, metric_type=None, metric_name=None, start_time=None, end_time=None, limit=100):
    """Get metrics for a device with optional filters"""
    try:
        query = Metric.query.filter_by(device_id=device_id)
        
        if metric_type:
            query = query.filter_by(metric_type=metric_type)
        
        if metric_name:
            query = query.filter_by(metric_name=metric_name)
        
        if start_time:
            query = query.filter(Metric.timestamp >= start_time)
        
        if end_time:
            query = query.filter(Metric.timestamp <= end_time)
        
        query = query.order_by(Metric.timestamp.desc()).limit(limit)
        
        return query.all()
    except SQLAlchemyError as e:
        logger.error(f"Database error getting metrics: {str(e)}")
        return []

# Alert rules operations
def get_all_alert_rules(enabled_only=False):
    """Get all alert rules"""
    try:
        query = AlertRule.query
        if enabled_only:
            query = query.filter_by(enabled=True)
        return query.all()
    except SQLAlchemyError as e:
        logger.error(f"Database error getting alert rules: {str(e)}")
        return []

def get_alert_rules():
    """Get all alert rules"""
    try:
        return AlertRule.query.all()
    except SQLAlchemyError as e:
        logger.error(f"Database error getting alert rules: {str(e)}")
        return []

def get_alert_rule_by_id(rule_id):
    """Get an alert rule by ID"""
    try:
        return AlertRule.query.get(rule_id)
    except SQLAlchemyError as e:
        logger.error(f"Database error getting alert rule: {str(e)}")
        return None

def create_alert_rule(name, device_id, metric, condition, threshold, duration=0, enabled=True, 
                      notify_email=False, notify_telegram=False, email_recipients='', message_template=''):
    """Create a new alert rule"""
    try:
        rule = AlertRule(
            name=name,
            device_id=device_id,
            metric=metric,
            condition=condition,
            threshold=threshold,
            duration=duration,
            enabled=enabled,
            notify_email=notify_email,
            notify_telegram=notify_telegram,
            email_recipients=email_recipients,
            message_template=message_template
        )
        db.session.add(rule)
        db.session.commit()
        return rule
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error creating alert rule: {str(e)}")
        raise

def update_alert_rule(rule_id, name=None, device_id=None, metric=None, condition=None, threshold=None, 
                     duration=None, enabled=None, notify_email=None, notify_telegram=None, 
                     email_recipients=None, message_template=None):
    """Update an alert rule"""
    try:
        rule = AlertRule.query.get(rule_id)
        if not rule:
            return None
        
        if name:
            rule.name = name
        if device_id:
            rule.device_id = device_id
        if metric:
            rule.metric = metric
        if condition:
            rule.condition = condition
        if threshold is not None:
            rule.threshold = threshold
        if duration is not None:
            rule.duration = duration
        if enabled is not None:
            rule.enabled = enabled
        if notify_email is not None:
            rule.notify_email = notify_email
        if notify_telegram is not None:
            rule.notify_telegram = notify_telegram
        if email_recipients is not None:
            rule.email_recipients = email_recipients
        if message_template is not None:
            rule.message_template = message_template
        
        rule.updated_at = datetime.utcnow()
        db.session.commit()
        return rule
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error updating alert rule: {str(e)}")
        return None

def delete_alert_rule(rule_id):
    """Delete an alert rule"""
    try:
        rule = AlertRule.query.get(rule_id)
        if not rule:
            return False
        
        db.session.delete(rule)
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error deleting alert rule: {str(e)}")
        return False

# Alerts operations
def create_alert(rule_id, device_id, metric, value, threshold, condition):
    """Create a new alert"""
    try:
        alert = Alert(
            rule_id=rule_id,
            device_id=device_id,
            metric=metric,
            value=value,
            threshold=threshold,
            condition=condition
        )
        db.session.add(alert)
        db.session.commit()
        return alert
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error creating alert: {str(e)}")
        return None

def get_recent_alerts(limit=20):
    """Get recent alerts"""
    try:
        return Alert.query.order_by(Alert.timestamp.desc()).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Database error getting recent alerts: {str(e)}")
        return []

def get_alerts_count():
    """Get count of unacknowledged alerts"""
    try:
        return Alert.query.filter_by(acknowledged=False).count()
    except SQLAlchemyError as e:
        logger.error(f"Database error getting alerts count: {str(e)}")
        return 0

def acknowledge_alert(alert_id, user_id):
    """Acknowledge an alert"""
    try:
        alert = Alert.query.get(alert_id)
        if not alert:
            return False
        
        alert.acknowledged = True
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.utcnow()
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error acknowledging alert: {str(e)}")
        return False

# Settings operations
def get_settings():
    """Get all settings as dictionary"""
    try:
        settings = {}
        for setting in Setting.query.all():
            settings[setting.key] = setting.value
        return settings
    except SQLAlchemyError as e:
        logger.error(f"Database error getting settings: {str(e)}")
        return {}

def get_setting(key, default=None):
    """Get a specific setting"""
    try:
        setting = Setting.query.filter_by(key=key).first()
        return setting.value if setting else default
    except SQLAlchemyError as e:
        logger.error(f"Database error getting setting {key}: {str(e)}")
        return default

def update_settings(settings_dict):
    """Update multiple settings at once"""
    try:
        for key, value in settings_dict.items():
            setting = Setting.query.filter_by(key=key).first()
            if setting:
                setting.value = value
            else:
                setting = Setting(key=key, value=value)
                db.session.add(setting)
        
        db.session.commit()
        return get_settings()
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error updating settings: {str(e)}")
        return {}
