import logging
from datetime import datetime
from librouteros import connect
from librouteros import exceptions as routeros_exceptions
from mik.app.utils.security import decrypt_device_password

# Set up logger
logger = logging.getLogger(__name__)

def get_vpn_stats(device):
    """
    Get VPN statistics from a MikroTik device
    
    Args:
        device: Device object with connection parameters
        
    Returns:
        Dictionary containing VPN statistics and configuration
    """
    try:
        # Connect to the device using device's port settings
        api = connect(
            username=device.username,
            password=device.password,
            host=device.ip_address,
            port=device.api_port,
            ssl=device.use_ssl
        )
        
        # Get active connections (PPTP, L2TP, SSTP)
        active_connections = []
        
        # Get PPTP active connections
        pptp_active = []
        try:
            pptp_active = list(api.path('/interface/pptp-server/active').select('*').where(
                'uptime', '>', '00:00:00'
            ))
            for conn in pptp_active:
                conn['type'] = 'pptp'
                conn['service'] = 'PPTP'
                active_connections.append(conn)
        except routeros_exceptions.RouterOsApiConnectionError as e:
            logger.warning(f"Error getting PPTP connections: {str(e)}")
        except (KeyError, ValueError) as e:
            logger.warning(f"Error processing PPTP data: {str(e)}")
            
        # Get L2TP active connections
        l2tp_active = []
        try:
            l2tp_active = list(api.path('/interface/l2tp-server/active').select('*').where(
                'uptime', '>', '00:00:00'
            ))
            for conn in l2tp_active:
                conn['type'] = 'l2tp'
                conn['service'] = 'L2TP'
                active_connections.append(conn)
        except routeros_exceptions.RouterOsApiConnectionError as e:
            logger.warning(f"Error getting L2TP connections: {str(e)}")
        except (KeyError, ValueError) as e:
            logger.warning(f"Error processing L2TP data: {str(e)}")
            
        # Get SSTP active connections
        sstp_active = []
        try:
            sstp_active = list(api.path('/interface/sstp-server/active').select('*').where(
                'uptime', '>', '00:00:00'
            ))
            for conn in sstp_active:
                conn['type'] = 'sstp'
                conn['service'] = 'SSTP'
                active_connections.append(conn)
        except routeros_exceptions.RouterOsApiConnectionError as e:
            logger.warning(f"Error getting SSTP connections: {str(e)}")
        except (KeyError, ValueError) as e:
            logger.warning(f"Error processing SSTP data: {str(e)}")
            
        # Get OpenVPN active connections
        ovpn_active = []
        try:
            ovpn_active = list(api.path('/interface/ovpn-server/active').select('*').where(
                'uptime', '>', '00:00:00'
            ))
            for conn in ovpn_active:
                conn['type'] = 'ovpn'
                conn['service'] = 'OpenVPN'
                active_connections.append(conn)
        except routeros_exceptions.RouterOsApiConnectionError as e:
            logger.warning(f"Error getting OpenVPN connections: {str(e)}")
        except (KeyError, ValueError) as e:
            logger.warning(f"Error processing OpenVPN data: {str(e)}")
            
        # Get IPsec active connections (more complex - peer data)
        ipsec_active = []
        try:
            ipsec_peers = list(api.path('/ip/ipsec/active-peers').select('*'))
            for peer in ipsec_peers:
                peer['type'] = 'ipsec'
                peer['service'] = 'IPsec'
                # Convert some fields for consistency
                if 'local-address' in peer:
                    peer['local_address'] = peer.pop('local-address')
                if 'remote-address' in peer:
                    peer['remote_address'] = peer.pop('remote-address')
                if 'state' in peer:
                    peer['state'] = peer.pop('state')
                if 'established' in peer:
                    peer['uptime'] = peer.pop('established')
                # Add to active connections
                ipsec_active.append(peer)
                active_connections.append(peer)
        except routeros_exceptions.RouterOsApiConnectionError as e:
            logger.warning(f"Error getting IPsec connections: {str(e)}")
        except (KeyError, ValueError) as e:
            logger.warning(f"Error processing IPsec data: {str(e)}")
        
        # Get server configuration status
        server_config = {
            'pptp': {
                'enabled': False,
                'port': 0,
                'max_mtu': 0,
                'max_mru': 0,
                'authentication': []
            },
            'l2tp': {
                'enabled': False,
                'port': 0,
                'max_mtu': 0,
                'max_mru': 0,
                'authentication': []
            },
            'sstp': {
                'enabled': False,
                'port': 0,
                'max_mtu': 0,
                'max_mru': 0,
                'authentication': []
            },
            'ovpn': {
                'enabled': False,
                'port': 0,
                'mode': '',
                'authentication': []
            },
            'ipsec': {
                'enabled': False,
                'policy_count': 0,
                'proposals': []
            }
        }
        
        # PPTP Server Config
        try:
            pptp_config = list(api.path('/interface/pptp-server/server').select('*'))
            if pptp_config and len(pptp_config) > 0:
                config = pptp_config[0]
                server_config['pptp']['enabled'] = config.get('enabled', 'false') == 'true'
                server_config['pptp']['port'] = int(config.get('port', 1723))
                server_config['pptp']['max_mtu'] = int(config.get('max-mtu', 1450))
                server_config['pptp']['max_mru'] = int(config.get('max-mru', 1450))
                # Get authentication methods
                server_config['pptp']['authentication'] = parse_auth_methods(config.get('authentication', ''))
        except routeros_exceptions.RouterOsApiConnectionError as e:
            logger.warning(f"Error getting PPTP server config: {str(e)}")
        
        # L2TP Server Config
        try:
            l2tp_config = list(api.path('/interface/l2tp-server/server').select('*'))
            if l2tp_config and len(l2tp_config) > 0:
                config = l2tp_config[0]
                server_config['l2tp']['enabled'] = config.get('enabled', 'false') == 'true'
                server_config['l2tp']['port'] = int(config.get('port', 1701))
                server_config['l2tp']['max_mtu'] = int(config.get('max-mtu', 1450))
                server_config['l2tp']['max_mru'] = int(config.get('max-mru', 1450))
                # Get authentication methods
                server_config['l2tp']['authentication'] = parse_auth_methods(config.get('authentication', ''))
        except routeros_exceptions.RouterOsApiConnectionError as e:
            logger.warning(f"Error getting L2TP server config: {str(e)}")
        
        # SSTP Server Config
        try:
            sstp_config = list(api.path('/interface/sstp-server/server').select('*'))
            if sstp_config and len(sstp_config) > 0:
                config = sstp_config[0]
                server_config['sstp']['enabled'] = config.get('enabled', 'false') == 'true'
                server_config['sstp']['port'] = int(config.get('port', 443))
                server_config['sstp']['max_mtu'] = int(config.get('max-mtu', 1450))
                server_config['sstp']['max_mru'] = int(config.get('max-mru', 1450))
                # Get authentication methods
                server_config['sstp']['authentication'] = parse_auth_methods(config.get('authentication', ''))
        except routeros_exceptions.RouterOsApiConnectionError as e:
            logger.warning(f"Error getting SSTP server config: {str(e)}")
        
        # OpenVPN Server Config
        try:
            ovpn_config = list(api.path('/interface/ovpn-server/server').select('*'))
            if ovpn_config and len(ovpn_config) > 0:
                config = ovpn_config[0]
                server_config['ovpn']['enabled'] = config.get('enabled', 'false') == 'true'
                server_config['ovpn']['port'] = int(config.get('port', 1194))
                server_config['ovpn']['mode'] = config.get('mode', 'ip')
                # Get authentication methods
                server_config['ovpn']['authentication'] = ['certificate']
                if config.get('auth', '') != '':
                    server_config['ovpn']['authentication'].append(config.get('auth', ''))
        except routeros_exceptions.RouterOsApiConnectionError as e:
            logger.warning(f"Error getting OpenVPN server config: {str(e)}")
        
        # IPsec Config
        try:
            ipsec_policies = list(api.path('/ip/ipsec/policy').select('*'))
            ipsec_proposals = list(api.path('/ip/ipsec/proposal').select('*'))
            
            # Check if IPsec is active (has policies)
            server_config['ipsec']['enabled'] = len(ipsec_policies) > 0
            server_config['ipsec']['policy_count'] = len(ipsec_policies)
            
            # Get proposal information
            for proposal in ipsec_proposals:
                if 'name' in proposal and 'enc-algorithms' in proposal:
                    server_config['ipsec']['proposals'].append({
                        'name': proposal.get('name', ''),
                        'encryption': proposal.get('enc-algorithms', ''),
                        'hash': proposal.get('auth-algorithms', '')
                    })
        except routeros_exceptions.RouterOsApiConnectionError as e:
            logger.warning(f"Error getting IPsec config: {str(e)}")
        
        # Count connections by type
        connections_by_type = {
            'pptp': len(pptp_active),
            'l2tp': len(l2tp_active),
            'sstp': len(sstp_active),
            'ovpn': len(ovpn_active),
            'ipsec': len(ipsec_active)
        }
        
        # Format and prepare the final result
        result = {
            'timestamp': datetime.now().isoformat(),
            'device_id': device.id,
            'device_name': device.name,
            'total_connections': len(active_connections),
            'connections_by_type': connections_by_type,
            'active_connections': format_connections(active_connections),
            'server_config': server_config
        }
        
        return result
        
    except routeros_exceptions.RouterOsApiConnectionError as e:
        logger.error(f"Error connecting to device {device.id}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error getting VPN data from device {device.id}: {str(e)}")
        return None
    finally:
        # Clean up the connection
        try:
            if 'api' in locals():
                api.close()
        except:
            pass


def parse_auth_methods(auth_string):
    """Parse authentication methods string into a list"""
    if not auth_string or auth_string == '':
        return []
    
    methods = []
    for method in auth_string.split(','):
        method = method.strip()
        if method:
            methods.append(method)
    return methods


def format_connections(connections):
    """Format connection data for the API response"""
    formatted_connections = []
    
    for conn in connections:
        formatted_conn = {}
        
        # Common fields for all VPN types
        formatted_conn['type'] = conn.get('type', '')
        formatted_conn['service'] = conn.get('service', '')
        
        # Handle different naming conventions in RouterOS API
        if 'name' in conn:
            formatted_conn['name'] = conn['name']
        elif 'interface' in conn:
            formatted_conn['name'] = conn['interface']
            
        if 'uptime' in conn:
            formatted_conn['uptime'] = conn['uptime']
            
        # User identification
        if 'user' in conn:
            formatted_conn['user'] = conn['user']
        elif 'username' in conn:
            formatted_conn['user'] = conn['username']
        elif 'name' in conn:
            formatted_conn['user'] = conn['name']
            
        # IP addresses
        if 'address' in conn:
            formatted_conn['address'] = conn['address']
        elif 'remote-address' in conn:
            formatted_conn['address'] = conn['remote-address']
        elif 'remote_address' in conn:
            formatted_conn['address'] = conn['remote_address']
            
        # Add local address if available
        if 'local-address' in conn:
            formatted_conn['local_address'] = conn['local-address']
        elif 'local_address' in conn:
            formatted_conn['local_address'] = conn['local_address']
            
        # Encryption details
        if 'encoding' in conn:
            formatted_conn['encoding'] = conn['encoding']
            
        if 'cipher' in conn:
            formatted_conn['cipher'] = conn['cipher']
            
        # Add other fields based on their presence
        for key, value in conn.items():
            if key not in ['type', 'service', 'name', 'interface', 'uptime', 'user', 'username',
                          'address', 'remote-address', 'remote_address', 'local-address', 'local_address',
                          'encoding', 'cipher']:
                # Convert kebab-case to snake_case for consistent API naming
                new_key = key.replace('-', '_')
                formatted_conn[new_key] = value
                
        formatted_connections.append(formatted_conn)
        
    return formatted_connections


def get_vpn_users(device):
    """Get all VPN users from a MikroTik device"""
    try:
        # Connect to the device using device's port settings
        api = connect(
            username=device.username,
            password=device.password,
            host=device.ip_address,
            port=device.api_port,
            ssl=device.use_ssl
        )
        
        # Get VPN users from PPP secrets
        ppp_users = []
        try:
            ppp_secrets = list(api.path('/ppp/secret').select('*'))
            for secret in ppp_secrets:
                user = {
                    'name': secret.get('name', ''),
                    'profile': secret.get('profile', ''),
                    'service': secret.get('service', ''),
                    'caller_id': secret.get('caller-id', ''),
                    'remote_address': secret.get('remote-address', ''),
                    'last_logged_out': secret.get('last-logged-out', ''),
                    'disabled': secret.get('disabled', 'false') == 'true'
                }
                ppp_users.append(user)
        except routeros_exceptions.RouterOsApiConnectionError as e:
            logger.warning(f"Error getting PPP secrets: {str(e)}")
        except (KeyError, ValueError) as e:
            logger.warning(f"Error processing PPP secrets data: {str(e)}")
        
        # Get OpenVPN users from certificates
        ovpn_users = []
        try:
            certificates = list(api.path('/certificate').select('*').where('common-name', '!=', ''))
            for cert in certificates:
                # Skip CA certificates
                if cert.get('key-usage', '') == 'key-cert-sign,crl-sign':
                    continue
                    
                user = {
                    'name': cert.get('name', ''),
                    'common_name': cert.get('common-name', ''),
                    'service': 'ovpn',
                    'fingerprint': cert.get('fingerprint', ''),
                    'expires_at': cert.get('expires-at', ''),
                    'valid_from': cert.get('invalid-before', ''),
                    'valid_to': cert.get('invalid-after', ''),
                    'status': cert.get('status', '')
                }
                ovpn_users.append(user)
        except routeros_exceptions.RouterOsApiConnectionError as e:
            logger.warning(f"Error getting certificates: {str(e)}")
        except (KeyError, ValueError) as e:
            logger.warning(f"Error processing certificate data: {str(e)}")
        
        # Format and prepare the final result
        result = {
            'ppp_users': ppp_users,
            'ovpn_users': ovpn_users
        }
        
        return result
        
    except routeros_exceptions.RouterOsApiConnectionError as e:
        logger.error(f"Error connecting to device {device.id}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error getting VPN users from device {device.id}: {str(e)}")
        return None
    finally:
        # Clean up the connection
        try:
            if 'api' in locals():
                api.close()
        except:
            pass