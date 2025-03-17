from flask import Blueprint, request, jsonify, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from app.database.crud import (
    get_all_devices, 
    get_device_by_id, 
    create_device, 
    update_device,
    delete_device
)
from app.core.mikrotik import connect_to_device, get_device_metrics, backup_config
from app.core.discovery import scan_network
from app.utils.network import validate_ip_address

# Configure logger
logger = logging.getLogger(__name__)

# Create blueprint
devices_bp = Blueprint('devices_bp', __name__, url_prefix='/api/devices')

@devices_bp.route('/', methods=['GET'])
@jwt_required()
def get_devices():
    """Get all devices"""
    devices = get_all_devices()
    return jsonify([device.to_dict() for device in devices])

@devices_bp.route('/<int:device_id>', methods=['GET'])
@jwt_required()
def get_device(device_id):
    """Get a specific device"""
    device = get_device_by_id(device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404
    return jsonify(device.to_dict())

@devices_bp.route('/', methods=['POST'])
@jwt_required()
def add_device():
    """Add a new device"""
    data = request.json
    
    # Validate required fields
    required_fields = ['name', 'ip_address', 'username', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Validate IP address
    if not validate_ip_address(data['ip_address']):
        return jsonify({"error": "Invalid IP address"}), 400
    
    # Test connection before saving
    try:
        api = connect_to_device(
            data['ip_address'], 
            data['username'], 
            data['password']
        )
        if not api:
            return jsonify({"error": "Unable to connect to device"}), 400
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")
        return jsonify({"error": f"Connection error: {str(e)}"}), 400
    
    # Create device
    try:
        device = create_device(
            name=data['name'],
            ip_address=data['ip_address'],
            username=data['username'],
            password=data['password'],
            api_port=data.get('api_port', 8728),
            use_ssl=data.get('use_ssl', False),
            model=data.get('model', 'Unknown'),
            location=data.get('location', ''),
            notes=data.get('notes', '')
        )
        return jsonify(device.to_dict()), 201
    except Exception as e:
        logger.error(f"Error creating device: {str(e)}")
        return jsonify({"error": f"Error creating device: {str(e)}"}), 500

@devices_bp.route('/<int:device_id>', methods=['PUT'])
@jwt_required()
def update_device_route(device_id):
    """Update a device"""
    device = get_device_by_id(device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404
    
    data = request.json
    
    # If IP, username or password has changed, verify connection
    if (data.get('ip_address') and data['ip_address'] != device.ip_address) or \
       (data.get('username') and data['username'] != device.username) or \
       (data.get('password') and data['password'] != device.password):
        
        ip = data.get('ip_address', device.ip_address)
        username = data.get('username', device.username)
        password = data.get('password', device.password)
        
        # Validate IP address
        if not validate_ip_address(ip):
            return jsonify({"error": "Invalid IP address"}), 400
        
        # Test connection
        try:
            api = connect_to_device(ip, username, password)
            if not api:
                return jsonify({"error": "Unable to connect to device with new credentials"}), 400
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            return jsonify({"error": f"Connection error: {str(e)}"}), 400
    
    # Update device
    try:
        updated_device = update_device(
            device_id,
            name=data.get('name'),
            ip_address=data.get('ip_address'),
            username=data.get('username'),
            password=data.get('password'),
            api_port=data.get('api_port'),
            use_ssl=data.get('use_ssl'),
            model=data.get('model'),
            location=data.get('location'),
            notes=data.get('notes')
        )
        return jsonify(updated_device.to_dict())
    except Exception as e:
        logger.error(f"Error updating device: {str(e)}")
        return jsonify({"error": f"Error updating device: {str(e)}"}), 500

@devices_bp.route('/<int:device_id>', methods=['DELETE'])
@jwt_required()
def delete_device_route(device_id):
    """Delete a device"""
    device = get_device_by_id(device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404
    
    try:
        delete_device(device_id)
        return jsonify({"message": "Device deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting device: {str(e)}")
        return jsonify({"error": f"Error deleting device: {str(e)}"}), 500

@devices_bp.route('/<int:device_id>/metrics', methods=['GET'])
@jwt_required()
def get_metrics(device_id):
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

@devices_bp.route('/<int:device_id>/backup', methods=['GET'])
@jwt_required()
def backup_device_config(device_id):
    """Backup device configuration"""
    device = get_device_by_id(device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404
    
    try:
        backup_data = backup_config(device)
        if backup_data:
            return jsonify({"backup": backup_data})
        else:
            return jsonify({"error": "Failed to backup device configuration"}), 500
    except Exception as e:
        logger.error(f"Error backing up device configuration: {str(e)}")
        return jsonify({"error": f"Error backing up device configuration: {str(e)}"}), 500

@devices_bp.route('/scan', methods=['POST'])
@jwt_required()
def scan_for_devices():
    """Scan network for MikroTik devices"""
    data = request.json
    
    subnet = data.get('subnet')
    if not subnet:
        return jsonify({"error": "Subnet is required"}), 400
    
    try:
        devices = scan_network(subnet)
        return jsonify({"devices": devices})
    except Exception as e:
        logger.error(f"Error scanning network: {str(e)}")
        return jsonify({"error": f"Error scanning network: {str(e)}"}), 500

@devices_bp.route('/<int:device_id>/command', methods=['POST'])
@jwt_required()
def send_command(device_id):
    """Send CLI command to device"""
    device = get_device_by_id(device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404
    
    data = request.json
    command = data.get('command')
    
    if not command:
        return jsonify({"error": "Command is required"}), 400
    
    try:
        from app.core.mikrotik import send_command_to_device
        result = send_command_to_device(device, command)
        return jsonify({"result": result})
    except Exception as e:
        logger.error(f"Error sending command: {str(e)}")
        return jsonify({"error": f"Error sending command: {str(e)}"}), 500
