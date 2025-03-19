import logging
from librouteros import connect
from librouteros.exceptions import *
from datetime import datetime

def get_device_connection(device):
    """
    Tạo kết nối đến thiết bị MikroTik
    
    Args:
        device: Device object chứa thông tin kết nối
        
    Returns:
        API connection object hoặc None nếu kết nối thất bại
    """
    try:
        # Thử kết nối đến thiết bị
        api = connect(
            username=device.username,
            password=device.password,
            host=device.ip_address,
            port=device.port
        )
        return api
    except Exception as e:
        logging.error(f"Error connecting to device {device.name}: {str(e)}")
        return None

def get_system_info(api):
    """
    Lấy thông tin hệ thống từ thiết bị
    
    Args:
        api: API connection object
        
    Returns:
        Dict chứa thông tin hệ thống hoặc None nếu có lỗi
    """
    try:
        # Lấy thông tin hệ thống
        identity = api(cmd="/system/identity/print")[0]
        resource = api(cmd="/system/resource/print")[0]
        
        return {
            'identity': identity.get('name', 'Unknown'),
            'model': resource.get('board-name', 'Unknown'),
            'version': resource.get('version', 'Unknown'),
            'cpu_load': resource.get('cpu-load', 0),
            'memory_used': calculate_memory_usage(resource),
            'uptime': resource.get('uptime', '0s')
        }
    except Exception as e:
        logging.error(f"Error getting system info: {str(e)}")
        return None

def get_interfaces(api):
    """
    Lấy danh sách interface từ thiết bị
    
    Args:
        api: API connection object
        
    Returns:
        List các interface hoặc None nếu có lỗi
    """
    try:
        # Lấy danh sách interface
        interfaces = api(cmd="/interface/print")
        
        result = []
        for iface in interfaces:
            result.append({
                'name': iface.get('name', 'Unknown'),
                'type': iface.get('type', 'Unknown'),
                'mac_address': iface.get('mac-address', 'Unknown'),
                'running': iface.get('running', False),
                'disabled': iface.get('disabled', True)
            })
            
        return result
    except Exception as e:
        logging.error(f"Error getting interfaces: {str(e)}")
        return None

def get_device_clients(api):
    """
    Lấy danh sách client kết nối đến thiết bị
    
    Args:
        api: API connection object
        
    Returns:
        Dict chứa danh sách client từ các nguồn khác nhau
    """
    try:
        result = {
            'dhcp': get_dhcp_clients(api),
            'wireless': get_wireless_clients(api),
            'hotspot': get_hotspot_clients(api)
        }
        return result
    except Exception as e:
        logging.error(f"Error getting device clients: {str(e)}")
        return None

def get_dhcp_clients(api):
    """Lấy danh sách DHCP client"""
    try:
        clients = api(cmd="/ip/dhcp-server/lease/print")
        return [{
            'mac_address': client.get('mac-address', 'Unknown'),
            'address': client.get('address', 'Unknown'),
            'host_name': client.get('host-name', 'Unknown'),
            'server': client.get('server', 'Unknown'),
            'status': client.get('status', 'Unknown')
        } for client in clients]
    except Exception as e:
        logging.error(f"Error getting DHCP clients: {str(e)}")
        return []

def get_wireless_clients(api):
    """Lấy danh sách Wireless client"""
    try:
        clients = api(cmd="/interface/wireless/registration-table/print")
        return [{
            'mac_address': client.get('mac-address', 'Unknown'),
            'interface': client.get('interface', 'Unknown'),
            'signal_strength': client.get('signal-strength', 'Unknown'),
            'tx_rate': client.get('tx-rate', 'Unknown'),
            'rx_rate': client.get('rx-rate', 'Unknown'),
            'uptime': client.get('uptime', 'Unknown')
        } for client in clients]
    except Exception as e:
        logging.error(f"Error getting wireless clients: {str(e)}")
        return []

def get_hotspot_clients(api):
    """Lấy danh sách Hotspot client"""
    try:
        clients = api(cmd="/ip/hotspot/active/print")
        return [{
            'user': client.get('user', 'Unknown'),
            'address': client.get('address', 'Unknown'),
            'mac_address': client.get('mac-address', 'Unknown'),
            'uptime': client.get('uptime', 'Unknown'),
            'session_time_left': client.get('session-time-left', 'Unknown')
        } for client in clients]
    except Exception as e:
        logging.error(f"Error getting hotspot clients: {str(e)}")
        return []

def calculate_memory_usage(resource):
    """Tính % sử dụng memory"""
    try:
        total = int(resource.get('total-memory', 0))
        free = int(resource.get('free-memory', 0))
        if total > 0:
            return round(((total - free) / total) * 100, 2)
        return 0
    except:
        return 0

def update_device_status(device):
    """
    Cập nhật trạng thái thiết bị
    
    Args:
        device: Device object cần cập nhật
        
    Returns:
        bool: True nếu thiết bị online, False nếu offline
    """
    try:
        # Thử kết nối đến thiết bị
        api = get_device_connection(device)
        if api:
            # Lấy thông tin hệ thống để xác nhận thiết bị hoạt động
            system_info = get_system_info(api)
            if system_info:
                device.status = 'online'
                device.last_check = datetime.utcnow()
                return True
                
        device.status = 'offline'
        device.last_check = datetime.utcnow()
        return False
    except Exception as e:
        logging.error(f"Error updating device status: {str(e)}")
        device.status = 'error'
        device.last_check = datetime.utcnow()
        return False