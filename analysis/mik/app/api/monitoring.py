from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from datetime import datetime, timedelta
from app.database.crud import (
    get_device_by_id,
    get_all_devices,
    get_metrics_for_device,
    get_recent_alerts,
    create_alert_rule,
    get_alert_rules,
    update_alert_rule,
    delete_alert_rule
)
from app.core.mikrotik import get_device_metrics, get_device_clients, get_interface_traffic
from app.utils.time_series import get_time_series_data

# Configure logger
logger = logging.getLogger(__name__)

# Create blueprint
monitoring_bp = Blueprint('monitoring_bp', __name__, url_prefix='/api/monitoring')

@monitoring_bp.route('/metrics/<int:device_id>', methods=['GET'])
@jwt_required()
def get_device_metrics_route(device_id):
    """Get current metrics for a device"""
    device = get_device_by_id(device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404
    
    try:
        metrics = get_device_metrics(device)
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error getting device metrics: {str(e)}")
        return jsonify({"error": f"Error getting device metrics: {str(e)}"}), 500

@monitoring_bp.route('/history/<int:device_id>', methods=['GET'])
@jwt_required()
def get_metrics_history(device_id):
    """Get historical metrics for a device"""
    device = get_device_by_id(device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404
    
    # Get query parameters
    metric = request.args.get('metric', 'cpu_load')
    hours = int(request.args.get('hours', 24))
    
    # Validate hours parameter
    if hours < 1 or hours > 168:  # Max 7 days
        return jsonify({"error": "Hours parameter must be between 1 and 168"}), 400
    
    # Define time range
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    try:
        # Get time series data
        data = get_time_series_data(device_id, metric, start_time, end_time)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error getting metrics history: {str(e)}")
        return jsonify({"error": f"Error getting metrics history: {str(e)}"}), 500

@monitoring_bp.route('/clients/<int:device_id>', methods=['GET'])
@jwt_required()
def get_clients_route(device_id):
    """Get clients connected to a device"""
    device = get_device_by_id(device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404
    
    try:
        clients = get_device_clients(device)
        return jsonify(clients)
    except Exception as e:
        logger.error(f"Error getting device clients: {str(e)}")
        return jsonify({"error": f"Error getting device clients: {str(e)}"}), 500

@monitoring_bp.route('/traffic/<int:device_id>', methods=['GET'])
@jwt_required()
def get_traffic_route(device_id):
    """Get interface traffic for a device"""
    device = get_device_by_id(device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404
    
    interface = request.args.get('interface')
    if not interface:
        return jsonify({"error": "Interface parameter is required"}), 400
    
    try:
        traffic = get_interface_traffic(device, interface)
        return jsonify(traffic)
    except Exception as e:
        logger.error(f"Error getting interface traffic: {str(e)}")
        return jsonify({"error": f"Error getting interface traffic: {str(e)}"}), 500

@monitoring_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_metrics():
    """Get summary metrics for dashboard"""
    try:
        devices = get_all_devices()
        summary = {
            "total_devices": len(devices),
            "online_devices": 0,
            "device_status": [],
            "recent_alerts": []
        }
        
        # Check status of each device
        for device in devices:
            try:
                metrics = get_device_metrics(device)
                online = metrics.get('online', False)
                
                device_status = {
                    "id": device.id,
                    "name": device.name,
                    "online": online,
                    "cpu_load": metrics.get('cpu_load', 0) if online else 0,
                    "memory_usage": metrics.get('memory_usage', 0) if online else 0,
                    "uptime": metrics.get('uptime', '') if online else ''
                }
                
                summary["device_status"].append(device_status)
                
                if online:
                    summary["online_devices"] += 1
            except Exception as e:
                logger.error(f"Error getting metrics for device {device.id}: {str(e)}")
                device_status = {
                    "id": device.id,
                    "name": device.name,
                    "online": False,
                    "cpu_load": 0,
                    "memory_usage": 0,
                    "uptime": ''
                }
                summary["device_status"].append(device_status)
        
        # Get recent alerts
        alerts = get_recent_alerts(limit=5)
        summary["recent_alerts"] = [alert.to_dict() for alert in alerts]
        
        return jsonify(summary)
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {str(e)}")
        return jsonify({"error": f"Error getting dashboard metrics: {str(e)}"}), 500

@monitoring_bp.route('/alerts', methods=['GET'])
@jwt_required()
def get_alerts():
    """Get recent alerts"""
    limit = int(request.args.get('limit', 20))
    
    # Validate limit parameter
    if limit < 1 or limit > 100:
        return jsonify({"error": "Limit parameter must be between 1 and 100"}), 400
    
    try:
        alerts = get_recent_alerts(limit=limit)
        return jsonify([alert.to_dict() for alert in alerts])
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        return jsonify({"error": f"Error getting alerts: {str(e)}"}), 500

@monitoring_bp.route('/alert-rules', methods=['GET'])
@jwt_required()
def get_alert_rules_route():
    """Get alert rules"""
    try:
        rules = get_alert_rules()
        return jsonify([rule.to_dict() for rule in rules])
    except Exception as e:
        logger.error(f"Error getting alert rules: {str(e)}")
        return jsonify({"error": f"Error getting alert rules: {str(e)}"}), 500

@monitoring_bp.route('/alert-rules', methods=['POST'])
@jwt_required()
def add_alert_rule():
    """Add a new alert rule"""
    data = request.json
    
    # Validate required fields
    required_fields = ['name', 'device_id', 'metric', 'condition', 'threshold', 'enabled']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Validate device exists
    device = get_device_by_id(data['device_id'])
    if not device:
        return jsonify({"error": "Device not found"}), 404
    
    # Validate metric
    valid_metrics = ['cpu_load', 'memory_usage', 'disk_usage', 'interface_traffic']
    if data['metric'] not in valid_metrics:
        return jsonify({"error": f"Invalid metric. Must be one of: {', '.join(valid_metrics)}"}), 400
    
    # Validate condition
    valid_conditions = ['>', '<', '>=', '<=', '==']
    if data['condition'] not in valid_conditions:
        return jsonify({"error": f"Invalid condition. Must be one of: {', '.join(valid_conditions)}"}), 400
    
    # Create alert rule
    try:
        rule = create_alert_rule(
            name=data['name'],
            device_id=data['device_id'],
            metric=data['metric'],
            condition=data['condition'],
            threshold=data['threshold'],
            duration=data.get('duration', 0),
            enabled=data['enabled'],
            notify_email=data.get('notify_email', False),
            notify_telegram=data.get('notify_telegram', False),
            email_recipients=data.get('email_recipients', ''),
            message_template=data.get('message_template', '')
        )
        return jsonify(rule.to_dict()), 201
    except Exception as e:
        logger.error(f"Error creating alert rule: {str(e)}")
        return jsonify({"error": f"Error creating alert rule: {str(e)}"}), 500

@monitoring_bp.route('/alert-rules/<int:rule_id>', methods=['PUT'])
@jwt_required()
def update_alert_rule_route(rule_id):
    """Update an alert rule"""
    data = request.json
    
    try:
        rule = update_alert_rule(
            rule_id,
            name=data.get('name'),
            device_id=data.get('device_id'),
            metric=data.get('metric'),
            condition=data.get('condition'),
            threshold=data.get('threshold'),
            duration=data.get('duration'),
            enabled=data.get('enabled'),
            notify_email=data.get('notify_email'),
            notify_telegram=data.get('notify_telegram'),
            email_recipients=data.get('email_recipients'),
            message_template=data.get('message_template')
        )
        
        if not rule:
            return jsonify({"error": "Alert rule not found"}), 404
            
        return jsonify(rule.to_dict())
    except Exception as e:
        logger.error(f"Error updating alert rule: {str(e)}")
        return jsonify({"error": f"Error updating alert rule: {str(e)}"}), 500

@monitoring_bp.route('/alert-rules/<int:rule_id>', methods=['DELETE'])
@jwt_required()
def delete_alert_rule_route(rule_id):
    """Delete an alert rule"""
    result = delete_alert_rule(rule_id)
    if not result:
        return jsonify({"error": "Alert rule not found"}), 404
    
    return jsonify({"message": "Alert rule deleted successfully"})

@monitoring_bp.route('/vpn/<int:device_id>', methods=['GET'])
@jwt_required()
def get_vpn_route(device_id):
    """Get VPN information for a device"""
    try:
        # Get device
        device = get_device_by_id(device_id)
        if not device:
            return jsonify({"error": "Device not found"}), 404
        
        # Get VPN data
        from app.core.vpn import get_vpn_stats
        vpn_data = get_vpn_stats(device)
        
        if not vpn_data:
            return jsonify({"error": "Failed to get VPN data"}), 500
        
        return jsonify(vpn_data)
        
    except Exception as e:
        logger.error(f"Error getting VPN data: {str(e)}")
        return jsonify({"error": f"Error getting VPN data: {str(e)}"}), 500
