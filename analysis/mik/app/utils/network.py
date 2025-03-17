import socket
import ipaddress
import logging
import re

# Configure logger
logger = logging.getLogger(__name__)

def validate_ip_address(ip):
    """Validate IP address format"""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def validate_subnet(subnet):
    """Validate subnet format"""
    try:
        ipaddress.ip_network(subnet)
        return True
    except ValueError:
        return False

def check_port_open(ip, port, timeout=2):
    """Check if a port is open on a host"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except Exception as e:
        logger.error(f"Error checking port {port} on {ip}: {str(e)}")
        return False

def check_host_reachable(ip, timeout=2):
    """Check if a host is reachable (ping)"""
    try:
        # Try to establish a connection to port 7 (echo)
        return check_port_open(ip, 7, timeout) or check_port_open(ip, 80, timeout)
    except Exception as e:
        logger.error(f"Error checking host reachability {ip}: {str(e)}")
        return False

def get_network_interfaces():
    """Get local network interfaces"""
    try:
        import netifaces
        interfaces = []
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    interfaces.append({
                        'name': iface,
                        'ip': addr['addr'],
                        'netmask': addr.get('netmask', ''),
                        'broadcast': addr.get('broadcast', '')
                    })
        return interfaces
    except ImportError:
        logger.warning("netifaces module not available")
        return []
    except Exception as e:
        logger.error(f"Error getting network interfaces: {str(e)}")
        return []

def parse_mac_address(mac):
    """Parse and normalize MAC address format"""
    if not mac:
        return None
    
    # Remove all non-hex characters
    mac = re.sub(r'[^0-9a-fA-F]', '', mac)
    
    # Check if we have 12 hex digits
    if len(mac) != 12:
        return None
    
    # Format as XX:XX:XX:XX:XX:XX
    return ':'.join(mac[i:i+2] for i in range(0, 12, 2)).upper()
