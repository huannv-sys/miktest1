import logging
import ipaddress
import socket
import concurrent.futures
from queue import Queue
import netifaces
import platform
import subprocess
import re
from app.core.mikrotik import connect_to_device, get_interface_traffic
from app.utils.network import validate_ip_address, check_port_open, validate_subnet, parse_mac_address

# Configure logger
logger = logging.getLogger(__name__)

def scan_network(subnet, max_workers=10):
    """Scan a network subnet for MikroTik devices"""
    try:
        # Validate subnet format
        if not validate_subnet(subnet):
            return {"error": "Invalid subnet format. Use CIDR notation (e.g., 192.168.1.0/24)"}
        
        network = ipaddress.ip_network(subnet, strict=False)
        
        # Queue for results
        result_queue = Queue()
        found_devices = []
        
        # Scan IPs in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(scan_ip, str(ip), result_queue) for ip in network.hosts()]
            concurrent.futures.wait(futures)
        
        # Collect results
        while not result_queue.empty():
            device = result_queue.get()
            if device:
                found_devices.append(device)
        
        return {"devices": found_devices}
        
    except Exception as e:
        logger.error(f"Error in network scan: {str(e)}")
        return {"error": f"Error in network scan: {str(e)}"}

def scan_ip(ip, result_queue):
    """Scan a single IP address for MikroTik device"""
    try:
        # Skip broadcast and network addresses
        if ip.endswith('.0') or ip.endswith('.255'):
            return None
        
        # Check if port 8728 (API) is open
        if not check_port_open(ip, 8728):
            if not check_port_open(ip, 80, timeout=1):  # Try HTTP port as fallback
                return None
        
        # Try to get hostname
        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except:
            hostname = "Unknown"
        
        # Get MAC address
        mac = get_mac_address(ip)
        
        # Return device info
        device = {
            "ip_address": ip,
            "hostname": hostname,
            "mac_address": mac if mac else "Unknown",
            "port_api": check_port_open(ip, 8728),
            "port_www": check_port_open(ip, 80),
            "port_winbox": check_port_open(ip, 8291)
        }
        
        result_queue.put(device)
        
    except Exception as e:
        logger.error(f"Error scanning IP {ip}: {str(e)}")
        return None

def get_mac_address(ip):
    """Get MAC address for an IP (platform specific)"""
    try:
        if platform.system() == "Windows":
            # Use arp on Windows
            p = subprocess.Popen(["arp", "-a", ip], stdout=subprocess.PIPE)
            output = p.stdout.read().decode('utf-8')
            matches = re.search(r'([0-9A-F]{2}[:-][0-9A-F]{2}[:-][0-9A-F]{2}[:-][0-9A-F]{2}[:-][0-9A-F]{2}[:-][0-9A-F]{2})', output, re.IGNORECASE)
            if matches:
                return matches.group(0)
        else:
            # Use arp on Linux/Unix/MacOS
            p = subprocess.Popen(["arp", "-n", ip], stdout=subprocess.PIPE)
            output = p.stdout.read().decode('utf-8')
            matches = re.search(r'([0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})', output, re.IGNORECASE)
            if matches:
                return matches.group(0)
        return None
    except Exception as e:
        logger.error(f"Error getting MAC address: {str(e)}")
        return None

def discover_topology(devices, all_devices=None):
    """Discover network topology between MikroTik devices"""
    try:
        if all_devices is None:
            all_devices = devices
            
        topology = []
        
        # Create mapping of IP to device ID
        ip_to_id = {device.ip_address: device.id for device in all_devices}
        
        for device in devices:
            try:
                # Connect to device
                api = connect_to_device(device.ip_address, device.username, device.password)
                if not api:
                    continue
                
                # Get ARP table
                arp_entries = api(cmd='/ip/arp/print')
                
                # Get interface addresses
                interfaces = api(cmd='/ip/address/print')
                interface_networks = {}
                
                # Map interfaces to networks
                for iface in interfaces:
                    if 'address' in iface:
                        # Parse CIDR notation (e.g., 192.168.1.1/24)
                        address_parts = iface['address'].split('/')
                        if len(address_parts) > 1:
                            ip = address_parts[0]
                            mask = int(address_parts[1])
                            try:
                                network = ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
                                interface_networks[iface.get('interface', 'unknown')] = {
                                    'network': str(network.network_address),
                                    'mask': mask,
                                    'ip': ip
                                }
                            except Exception as e:
                                logger.error(f"Error parsing interface address: {str(e)}")
                
                # Process ARP entries
                for entry in arp_entries:
                    target_ip = entry.get('address')
                    
                    # Check if IP belongs to another monitored device
                    if target_ip in ip_to_id and ip_to_id[target_ip] != device.id:
                        target_id = ip_to_id[target_ip]
                        interface_name = entry.get('interface', 'unknown')
                        
                        # Find interface network
                        network_info = interface_networks.get(interface_name, {})
                        
                        # Create link
                        link = {
                            'source_id': device.id,
                            'target_id': target_id,
                            'source_interface': interface_name,
                            'source_ip': network_info.get('ip'),
                            'target_ip': target_ip
                        }
                        
                        # Check if link already exists (in reverse direction)
                        existing_link = False
                        for existing in topology:
                            if existing['source_id'] == target_id and existing['target_id'] == device.id:
                                existing_link = True
                                # Update with reverse info
                                existing['target_interface'] = interface_name
                                break
                        
                        if not existing_link:
                            topology.append(link)
                
                # Check routing table for additional links
                routes = api(cmd='/ip/route/print')
                for route in routes:
                    if 'gateway' in route:
                        gateway = route['gateway']
                        if gateway in ip_to_id and ip_to_id[gateway] != device.id:
                            target_id = ip_to_id[gateway]
                            
                            # Check if link already exists
                            existing_link = False
                            for existing in topology:
                                if (existing['source_id'] == device.id and existing['target_id'] == target_id) or \
                                   (existing['source_id'] == target_id and existing['target_id'] == device.id):
                                    existing_link = True
                                    break
                            
                            if not existing_link:
                                link = {
                                    'source_id': device.id,
                                    'target_id': target_id,
                                    'source_interface': route.get('interface', 'unknown'),
                                    'source_ip': None,  # We don't know the exact source IP
                                    'target_ip': gateway
                                }
                                topology.append(link)
                
            except Exception as e:
                logger.error(f"Error discovering topology for device {device.name}: {str(e)}")
        
        return topology
        
    except Exception as e:
        logger.error(f"Error in topology discovery: {str(e)}")
        return []