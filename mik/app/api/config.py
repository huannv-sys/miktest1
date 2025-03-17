from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from mik.app.database.crud import (
    get_device_by_id,
    get_settings,
    update_settings,
    get_user_by_username
)
from mik.app.core.mikrotik import (
    send_command_to_device,
    backup_config,
    restore_config
)

# Configure logger
logger = logging.getLogger(__name__)

# Create blueprint
config_bp = Blueprint('config_bp', __name__, url_prefix='/api/config')

@config_bp.route('/command/<int:device_id>', methods=['POST'])
@jwt_required()
def send_command_route(device_id):
    """Send CLI command to device"""
    device = get_device_by_id(device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404
    
    data = request.json
    command = data.get('command')
    
    if not command:
        return jsonify({"error": "Command is required"}), 400
    
    try:
        result = send_command_to_device(device, command)
        return jsonify({"result": result})
    except Exception as e:
        logger.error(f"Error sending command: {str(e)}")
        return jsonify({"error": f"Error sending command: {str(e)}"}), 500

@config_bp.route('/backup/<int:device_id>', methods=['GET'])
@jwt_required()
def backup_device_config(device_id):
    """Backup device configuration"""
    device = get_device_by_id(device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404
    
    try:
        backup_data = backup_config(device)
        if backup_data:
            # Return backup as JSON
            return jsonify({"backup": backup_data})
        else:
            return jsonify({"error": "Failed to backup device configuration"}), 500
    except Exception as e:
        logger.error(f"Error backing up device configuration: {str(e)}")
        return jsonify({"error": f"Error backing up device configuration: {str(e)}"}), 500

@config_bp.route('/restore/<int:device_id>', methods=['POST'])
@jwt_required()
def restore_device_config(device_id):
    """Restore device configuration"""
    device = get_device_by_id(device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404
    
    data = request.json
    backup_data = data.get('backup')
    
    if not backup_data:
        return jsonify({"error": "Backup data is required"}), 400
    
    try:
        result = restore_config(device, backup_data)
        if result:
            return jsonify({"message": "Configuration restored successfully"})
        else:
            return jsonify({"error": "Failed to restore device configuration"}), 500
    except Exception as e:
        logger.error(f"Error restoring device configuration: {str(e)}")
        return jsonify({"error": f"Error restoring device configuration: {str(e)}"}), 500

@config_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_app_settings():
    """Get application settings"""
    current_user = get_jwt_identity()
    
    # Check if user is admin
    user = get_user_by_username(current_user)
    
    if not user or user.role != 'admin':
        return jsonify({"error": "Admin privileges required"}), 403
    
    try:
        settings = get_settings()
        return jsonify(settings)
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}")
        return jsonify({"error": f"Error getting settings: {str(e)}"}), 500

@config_bp.route('/settings', methods=['PUT'])
@jwt_required()
def update_app_settings():
    """Update application settings"""
    current_user = get_jwt_identity()
    
    # Check if user is admin
    user = get_user_by_username(current_user)
    
    if not user or user.role != 'admin':
        return jsonify({"error": "Admin privileges required"}), 403
    
    data = request.json
    
    try:
        settings = update_settings(data)
        return jsonify(settings)
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        return jsonify({"error": f"Error updating settings: {str(e)}"}), 500