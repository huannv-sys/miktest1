import logging
import time
import re
from librouteros import connect
from librouteros.query import Key
from librouteros.exceptions import ConnectionClosed, FatalError, LibRouterosError
from datetime import datetime
from mik.app.utils.security import decrypt_device_password

# Configure logger
logger = logging.getLogger(__name__)

def connect_to_device(ip_address, username, password, port=8728, use_ssl=True, timeout=None):
    """Connect to MikroTik device via API
    
    Args:
        ip_address (str): Device IP address
        username (str): API username
        password (str): API password (may be encrypted)
        port (int): API port number
        use_ssl (bool): Whether to use SSL for connection
        timeout (int, optional): Connection timeout in seconds. Default from config.
        
    Returns:
        API connection object or None if connection failed
    """
    # Configuration
    from mik.app.config import Config
    default_timeout = getattr(Config, 'MIKROTIK_CONNECTION_TIMEOUT', 10)
    
    # Use configured timeout if not specified
    if timeout is None:
        timeout = default_timeout
    
    # Validate connection parameters before attempting connection
    if not ip_address or not username or not password:
        logger.error("Invalid connection parameters: IP, username, and password must be provided")
        return None
    
    # Limit timeout to reasonable values
    if not isinstance(timeout, (int, float)) or timeout < 1 or timeout > 60:
        logger.warning(f"Invalid timeout value: {timeout}, using default {default_timeout}")
        timeout = default_timeout
    
    # Check port range
    if not isinstance(port, int) or port < 1 or port > 65535:
        logger.error(f"Invalid port: {port}")
        return None
    
    api = None
    try:
        # If password is encrypted (from database), decrypt it
        decrypted_password = password
        if hasattr(password, 'startswith') and password.startswith('gAAAAA'):
            decrypted_password = decrypt_device_password(password)
            if not decrypted_password:
                logger.error(f"Failed to decrypt password for device at {ip_address}")
                return None
        
        # Connect to the device with timeout
        api = connect(
            host=ip_address,
            username=username,
            password=decrypted_password,
            port=port,
            timeout=timeout,
            ssl=use_ssl
        )
        return api
    except ConnectionClosed as e:
        logger.error(f"Connection closed to device at {ip_address}")
        return None
    except FatalError as e:
        logger.error(f"Fatal error connecting to device at {ip_address}")
        return None
    except LibRouterosError as e:
        # Don't log full exception which might contain credentials
        logger.error(f"API error connecting to device at {ip_address}: {e.__class__.__name__}")
        return None
    except Exception as e:
        # Log exception type but not full details which might contain sensitive data
        logger.error(f"Unexpected error connecting to device at {ip_address}: {e.__class__.__name__}")
        return None

def get_device_metrics(device):
    """Get current device metrics
    
    Args:
        device: Device object with connection parameters
        
    Returns:
        Dictionary with device metrics or offline status
    """
    # Input validation
    if not device or not hasattr(device, 'ip_address') or not device.ip_address:
        logger.error("Invalid device object provided to get_device_metrics")
        return {"online": False, "error": "Invalid device configuration"}
    
    # Avoid exposing full error details in response
    api = None
    
    try:
        # Get timeout from config
        from mik.app.config import Config
        timeout = getattr(Config, 'MIKROTIK_CONNECTION_TIMEOUT', 10)
        
        # Connect to device with proper timeout
        api = connect_to_device(
            device.ip_address, 
            device.username, 
            device.password_hash, 
            port=device.api_port, 
            use_ssl=device.use_ssl,
            timeout=timeout
        )
        
        if not api:
            logger.warning(f"Could not connect to device {device.name} at {device.ip_address}")
            return {"online": False, "error": "Connection failed"}
        
        # Use context-like pattern to ensure connection is closed
        try:
            # Get system resources with error handling
            try:
                resource = next(api.path('/system/resource').get())
            except Exception as e:
                logger.error(f"Failed to get system resources from {device.name}: {e.__class__.__name__}")
                return {"online": False, "error": "Failed to retrieve system resources"}
            
            # Get identity with error handling
            try:
                identity = next(api.path('/system/identity').get())
            except Exception as e:
                logger.error(f"Failed to get device identity from {device.name}: {e.__class__.__name__}")
                identity = {"name": "Unknown"}
            
            # Get health if available
            temperature = 'N/A'
            try:
                health = next(api.path('/system/health').get())
                temperature = health.get('temperature', 'N/A')
            except Exception:
                # Health monitoring might not be available on all devices
                pass
            
            # Process uptime safely
            uptime_seconds = resource.get('uptime', 0)
            uptime = format_uptime(uptime_seconds)
            
            # Safe memory calculations
            total_memory = resource.get('total-memory', 0)
            free_memory = resource.get('free-memory', 0)
            used_memory = 0
            
            if total_memory > 0 and free_memory <= total_memory:
                used_memory = total_memory - free_memory
            
            # Safe disk calculations
            total_disk = resource.get('total-hdd-space', 0)
            free_disk = resource.get('free-hdd-space', 0)
            used_disk = 0
            
            if total_disk > 0 and free_disk <= total_disk:
                used_disk = total_disk - free_disk
            
            # Prepare metrics
            metrics = {
                "online": True,
                "identity": identity.get('name', 'Unknown'),
                "model": resource.get('board-name', 'Unknown'),
                "cpu_count": resource.get('cpu-count', 1),
                "cpu_load": resource.get('cpu-load', 0),
                "cpu_frequency": resource.get('cpu-frequency', 0),
                "memory_total": total_memory,
                "memory_used": used_memory,
                "memory_usage": calculate_percentage(used_memory, total_memory),
                "disk_total": total_disk,
                "disk_used": used_disk,
                "disk_usage": calculate_percentage(used_disk, total_disk),
                "version": resource.get('version', 'Unknown'),
                "architecture": resource.get('architecture-name', 'Unknown'),
                "uptime": uptime,
                "uptime_seconds": uptime_seconds,
                "temperature": temperature,
                "timestamp": datetime.now().isoformat()
            }
            
            return metrics
        finally:
            # Always close the connection in the finally block
            if api:
                try:
                    api.close()
                except Exception as e:
                    logger.warning(f"Error closing API connection: {e.__class__.__name__}")
    
    except LibRouterosError as e:
        # Handle specific RouterOS API errors
        logger.error(f"RouterOS API error getting metrics for {device.name}: {e.__class__.__name__}")
        return {"online": False, "error": "RouterOS API error"}
    
    except ConnectionClosed as e:
        # Handle connection closed errors
        logger.error(f"Connection closed while getting metrics for {device.name}")
        return {"online": False, "error": "Connection closed unexpectedly"}
    
    except Exception as e:
        # Generic error handling
        logger.error(f"Error getting device metrics for {device.name}: {e.__class__.__name__}")
        # Don't expose internal error details to client
        return {"online": False, "error": "Failed to retrieve device metrics"}

def get_device_clients(device):
    """Get clients connected to device

    Args:
        device: Device object with connection parameters
        
    Returns:
        Dictionary with client information or offline status
    """
    # Input validation
    if not device or not hasattr(device, 'ip_address') or not device.ip_address:
        logger.error("Invalid device object provided to get_device_clients")
        return {"online": False, "error": "Invalid device configuration"}
    
    api = None
    
    try:
        # Get timeout from config for performance optimization
        from mik.app.config import Config
        timeout = getattr(Config, 'MIKROTIK_CONNECTION_TIMEOUT', 10)
        
        # Connect to device with proper timeout
        start_time = datetime.now()
        api = connect_to_device(
            device.ip_address, 
            device.username, 
            device.password_hash, 
            port=device.api_port, 
            use_ssl=device.use_ssl,
            timeout=timeout
        )
        
        if not api:
            logger.warning(f"Could not connect to device {device.name} at {device.ip_address}")
            return {"online": False, "error": "Connection failed"}
        
        # Prepare results containers
        result = {
            "online": True,
            "wireless_clients": [],
            "dhcp_clients": [],
            "capsman_clients": [],
            "timestamp": datetime.now().isoformat(),
            "performance": {}
        }
        
        # Use try-finally pattern to ensure connection is closed
        try:
            # Get clients with concurrent execution for performance
            tasks = [
                ('wireless_clients', _get_wireless_clients, api),
                ('dhcp_clients', _get_dhcp_clients, api),
                ('capsman_clients', _get_capsman_clients, api)
            ]
            
            # Execute data collection tasks
            for key, func, api_conn in tasks:
                try:
                    task_start = datetime.now()
                    result[key] = func(api_conn)
                    task_time = (datetime.now() - task_start).total_seconds()
                    # Track performance metrics
                    result["performance"][key] = task_time
                except Exception as e:
                    logger.error(f"Error collecting {key} from {device.name}: {e.__class__.__name__}")
                    result[key] = []
            
            # Calculate total execution time
            result["performance"]["total_time"] = (datetime.now() - start_time).total_seconds()
            
            # Remove performance metrics in production for security
            if not getattr(Config, 'DEBUG', False):
                del result["performance"]
                
            return result
        finally:
            # Always close the connection in the finally block
            if api:
                try:
                    api.close()
                except Exception as e:
                    logger.warning(f"Error closing API connection: {e.__class__.__name__}")
    
    except LibRouterosError as e:
        # Handle specific RouterOS API errors
        logger.error(f"RouterOS API error getting clients for {device.name}: {e.__class__.__name__}")
        return {"online": False, "error": "RouterOS API error"}
    
    except ConnectionClosed as e:
        # Handle connection closed errors
        logger.error(f"Connection closed while getting clients for {device.name}")
        return {"online": False, "error": "Connection closed unexpectedly"}
    
    except Exception as e:
        # Generic error handling
        logger.error(f"Error getting device clients for {device.name}: {e.__class__.__name__}")
        return {"online": False, "error": "Failed to retrieve device clients"}

# Helper functions for getting client data
def _get_wireless_clients(api):
    """Get wireless clients from device
    
    Args:
        api: Active API connection
        
    Returns:
        List of wireless clients
    """
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
        logger.error(f"Error getting wireless clients: {e.__class__.__name__}")
    
    return wireless_clients

def _get_dhcp_clients(api):
    """Get DHCP clients from device
    
    Args:
        api: Active API connection
        
    Returns:
        List of DHCP clients
    """
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
        logger.error(f"Error getting DHCP leases: {e.__class__.__name__}")
    
    return dhcp_clients

def _get_capsman_clients(api):
    """Get CAPsMAN clients from device
    
    Args:
        api: Active API connection
        
    Returns:
        List of CAPsMAN clients
    """
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
        # CAPsMAN might not be available, not an error
        pass
    
    return capsman_clients

def get_interface_traffic(device, interface_name=None, include_types=None):
    """Get interface traffic for a device
    
    Args:
        device: Device object with connection parameters
        interface_name (str, optional): Specific interface to query
        include_types (list, optional): Interface types to include (default: ['ether', 'wlan', 'bridge'])
        
    Returns:
        Dictionary with interface traffic data or offline status
    """
    # Input validation
    if not device or not hasattr(device, 'ip_address') or not device.ip_address:
        logger.error("Invalid device object provided to get_interface_traffic")
        return {"online": False, "error": "Invalid device configuration"}
    
    # Default interface types if not specified
    if include_types is None:
        include_types = ['ether', 'wlan', 'bridge']
    
    # Track API connection for cleanup
    api = None
    
    try:
        # Get timeout from config
        from mik.app.config import Config
        timeout = getattr(Config, 'MIKROTIK_CONNECTION_TIMEOUT', 10)
        
        # Start timing for performance metrics
        start_time = datetime.now()
        
        # Connect to device
        api = connect_to_device(
            device.ip_address, 
            device.username, 
            device.password_hash,
            port=device.api_port, 
            use_ssl=device.use_ssl,
            timeout=timeout
        )
        
        if not api:
            logger.warning(f"Could not connect to device {device.name} at {device.ip_address}")
            return {"online": False, "error": "Connection failed"}
        
        # Prepare result structure with performance tracking
        result = {
            "online": True,
            "interfaces": [],
            "timestamp": datetime.now().isoformat(),
            "performance": {
                "connection_time": (datetime.now() - start_time).total_seconds()
            }
        }
        
        # Use try-finally pattern to ensure connection is closed
        try:
            query_start_time = datetime.now()
            
            # Get interfaces
            interfaces = []
            if interface_name:
                # Get specific interface - more efficient
                try:
                    interface_path = api.path('/interface')
                    params = {Key('name'): interface_name}
                    interface_query = interface_path.select(**params)
                    interfaces.extend(interface_query)
                    
                    # If specific interface requested but not found, try case-insensitive match
                    if not interfaces:
                        all_interfaces = api.path('/interface').get()
                        interfaces = [
                            iface for iface in all_interfaces 
                            if iface.get('name', '').lower() == interface_name.lower()
                        ]
                except Exception as e:
                    logger.error(f"Error querying specific interface {interface_name}: {e.__class__.__name__}")
                    # Fall back to getting all interfaces if specific query fails
                    interface_query = api.path('/interface').get()
                    interfaces.extend(interface_query)
            else:
                # Get all interfaces
                interface_query = api.path('/interface').get()
                interfaces.extend(interface_query)
            
            # Record query time
            result["performance"]["query_time"] = (datetime.now() - query_start_time).total_seconds()
            
            # Efficient interface filtering and processing
            processing_start_time = datetime.now()
            interface_data = []
            
            # Create a map of interface types to help with speed selection
            interface_types = set(include_types)
            
            for iface in interfaces:
                interface_type = iface.get('type', '')
                
                # Only include interfaces of requested types
                if interface_type in interface_types:
                    # Safely convert numeric values with error handling
                    try:
                        tx_byte = int(iface.get('tx-byte', 0))
                    except (ValueError, TypeError):
                        tx_byte = 0
                        
                    try:
                        rx_byte = int(iface.get('rx-byte', 0))
                    except (ValueError, TypeError):
                        rx_byte = 0
                        
                    # Calculate speed in bits per second if possible
                    tx_rate_bps = 0
                    rx_rate_bps = 0
                    
                    # Process additional data for better information
                    disabled = iface.get('disabled', 'true')
                    # Handle different formats for boolean values
                    is_enabled = (disabled == 'false' or disabled is False)
                    
                    # Only enabled interfaces can be running
                    is_running = False
                    if is_enabled:
                        running = iface.get('running', 'false')
                        is_running = (running == 'true' or running is True)
                    
                    # Add interface to results
                    interface_data.append({
                        "name": iface.get('name', ''),
                        "type": interface_type,
                        "mac_address": iface.get('mac-address', ''),
                        "enabled": is_enabled,
                        "running": is_running,
                        "tx_byte": tx_byte,
                        "rx_byte": rx_byte,
                        "tx_packet": int(iface.get('tx-packet', 0)),
                        "rx_packet": int(iface.get('rx-packet', 0)),
                        "tx_drop": int(iface.get('tx-drop', 0)),
                        "rx_drop": int(iface.get('rx-drop', 0)),
                        "tx_error": int(iface.get('tx-error', 0)),
                        "rx_error": int(iface.get('rx-error', 0)),
                        "tx_rate_bps": tx_rate_bps,
                        "rx_rate_bps": rx_rate_bps,
                        "last_link_down": iface.get('last-link-down-time', ''),
                        "last_link_up": iface.get('last-link-up-time', '')
                    })
            
            # Record processing time
            result["performance"]["processing_time"] = (datetime.now() - processing_start_time).total_seconds()
            result["performance"]["total_time"] = (datetime.now() - start_time).total_seconds()
            
            # Set interfaces in result
            result["interfaces"] = interface_data
            
            # Calculate some aggregates if multiple interfaces
            if len(interface_data) > 0:
                result["total_interfaces"] = len(interface_data)
                result["active_interfaces"] = sum(1 for iface in interface_data if iface["running"])
                result["total_tx_bytes"] = sum(iface["tx_byte"] for iface in interface_data)
                result["total_rx_bytes"] = sum(iface["rx_byte"] for iface in interface_data)
            
            # Remove performance metrics in production
            if not getattr(Config, 'DEBUG', False):
                del result["performance"]
                
            return result
        finally:
            # Always close connection
            if api:
                try:
                    api.close()
                except Exception as e:
                    logger.warning(f"Error closing API connection: {e.__class__.__name__}")
    
    except LibRouterosError as e:
        # Handle specific RouterOS API errors
        logger.error(f"RouterOS API error for {device.name}: {e.__class__.__name__}")
        return {"online": False, "error": "RouterOS API error"}
    
    except ConnectionClosed as e:
        # Handle connection closed errors
        logger.error(f"Connection closed unexpectedly for {device.name}")
        return {"online": False, "error": "Connection closed unexpectedly"}
    
    except Exception as e:
        # Generic error handling that doesn't expose details
        logger.error(f"Error getting interface traffic for {device.name}: {e.__class__.__name__}")
        return {"online": False, "error": "Failed to retrieve interface data"}

def send_command_to_device(device, command):
    """Send a CLI command to device and return result
    
    Args:
        device: Device object with connection parameters
        command: MikroTik CLI command to execute
        
    Returns:
        Dictionary with command result or error message
    """
    # Security: validate command before processing
    if not command or not isinstance(command, str):
        return {"success": False, "message": "Empty or invalid command format"}
    
    # Sanitize and validate command
    command = command.strip()
    
    # Dangerous commands patterns - reject these for security
    dangerous_patterns = [
        r'/tool\s+fetch', 
        r'/tool\s+mac-server', 
        r'/ip\s+service\s+set',
        r'/ip\s+firewall\s+filter\s+remove',
        r'/system\s+reset-configuration',
        r'/system\s+shutdown',
        r'/system\s+reboot',
        r'/user\s+add',
        r'/user\s+remove',
        r'/user\s+set',
        r'/certificate\s+',
        r'/system\s+script\s+'
    ]
    
    # Check for dangerous commands
    for pattern in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            logger.warning(f"Blocked potentially dangerous command: {command}")
            return {"success": False, "message": "Command is not allowed for security reasons"}
    
    # Track connections to ensure proper cleanup
    api = None
    
    try:
        # Establish connection with proper timeout
        api = connect_to_device(
            device.ip_address, 
            device.username, 
            device.password_hash,
            port=device.api_port, 
            use_ssl=device.use_ssl,
            timeout=15  # Longer timeout for commands
        )
        
        if not api:
            return {"success": False, "message": "Could not connect to device"}
        
        # Parse command to determine path and action
        parts = command.split()
        if len(parts) < 1:
            return {"success": False, "message": "Invalid command format"}
        
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
        
        # Validate path parts (prevent directory traversal-like attacks)
        for part in path_parts:
            if not part or not re.match(r'^[a-zA-Z0-9\-_]+$', part):
                return {"success": False, "message": f"Invalid path component: {part}"}
        
        # Build path
        path = '/' + '/'.join(path_parts)
        
        # Limit allowed actions
        allowed_actions = ['print', 'find', 'get', 'export']
        if action and action not in allowed_actions:
            logger.warning(f"Blocked command with disallowed action: {action}")
            return {"success": False, "message": f"Action not allowed. Allowed actions: {', '.join(allowed_actions)}"}
        
        # Execute command with proper error handling
        try:
            # Only allow safe actions
            if action == 'print' or action == 'get' or action == 'find':
                # Fetch data with a timeout to prevent hanging
                result = list(api.path(path).get())
                
                # Limit result size for security and performance
                if len(result) > 1000:
                    logger.warning(f"Large result set from command: {command} - truncating")
                    result = result[:1000]
                    return {
                        "success": True, 
                        "result": result,
                        "warning": "Result set was truncated (max 1000 items)"
                    }
                
                return {"success": True, "result": result}
            elif action == 'export':
                # Safer alternative to some commands - export configuration
                result = list(api.path(path).get())
                return {"success": True, "result": result}
            else:
                return {"success": False, "message": "Unsupported action"}
        except LibRouterosError as e:
            # Specific API error, safe to log type
            logger.error(f"MikroTik API error executing command: {e.__class__.__name__}")
            return {"success": False, "message": f"MikroTik API error"}
        except Exception as e:
            # Generic error, don't expose details
            logger.error(f"Error executing command: {e.__class__.__name__}")
            return {"success": False, "message": "Error executing command"}
        finally:
            # Always close the connection
            if api:
                try:
                    api.close()
                except:
                    pass
    except Exception as e:
        # Log error details for diagnostics but don't return them to user
        logger.error(f"Error processing command for {device.name}: {e.__class__.__name__}")
        
        # Return generic error message to avoid exposing system details
        return {"success": False, "message": "Error processing command"}

def backup_config(device, max_retries=2):
    """Backup device configuration
    
    Args:
        device: Device object with connection parameters
        max_retries (int, optional): Maximum number of retry attempts if backup fails
        
    Returns:
        Dictionary with backup info or None if backup failed
    """
    # Input validation
    if not device or not hasattr(device, 'ip_address') or not device.ip_address:
        logger.error("Invalid device object provided to backup_config")
        return {"success": False, "error": "Invalid device configuration"}
    
    api = None
    retry_count = 0
    backup_start_time = datetime.now()
    
    # Implement retry logic for reliability
    while retry_count <= max_retries:
        try:
            # Get timeout from config for backup operations (longer timeout)
            from mik.app.config import Config
            timeout = getattr(Config, 'MIKROTIK_COMMAND_TIMEOUT', 15)
            
            # Connect to device
            api = connect_to_device(
                device.ip_address, 
                device.username, 
                device.password_hash,
                port=device.api_port, 
                use_ssl=device.use_ssl,
                timeout=timeout
            )
            
            if not api:
                logger.warning(f"Could not connect to device {device.name} at {device.ip_address} for backup")
                
                # Retry logic
                retry_count += 1
                if retry_count <= max_retries:
                    logger.info(f"Retrying backup for {device.name} (attempt {retry_count}/{max_retries})")
                    time.sleep(1)  # Wait before retry
                    continue
                else:
                    return {"success": False, "error": "Connection failed"}
            
            # Once connected, use try-finally to ensure proper cleanup
            try:
                # Check router version and capabilities to properly handle backup
                system_resource = next(api.path('/system/resource').get(), None)
                router_version = "unknown"
                if system_resource:
                    router_version = system_resource.get('version', 'unknown')
                    logger.info(f"Creating backup for RouterOS version: {router_version}")
                
                # Create backup with timeout handling
                backup_path = api.path('/system/backup')
                
                # Generate backup name with timestamp and sanitize
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                device_name_safe = re.sub(r'[^a-zA-Z0-9_\-]', '_', device.name)
                backup_name = f"{device_name_safe}_{timestamp}"
                
                # Create backup with error trapping
                try:
                    # Set operation timeout from config
                    backup_timeout = getattr(Config, 'MIKROTIK_BACKUP_TIMEOUT', 10)
                    
                    # Create backup operation
                    backup_path.add(name=backup_name)
                    
                    # Wait for backup to be created, but with adaptive timeout
                    max_wait = backup_timeout
                    wait_start = datetime.now()
                    backup_created = False
                    
                    # Adaptive wait with polling instead of fixed sleep
                    while (datetime.now() - wait_start).total_seconds() < max_wait:
                        # Check if backup file exists
                        files_path = api.path('/file')
                        try:
                            backup_files = [
                                f for f in files_path.get() 
                                if f.get('name', '').endswith('.backup') and backup_name in f.get('name', '')
                            ]
                            
                            if backup_files:
                                backup_created = True
                                break
                        except Exception as e:
                            logger.warning(f"Error checking backup status: {e.__class__.__name__}")
                        
                        # Wait a bit before retrying
                        time.sleep(0.5)
                    
                    if not backup_created:
                        logger.warning(f"Backup creation timeout for {device.name}")
                        raise TimeoutError("Backup creation timed out")
                
                except Exception as e:
                    logger.error(f"Failed to create backup: {e.__class__.__name__}")
                    
                    # Retry logic on backup creation failure
                    retry_count += 1
                    if retry_count <= max_retries:
                        logger.info(f"Retrying backup creation for {device.name} (attempt {retry_count}/{max_retries})")
                        time.sleep(1)
                        continue
                    else:
                        return {"success": False, "error": "Failed to create backup"}
                
                # Get backup files to find our newly created one
                files_path = api.path('/file')
                backup_files = [f for f in files_path.get() if f.get('name', '').endswith('.backup')]
                
                if not backup_files:
                    logger.error(f"No backup files found for {device.name}")
                    
                    # Retry on no backup files found
                    retry_count += 1
                    if retry_count <= max_retries:
                        logger.info(f"Retrying backup for {device.name} (attempt {retry_count}/{max_retries})")
                        time.sleep(1)
                        continue
                    else:
                        return {"success": False, "error": "No backup files found"}
                
                # Find our backup file by name pattern
                target_backup = None
                for backup_file in backup_files:
                    if backup_name in backup_file.get('name', ''):
                        target_backup = backup_file
                        break
                
                # If not found, use the latest backup file
                if not target_backup:
                    logger.warning(f"Specific backup '{backup_name}' not found, using latest backup")
                    target_backup = sorted(backup_files, key=lambda x: x.get('creation-time', ''), reverse=True)[0]
                
                # Calculate backup duration
                backup_duration = (datetime.now() - backup_start_time).total_seconds()
                
                # Prepare backup info
                backup_info = {
                    "success": True,
                    "name": target_backup.get('name', ''),
                    "size": target_backup.get('size', 0),
                    "creation_time": target_backup.get('creation-time', ''),
                    "device_name": device.name,
                    "device_id": device.id,
                    "router_version": router_version,
                    "timestamp": timestamp,
                    "backup_duration_seconds": backup_duration
                }
                
                # Log successful backup
                logger.info(f"Backup created successfully for {device.name}, size: {backup_info['size']} bytes")
                
                return backup_info
            finally:
                # Always close the connection
                if api:
                    try:
                        api.close()
                    except Exception as e:
                        logger.warning(f"Error closing API connection: {e.__class__.__name__}")
                        
        except LibRouterosError as e:
            # Handle specific RouterOS API errors
            logger.error(f"RouterOS API error backing up {device.name}: {e.__class__.__name__}")
            
            # Retry logic
            retry_count += 1
            if retry_count <= max_retries:
                logger.info(f"Retrying backup for {device.name} (attempt {retry_count}/{max_retries})")
                time.sleep(2)  # Slightly longer wait for API errors
            else:
                return {"success": False, "error": "RouterOS API error during backup"}
                
        except ConnectionClosed as e:
            # Handle connection closed errors
            logger.error(f"Connection closed while backing up {device.name}")
            
            # Retry on connection closed
            retry_count += 1
            if retry_count <= max_retries:
                logger.info(f"Retrying backup after connection closed for {device.name} (attempt {retry_count}/{max_retries})")
                time.sleep(1)
            else:
                return {"success": False, "error": "Connection closed during backup operation"}
            
        except Exception as e:
            # Generic error handling
            logger.error(f"Error backing up config for {device.name}: {e.__class__.__name__}")
            
            # Retry on general errors
            retry_count += 1
            if retry_count <= max_retries:
                logger.info(f"Retrying backup after error for {device.name} (attempt {retry_count}/{max_retries})")
                time.sleep(1)
            else:
                return {"success": False, "error": "Error during backup process"}
    
    # If we reach here, all retries failed
    logger.error(f"All backup attempts failed for {device.name}")
    return {"success": False, "error": "All backup attempts failed"}

def restore_config(device, backup_file_name, max_retries=2):
    """Restore device configuration from backup
    
    Args:
        device: Device object with connection parameters
        backup_file_name: Name of the backup file to restore
        max_retries (int, optional): Maximum number of retry attempts if restore fails
        
    Returns:
        Dictionary with restore status info
    """
    # Input validation
    if not device or not hasattr(device, 'ip_address') or not device.ip_address:
        logger.error("Invalid device object provided to restore_config")
        return {"success": False, "error": "Invalid device configuration"}
    
    if not backup_file_name:
        logger.error("Missing backup file name for restore operation")
        return {"success": False, "error": "Backup file name required"}
    
    # Sanitize backup file name for security
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', backup_file_name):
        logger.error(f"Invalid backup file name format: {backup_file_name}")
        return {"success": False, "error": "Invalid backup file name format"}
    
    # Ensure file has .backup extension
    if not backup_file_name.endswith('.backup'):
        backup_file_name += '.backup'
    
    api = None
    retry_count = 0
    restore_start_time = datetime.now()
    
    # Implement retry logic for reliability
    while retry_count <= max_retries:
        try:
            # Get timeout from config for restore operations (longer timeout)
            from mik.app.config import Config
            timeout = getattr(Config, 'MIKROTIK_COMMAND_TIMEOUT', 20)  # Longer timeout for restore
            
            # Connect to device
            api = connect_to_device(
                device.ip_address, 
                device.username, 
                device.password_hash,
                port=device.api_port, 
                use_ssl=device.use_ssl,
                timeout=timeout
            )
            
            if not api:
                logger.warning(f"Could not connect to device {device.name} at {device.ip_address} for restore")
                
                # Retry logic
                retry_count += 1
                if retry_count <= max_retries:
                    logger.info(f"Retrying connection for restore on {device.name} (attempt {retry_count}/{max_retries})")
                    time.sleep(2)  # Wait longer before retry for connection issues
                    continue
                else:
                    return {"success": False, "error": "Connection failed"}
            
            # Once connected, use try-finally to ensure proper cleanup
            try:
                # Check if the backup file exists
                logger.info(f"Looking for backup file: {backup_file_name}")
                files_path = api.path('/file')
                backup_files = list(files_path.get())
                
                # Find our backup file
                backup_file_exists = False
                for file in backup_files:
                    if file.get('name') == backup_file_name:
                        backup_file_exists = True
                        logger.info(f"Found backup file: {backup_file_name}")
                        break
                
                if not backup_file_exists:
                    logger.error(f"Backup file {backup_file_name} not found on device {device.name}")
                    return {"success": False, "error": f"Backup file not found on device"}
                
                # Start restore process with additional validation
                try:
                    # Get router info before restore for verification
                    pre_restore_info = {}
                    try:
                        system_resource = next(api.path('/system/resource').get(), None)
                        if system_resource:
                            pre_restore_info["version"] = system_resource.get('version', 'unknown')
                            pre_restore_info["board"] = system_resource.get('board-name', 'unknown')
                    except Exception as e:
                        logger.warning(f"Could not get pre-restore system info: {e.__class__.__name__}")
                    
                    # Set restore timeout from config
                    restore_timeout = getattr(Config, 'MIKROTIK_RESTORE_TIMEOUT', 120)  # Long timeout for restore
                    
                    # Perform the restore operation
                    logger.info(f"Starting restore process from {backup_file_name} on {device.name}")
                    
                    # Navigate to system restore path
                    restore_path = api.path('/system/restore')
                    
                    # Execute restore command
                    restore_path.add(name=backup_file_name)
                    
                    # Log the restore command initiation
                    logger.info(f"Restore command issued for {device.name}")
                    
                    # The device will likely reboot, so the connection will be closed
                    # We'll wait for the device to come back online
                    api.close()
                    api = None  # Prevent double-closing in finally block
                    
                    # Wait for device to go offline and come back online
                    logger.info(f"Waiting for {device.name} to restart after restore...")
                    
                    # First wait for device to go offline
                    offline_wait_start = datetime.now()
                    device_went_offline = False
                    
                    # Wait up to 30 seconds for device to go offline
                    while (datetime.now() - offline_wait_start).total_seconds() < 30:
                        try:
                            test_api = connect_to_device(
                                device.ip_address, 
                                device.username, 
                                device.password_hash,
                                port=device.api_port, 
                                use_ssl=device.use_ssl,
                                timeout=2  # Short timeout for offline check
                            )
                            if test_api:
                                test_api.close()
                                time.sleep(2)  # Wait before checking again
                            else:
                                device_went_offline = True
                                break
                        except:
                            device_went_offline = True
                            break
                    
                    if not device_went_offline:
                        logger.warning(f"Device {device.name} did not go offline during restore")
                    
                    # Now wait for device to come back online
                    logger.info(f"Waiting for {device.name} to come back online...")
                    
                    # Device should reboot, give it time to come back online
                    online_wait_start = datetime.now()
                    device_back_online = False
                    
                    # Try to reconnect multiple times over the restore timeout period
                    while (datetime.now() - online_wait_start).total_seconds() < restore_timeout:
                        try:
                            test_api = connect_to_device(
                                device.ip_address, 
                                device.username, 
                                device.password_hash,
                                port=device.api_port, 
                                use_ssl=device.use_ssl,
                                timeout=5  # Slightly longer timeout for reconnection
                            )
                            if test_api:
                                # Successfully reconnected
                                device_back_online = True
                                
                                # Check system info to verify restore
                                try:
                                    post_restore_info = {}
                                    system_resource = next(test_api.path('/system/resource').get(), None)
                                    if system_resource:
                                        post_restore_info["version"] = system_resource.get('version', 'unknown')
                                        post_restore_info["board"] = system_resource.get('board-name', 'unknown')
                                except Exception:
                                    # This is not critical, just informational
                                    logger.warning("Could not get post-restore system info")
                                
                                test_api.close()
                                break
                        except:
                            # Still offline, wait before trying again
                            time.sleep(5)
                    
                    if not device_back_online:
                        logger.error(f"Timeout waiting for {device.name} to come back online after restore")
                        return {
                            "success": False, 
                            "error": "Device did not come back online after restore",
                            "pre_restore_info": pre_restore_info
                        }
                    
                    # Restore completed
                    restore_duration = (datetime.now() - restore_start_time).total_seconds()
                    
                    return {
                        "success": True,
                        "message": f"Configuration restored successfully from {backup_file_name}",
                        "device_name": device.name,
                        "device_id": device.id,
                        "backup_file": backup_file_name,
                        "restore_duration_seconds": restore_duration,
                        "pre_restore_info": pre_restore_info,
                        "post_restore_info": post_restore_info if 'post_restore_info' in locals() else {}
                    }
                    
                except Exception as e:
                    logger.error(f"Error during restore process: {e.__class__.__name__}")
                    
                    # Retry logic on restore failure
                    retry_count += 1
                    if retry_count <= max_retries:
                        logger.info(f"Retrying restore for {device.name} (attempt {retry_count}/{max_retries})")
                        time.sleep(3)  # Wait longer between restore attempts
                        continue
                    else:
                        return {"success": False, "error": f"Restore process failed: {e.__class__.__name__}"}
                
            finally:
                # Always close connection if it's still open
                if api:
                    try:
                        api.close()
                    except Exception as e:
                        logger.warning(f"Error closing API connection: {e.__class__.__name__}")
                        
        except LibRouterosError as e:
            # Handle specific RouterOS API errors
            logger.error(f"RouterOS API error during restore on {device.name}: {e.__class__.__name__}")
            
            # Retry logic
            retry_count += 1
            if retry_count <= max_retries:
                logger.info(f"Retrying restore after API error for {device.name} (attempt {retry_count}/{max_retries})")
                time.sleep(3)
            else:
                return {"success": False, "error": "RouterOS API error during restore operation"}
                
        except ConnectionClosed as e:
            # Handle connection closed errors
            logger.error(f"Connection closed while restoring configuration for {device.name}")
            
            # During restore, connection closed might actually be expected due to reboot
            # Check if we're in the middle of the restore process
            elapsed_time = (datetime.now() - restore_start_time).total_seconds()
            if elapsed_time > 10:  # If we've been running for a while, might be a reboot
                logger.info(f"Connection closed after {elapsed_time}s - might be due to device reboot")
                
                # Wait for device to come back online
                time.sleep(30)  # Give device time to reboot
                
                try:
                    # Try to reconnect once more
                    test_api = connect_to_device(
                        device.ip_address, 
                        device.username, 
                        device.password_hash,
                        port=device.api_port, 
                        use_ssl=device.use_ssl,
                        timeout=10
                    )
                    if test_api:
                        # Successfully reconnected, restore might have worked
                        test_api.close()
                        return {
                            "success": True,
                            "message": "Restore appears to have succeeded (device rebooted and is back online)",
                            "device_name": device.name,
                            "device_id": device.id,
                            "backup_file": backup_file_name,
                            "restore_duration_seconds": (datetime.now() - restore_start_time).total_seconds(),
                            "warning": "Connection closed during restore, status inferred from reconnection"
                        }
                except:
                    pass
            
            # Retry logic for regular connection issues
            retry_count += 1
            if retry_count <= max_retries:
                logger.info(f"Retrying restore after connection closed for {device.name} (attempt {retry_count}/{max_retries})")
                time.sleep(5)  # Longer wait after connection closed
            else:
                return {"success": False, "error": "Connection issues during restore operation"}
            
        except Exception as e:
            # Generic error handling
            logger.error(f"Error restoring config for {device.name}: {e.__class__.__name__}")
            
            # Retry on general errors
            retry_count += 1
            if retry_count <= max_retries:
                logger.info(f"Retrying restore after error for {device.name} (attempt {retry_count}/{max_retries})")
                time.sleep(2)
            else:
                return {"success": False, "error": "Error during restore process"}
    
    # If we reach here, all retries failed
    logger.error(f"All restore attempts failed for {device.name}")
    return {"success": False, "error": "All restore attempts failed"}

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
