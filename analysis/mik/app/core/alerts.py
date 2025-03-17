import logging
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from app.database.crud import (
    get_all_alert_rules,
    create_alert,
    get_device_by_id,
    get_settings
)
from app.core.mikrotik import get_device_metrics

# Configure logger
logger = logging.getLogger(__name__)

def check_alerts():
    """Check all alert rules and trigger alerts if needed"""
    try:
        # Get all enabled alert rules
        rules = get_all_alert_rules(enabled_only=True)
        
        # Get application settings
        settings = get_settings()
        
        for rule in rules:
            try:
                # Skip rules for non-existent devices
                device = get_device_by_id(rule.device_id)
                if not device:
                    logger.warning(f"Alert rule {rule.id} references non-existent device {rule.device_id}")
                    continue
                
                # Get current metrics
                metrics = get_device_metrics(device)
                
                # Skip offline devices
                if not metrics.get('online', False):
                    logger.debug(f"Device {device.name} is offline, skipping alert check")
                    continue
                
                # Get metric value based on rule
                metric_value = None
                
                if rule.metric == 'cpu_load':
                    metric_value = metrics.get('cpu_load', 0)
                elif rule.metric == 'memory_usage':
                    metric_value = metrics.get('memory_usage', 0)
                elif rule.metric == 'disk_usage':
                    metric_value = metrics.get('disk_usage', 0)
                # Add more metrics as needed
                
                if metric_value is None:
                    logger.warning(f"Metric {rule.metric} not available for device {device.name}")
                    continue
                
                # Check threshold condition
                alert_triggered = False
                
                if rule.condition == '>':
                    alert_triggered = metric_value > rule.threshold
                elif rule.condition == '<':
                    alert_triggered = metric_value < rule.threshold
                elif rule.condition == '>=':
                    alert_triggered = metric_value >= rule.threshold
                elif rule.condition == '<=':
                    alert_triggered = metric_value <= rule.threshold
                elif rule.condition == '==':
                    alert_triggered = metric_value == rule.threshold
                
                if alert_triggered:
                    # Create alert record
                    alert = create_alert(
                        rule_id=rule.id,
                        device_id=device.id,
                        metric=rule.metric,
                        value=metric_value,
                        threshold=rule.threshold,
                        condition=rule.condition
                    )
                    
                    # Prepare alert message
                    message = rule.message_template or generate_alert_message(rule, device, metric_value)
                    
                    # Send notifications
                    if rule.notify_email and settings.get('email_enabled', False):
                        send_email_alert(rule, device, metric_value, message, settings)
                    
                    if rule.notify_telegram and settings.get('telegram_enabled', False):
                        send_telegram_alert(rule, device, metric_value, message, settings)
                    
                    logger.info(f"Alert triggered: {rule.name} for device {device.name}")
            except Exception as e:
                logger.error(f"Error checking alert rule {rule.id}: {str(e)}")
    except Exception as e:
        logger.error(f"Error in alert check process: {str(e)}")

def generate_alert_message(rule, device, value):
    """Generate a default alert message"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    message = f"ALERT: {rule.name}\n"
    message += f"Device: {device.name} ({device.ip_address})\n"
    message += f"Metric: {rule.metric}\n"
    message += f"Condition: {rule.condition} {rule.threshold}\n"
    message += f"Current Value: {value}\n"
    message += f"Time: {timestamp}\n"
    
    return message

def send_email_alert(rule, device, value, message, settings):
    """Send alert via email"""
    try:
        # Get email settings
        mail_server = settings.get('mail_server')
        mail_port = int(settings.get('mail_port', 587))
        mail_use_tls = settings.get('mail_use_tls', True)
        mail_username = settings.get('mail_username')
        mail_password = settings.get('mail_password')
        mail_from = settings.get('mail_from')
        
        # Check if required settings are available
        if not all([mail_server, mail_username, mail_password, mail_from]):
            logger.error("Email settings are incomplete")
            return False
        
        # Parse recipients
        recipients = rule.email_recipients.split(',') if rule.email_recipients else [mail_username]
        recipients = [email.strip() for email in recipients if email.strip()]
        
        if not recipients:
            logger.error("No email recipients specified")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = mail_from
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = f"MikroTik Monitor Alert: {rule.name}"
        
        # Attach message
        msg.attach(MIMEText(message, 'plain'))
        
        # Send email
        with smtplib.SMTP(mail_server, mail_port) as server:
            if mail_use_tls:
                server.starttls()
            server.login(mail_username, mail_password)
            server.send_message(msg)
        
        logger.info(f"Email alert sent for {rule.name} to {', '.join(recipients)}")
        return True
    except Exception as e:
        logger.error(f"Error sending email alert: {str(e)}")
        return False

def send_telegram_alert(rule, device, value, message, settings):
    """Send alert via Telegram"""
    try:
        # Get Telegram settings
        bot_token = settings.get('telegram_bot_token')
        chat_id = settings.get('telegram_chat_id')
        
        # Check if required settings are available
        if not bot_token or not chat_id:
            logger.error("Telegram settings are incomplete")
            return False
        
        # Prepare API request
        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        # Send request
        response = requests.post(api_url, data=payload)
        
        if response.status_code == 200:
            logger.info(f"Telegram alert sent for {rule.name}")
            return True
        else:
            logger.error(f"Telegram API error: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error sending Telegram alert: {str(e)}")
        return False
