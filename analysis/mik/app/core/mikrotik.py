import logging
import time
from librouteros import connect
from librouteros.query import Key
from librouteros.exceptions import ConnectionClosed, FatalError, LibRouterosError
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)

def connect_to_device(ip_address, username, password, port=8728):
    """Connect to MikroTik device via API"""
    try:
        api = connect(
            host=ip_address,
            username=username,
            password=password,
            port=port,
            timeout=10
        )
        return api
    except ConnectionClosed as e:
        logger.error(f"Connection closed to {ip_address}: {str(e)}")
        return None
    except FatalError as e:
        logger.error(f"Fatal error connecting to {ip_address}: {str(e)}")
        return None
    except LibRouterosError as e:
        logger.error(f"API error connecting to {ip_address}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error connecting to {ip_address}: {str(e)}")
        return None

def get_device_metrics(device):
    """Get current device metrics"""
    try:
        api = connect_to_device(device.ip_address, device.username, device.password)
        if not api:
            return {"online": False}
        
        # Get system resources
        resource = next(api.path('/system/resource').get())
        
        # Get identity
        identity = next(api.path('/system/identity').get())
        
        # Get health if available
        try:
            health = next(api.path('/system/health').get())
            temperature = health.get('temperature', 'N/A')
        except:
            temperature = 'N/A'
        
        # Process uptime
        uptime_seconds = resource.get('uptime', 0)
        uptime = format_uptime(uptime_seconds)
        
        # Prepare metrics
        metrics = {
            "online": True,
            "identity": identity.get('name', 'Unknown'),
            "model": resource.get('board-name', 'Unknown'),
            "cpu_count": resource.get('cpu-count', 1),
            "cpu_load": resource.get('cpu-load', 0),
            "cpu_frequency": resource.get('cpu-frequency', 0),
            "memory_total": resource.get('total-memory', 0),
            "memory_used": resource.get('total-memory', 0) - resource.get('free-memory', 0),
            "memory_usage": calculate_percentage(
                resource.get('total-memory', 0) - resource.get('free-memory', 0),
                resource.get('total-memory', 1)
            ),
            "disk_total": resource.get('total-hdd-space', 0),
            "disk_used": resource.get('total-hdd-space', 0) - resource.get('free-hdd-space', 0),
            "disk_usage": calculate_percentage(
                resource.get('total-hdd-space', 0) - resource.get('free-hdd-space', 0),
                resource.get('total-hdd-space', 1)
            ),
            "version": resource.get('version', 'Unknown'),
            "architecture": resource.get('architecture-name', 'Unknown'),
            "uptime": uptime,
            "uptime_seconds": uptime_seconds,
            "temperature": temperature,
            "timestamp": datetime.now().isoformat()
        }
        
        api.close()
        return metrics
    except Exception as e:
        logger.error(f"Error getting device metrics for {device.name}: {str(e)}")
        return {"online": False, "error": str(e)}

def get_device_clients(device):
    """Get clients connected to device"""
    try:
        api = connect_to_device(device.ip_address, device.username, device.password)
        if not api:
            return {"online": False}
        
        # Get wireless clients
        wireless_clients = []
        try:
            registrations = api.path('/interface/wireless/registration-table').get()
            for client in registrations:
                wireless_clients.append({
                    "mac_address": client.get('mac-address', ''),
                    "interface": client.get('interface', ''),
                    "signal_strength": client.get('signal-strength', ''),
                    "tx_rate": client.get('tx-rate', ''),
                    "rx_rate": client.get('rx-rate', ''),
                    "uptime": client.get('uptime', '')
                })
        except Exception as e:
            logger.error(f"Error getting wireless clients: {str(e)}")
        
        # Get DHCP leases
        dhcp_clients = []
        try:
            leases = api.path('/ip/dhcp-server/lease').get()
            for lease in leases:
                dhcp_clients.append({
                    "mac_address": lease.get('mac-address', ''),
                    "address": lease.get('address', ''),
                    "host_name": lease.get('host-name', ''),
                    "client_id": lease.get('client-id', ''),
                    "status": lease.get('status', '')
                })
        except Exception as e:
            logger.error(f"Error getting DHCP leases: {str(e)}")
        
        # Get CAPsMAN clients if available
        capsman_clients = []
        try:
            caps_registrations = api.path('/caps-man/registration-table').get()
            for client in caps_registrations:
                capsman_clients.append({
                    "mac_address": client.get('mac-address', ''),
                    "interface": client.get('interface', ''),
                    "signal_strength": client.get('signal-strength', ''),
                    "tx_rate": client.get('tx-rate', ''),
                    "rx_rate": client.get('rx-rate', ''),
                    "uptime": client.get('uptime', '')
                })
        except Exception:
            # CAPsMAN might not be available
            pass
        
        api.close()
        
        return {
            "online": True,
            "wireless_clients": wireless_clients,
            "dhcp_clients": dhcp_clients,
            "capsman_clients": capsman_clients,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting device clients for {device.name}: {str(e)}")
        return {"online": False, "error": str(e)}

def get_interface_traffic(device, interface_name=None):
    """Get interface traffic for a device"""
    try:
        api = connect_to_device(device.ip_address, device.username, device.password)
        if not api:
            return {"online": False}
        
        # Get interfaces
        interfaces = []
        if interface_name:
            # Get specific interface
            interface_path = api.path('/interface')
            params = {Key('name'): interface_name}
            interface_query = interface_path.select(**params)
            interfaces.extend(interface_query)
        else:
            # Get all interfaces
            interface_query = api.path('/interface').get()
            interfaces.extend(interface_query)
        
        # Process interface data
        interface_data = []
        for iface in interfaces:
            # Only include Ethernet and WLAN interfaces
            if iface.get('type') in ['ether', 'wlan']:
                interface_data.append({
                    "name": iface.get('name', ''),
                    "type": iface.get('type', ''),
                    "mac_address": iface.get('mac-address', ''),
                    "enabled": iface.get('disabled', 'true') == 'false',
                    "running": iface.get('running', 'false') == 'true',
                    "tx_byte": int(iface.get('tx-byte', 0)),
                    "rx_byte": int(iface.get('rx-byte', 0)),
                    "tx_packet": int(iface.get('tx-packet', 0)),
                    "rx_packet": int(iface.get('rx-packet', 0)),
                    "tx_drop": int(iface.get('tx-drop', 0)),
                    "rx_drop": int(iface.get('rx-drop', 0)),
                    "tx_error": int(iface.get('tx-error', 0)),
                    "rx_error": int(iface.get('rx-error', 0)),
                    "last_link_down": iface.get('last-link-down-time', ''),
                    "last_link_up": iface.get('last-link-up-time', '')
                })
        
        api.close()
        
        return {
            "online": True,
            "interfaces": interface_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting interface traffic for {device.name}: {str(e)}")
        return {"online": False, "error": str(e)}

def send_command_to_device(device, command):
    """Send a CLI command to device and return result"""
    try:
        api = connect_to_device(device.ip_address, device.username, device.password)
        if not api:
            return {"success": False, "message": "Could not connect to device"}
        
        # Parse command to determine path and action
        parts = command.strip().split()
        if len(parts) < 1:
            return {"success": False, "message": "Invalid command"}
        
        # Convert /ip/firewall/nat/print to path /ip/firewall/nat with action print
        path_parts = []
        action = None
        
        for part in parts:
            if part.startswith('/'):
                # It's the start of a path
                path_parts = part.strip('/').split('/')
            elif not action:
                # First non-path part is the action
                action = part
        
        if not path_parts:
            return {"success": False, "message": "Invalid command path"}
        
        # Build path
        path = '/' + '/'.join(path_parts)
        
        # Execute command
        try:
            if action == 'print':
                # Fetch data
                result = list(api.path(path).get())
                return {"success": True, "result": result}
            elif action in ['add', 'set', 'remove']:
                # Execute action with parameters
                # For simplicity, we're just returning success
                # In a real implementation, you'd need to parse the parameters
                return {"success": True, "message": f"Command executed: {command}"}
            else:
                return {"success": False, "message": f"Unsupported action: {action}"}
        except Exception as e:
            return {"success": False, "message": f"Error executing command: {str(e)}"}
        finally:
            api.close()
    except Exception as e:
        logger.error(f"Error sending command to {device.name}: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}

def backup_config(device):
    """Backup device configuration"""
    try:
        api = connect_to_device(device.ip_address, device.username, device.password)
        if not api:
            return None
        
        # Create backup
        backup_path = api.path('/system/backup')
        
        # Generate backup name with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{device.name}_{timestamp}"
        
        # Create backup
        backup_path.add(name=backup_name)
        
        # Wait for backup to be created
        time.sleep(2)
        
        # Get backup files
        files_path = api.path('/file')
        backup_files = [f for f in files_path.get() if f.get('name', '').endswith('.backup')]
        
        if not backup_files:
            api.close()
            return None
        
        # Use the latest backup file
        backup_file = sorted(backup_files, key=lambda x: x.get('creation-time', ''), reverse=True)[0]
        
        # Get file contents
        # In a real implementation, you would download the binary file
        # For this example, we'll just return the file info
        backup_info = {
            "name": backup_file.get('name', ''),
            "size": backup_file.get('size', 0),
            "creation_time": backup_file.get('creation-time', ''),
            "device_name": device.name,
            "device_id": device.id,
            "timestamp": timestamp
        }
        
        api.close()
        return backup_info
    except Exception as e:
        logger.error(f"Error backing up config for {device.name}: {str(e)}")
        return None

def restore_config(device, backup_data):
    """Restore device configuration from backup"""
    # This is a placeholder function
    # In a real implementation, you would upload the backup file and restore it
    try:
        api = connect_to_device(device.ip_address, device.username, device.password)
        if not api:
            return False
        
        # Simulate restore process
        logger.info(f"Restoring configuration for device {device.name}")
        time.sleep(2)
        
        api.close()
        return True
    except Exception as e:
        logger.error(f"Error restoring config for {device.name}: {str(e)}")
        return False

# Helper functions
def calculate_percentage(used, total):
    """Calculate percentage with error handling"""
    if total <= 0:
        return 0
    return round((used / total) * 100, 2)

def format_uptime(seconds):
    """Format uptime in seconds to a readable string"""
    if not seconds:
        return "Unknown"
    
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0 or days > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    
    return " ".join(parts)
