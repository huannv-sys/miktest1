from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from app.database.crud import get_all_devices, get_device_by_id
from app.core.discovery import discover_topology
from app.utils.network import validate_subnet
import traceback

# Configure logger
logger = logging.getLogger(__name__)

# Create blueprint
topology_bp = Blueprint('topology_bp', __name__, url_prefix='/api/topology')

@topology_bp.route('/map', methods=['GET'])
@jwt_required()
def get_network_map():
    """Get network topology map data"""
    try:
        # Get all devices
        devices = get_all_devices()
        device_list = [device.to_dict() for device in devices]
        
        # Discover topology
        topology_data = discover_topology(devices)
        
        # Format response
        response = {
            "nodes": [],
            "links": []
        }
        
        # Add nodes (devices)
        for device in device_list:
            node = {
                "id": device["id"],
                "name": device["name"],
                "ip_address": device["ip_address"],
                "type": "router",
                "model": device.get("model", "Unknown"),
                "group": 1  # Default group
            }
            response["nodes"].append(node)
        
        # Add links from topology data
        for link in topology_data:
            response["links"].append({
                "source": link["source_id"],
                "target": link["target_id"],
                "value": link.get("bandwidth", 1),  # Link thickness based on bandwidth
                "interface_name": link.get("interface_name", "")
            })
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error generating network map: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Error generating network map: {str(e)}"}), 500

@topology_bp.route('/neighbors/<int:device_id>', methods=['GET'])
@jwt_required()
def get_device_neighbors(device_id):
    """Get neighbors for a specific device"""
    try:
        # Get device
        device = get_device_by_id(device_id)
        if not device:
            return jsonify({"error": "Device not found"}), 404
        
        # Get all devices
        all_devices = get_all_devices()
        
        # Discover topology focusing on this device
        topology_data = discover_topology([device], all_devices)
        
        # Format response to include device details
        neighbors = []
        for link in topology_data:
            # If this device is the source
            if link["source_id"] == device_id:
                target_device = get_device_by_id(link["target_id"])
                if target_device:
                    neighbors.append({
                        "device_id": target_device.id,
                        "name": target_device.name,
                        "ip_address": target_device.ip_address,
                        "interface": link.get("source_interface", ""),
                        "remote_interface": link.get("target_interface", "")
                    })
            # If this device is the target
            elif link["target_id"] == device_id:
                source_device = get_device_by_id(link["source_id"])
                if source_device:
                    neighbors.append({
                        "device_id": source_device.id,
                        "name": source_device.name,
                        "ip_address": source_device.ip_address,
                        "interface": link.get("target_interface", ""),
                        "remote_interface": link.get("source_interface", "")
                    })
        
        return jsonify(neighbors)
    
    except Exception as e:
        logger.error(f"Error getting device neighbors: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Error getting device neighbors: {str(e)}"}), 500