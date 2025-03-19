/**
 * VPN Monitoring functionality
 * Handles VPN monitoring view, retrieval and display of VPN connections data
 */

document.addEventListener('DOMContentLoaded', function() {
    const apiClient = new ApiClient();
    let vpnChart = null;
    let selectedDeviceId = null;
    let autoRefreshInterval = null;
    let vpnData = null;
    
    // Initialize the page
    initializeVpnMonitoring();
    
    /**
     * Initialize the VPN monitoring page
     */
    function initializeVpnMonitoring() {
        // Load devices for the dropdown
        loadDevices();
        
        // Set up event listeners
        document.getElementById('device-selector').addEventListener('change', handleDeviceChange);
        document.getElementById('refresh-vpn-btn').addEventListener('click', refreshVpnData);
        document.getElementById('auto-refresh-switch').addEventListener('change', toggleAutoRefresh);
        document.getElementById('export-btn').addEventListener('click', exportVpnData);
    }
    
    /**
     * Load devices for the dropdown
     */
    async function loadDevices() {
        try {
            const devices = await apiClient.getDevices();
            
            const selector = document.getElementById('device-selector');
            selector.innerHTML = '<option value="">Select a device</option>';
            
            devices.forEach(device => {
                const option = document.createElement('option');
                option.value = device.id;
                option.textContent = device.name;
                selector.appendChild(option);
            });
            
            // Show no device selected message
            document.getElementById('vpn-loading').style.display = 'none';
            document.getElementById('no-device-selected').style.display = 'block';
            document.getElementById('vpn-content').style.display = 'none';
            document.getElementById('vpn-error').style.display = 'none';
            
        } catch (error) {
            console.error('Error loading devices:', error);
            showError('Failed to load devices. ' + (error.message || 'Unknown error'));
        }
    }
    
    /**
     * Handle device selection change
     */
    function handleDeviceChange(event) {
        const deviceId = event.target.value;
        
        if (deviceId) {
            selectedDeviceId = deviceId;
            loadVpnData(deviceId);
            startAutoRefresh();
        } else {
            selectedDeviceId = null;
            clearAutoRefresh();
            document.getElementById('vpn-content').style.display = 'none';
            document.getElementById('vpn-loading').style.display = 'none';
            document.getElementById('vpn-error').style.display = 'none';
            document.getElementById('no-device-selected').style.display = 'block';
        }
    }
    
    /**
     * Load VPN data for a device
     */
    async function loadVpnData(deviceId) {
        try {
            // Show loading state
            document.getElementById('vpn-content').style.display = 'none';
            document.getElementById('no-device-selected').style.display = 'none';
            document.getElementById('vpn-error').style.display = 'none';
            document.getElementById('vpn-loading').style.display = 'block';
            
            // Fetch VPN data
            vpnData = await apiClient.getDeviceVpnData(deviceId);
            
            // Update UI with data
            updateVpnSummary(vpnData);
            updateServerStatus(vpnData.server_config);
            updateVpnConnectionsTable(vpnData.active_connections);
            createOrUpdateVpnChart(vpnData.connections_by_type);
            
            // Hide loading and show content
            document.getElementById('vpn-loading').style.display = 'none';
            document.getElementById('vpn-content').style.display = 'block';
            
        } catch (error) {
            console.error('Error loading VPN data:', error);
            document.getElementById('vpn-loading').style.display = 'none';
            document.getElementById('vpn-content').style.display = 'none';
            document.getElementById('no-device-selected').style.display = 'none';
            
            document.getElementById('vpn-error').style.display = 'block';
            document.getElementById('vpn-error-message').textContent = 'Error loading VPN data: ' + 
                (error.message || 'Could not connect to device');
        }
    }
    
    /**
     * Update VPN summary with data
     */
    function updateVpnSummary(data) {
        document.getElementById('total-connections').textContent = data.total_connections;
        document.getElementById('pptp-connections').textContent = data.connections_by_type.pptp;
        document.getElementById('l2tp-connections').textContent = data.connections_by_type.l2tp;
        document.getElementById('sstp-connections').textContent = data.connections_by_type.sstp;
        document.getElementById('ovpn-connections').textContent = data.connections_by_type.ovpn;
        document.getElementById('ipsec-connections').textContent = data.connections_by_type.ipsec;
    }
    
    /**
     * Update server status information
     */
    function updateServerStatus(config) {
        // Update PPTP status
        updateServiceStatus('pptp', config.pptp.enabled);
        
        // Update L2TP status
        updateServiceStatus('l2tp', config.l2tp.enabled);
        
        // Update SSTP status
        updateServiceStatus('sstp', config.sstp.enabled);
        
        // Update OpenVPN status
        updateServiceStatus('ovpn', config.ovpn.enabled);
        
        // Update IPsec status (special case)
        updateServiceStatus('ipsec', config.ipsec.enabled);
    }
    
    /**
     * Update status for a specific VPN service
     */
    function updateServiceStatus(service, enabled) {
        const statusElement = document.getElementById(`${service}-status`);
        const statusIndicator = statusElement.querySelector('.status-indicator');
        const statusText = statusElement.querySelector('.status-text');
        
        if (enabled) {
            statusElement.classList.remove('disabled');
            statusElement.classList.add('enabled');
            statusIndicator.classList.remove('status-offline');
            statusIndicator.classList.add('status-online');
            statusText.textContent = 'Enabled';
        } else {
            statusElement.classList.remove('enabled');
            statusElement.classList.add('disabled');
            statusIndicator.classList.remove('status-online');
            statusIndicator.classList.add('status-offline');
            statusText.textContent = service === 'ipsec' ? 'Not Configured' : 'Disabled';
        }
    }
    
    /**
     * Update VPN connections table
     */
    function updateVpnConnectionsTable(connections) {
        const tableBody = document.getElementById('vpn-connections-table');
        
        if (connections.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center py-3">No active VPN connections found</td>
                </tr>
            `;
            return;
        }
        
        let html = '';
        connections.forEach((conn, index) => {
            html += `
                <tr>
                    <td>
                        <span class="badge bg-info">${conn.service}</span>
                    </td>
                    <td>${conn.user || 'Unknown'}</td>
                    <td>${conn.address || 'N/A'}</td>
                    <td>${conn.uptime || 'N/A'}</td>
                    <td>${conn.encoding || conn.cipher || 'Default'}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary me-1" 
                                onclick="showConnectionDetails(${index})">
                            <i class="fas fa-info-circle"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        
        tableBody.innerHTML = html;
    }
    
    /**
     * Show connection details modal
     */
    window.showConnectionDetails = function(index) {
        if (!vpnData || !vpnData.active_connections || index >= vpnData.active_connections.length) {
            return;
        }
        
        const conn = vpnData.active_connections[index];
        const modal = new bootstrap.Modal(document.getElementById('connectionDetailsModal'));
        const detailsContainer = document.getElementById('connection-details');
        
        let html = '<div class="table-responsive"><table class="table table-borderless">';
        
        // Connection type and service
        html += `
            <tr>
                <td class="fw-bold">Type:</td>
                <td><span class="badge bg-info">${conn.service}</span></td>
            </tr>
        `;
        
        // Username/ID
        html += `
            <tr>
                <td class="fw-bold">Username/ID:</td>
                <td>${conn.user || 'Unknown'}</td>
            </tr>
        `;
        
        // Remote address
        html += `
            <tr>
                <td class="fw-bold">Remote Address:</td>
                <td>${conn.address || 'N/A'}</td>
            </tr>
        `;
        
        // Local address (if available)
        if (conn.local_address) {
            html += `
                <tr>
                    <td class="fw-bold">Local Address:</td>
                    <td>${conn.local_address}</td>
                </tr>
            `;
        }
        
        // Uptime
        html += `
            <tr>
                <td class="fw-bold">Uptime:</td>
                <td>${conn.uptime || 'N/A'}</td>
            </tr>
        `;
        
        // Encryption details
        if (conn.encoding || conn.cipher) {
            html += `
                <tr>
                    <td class="fw-bold">Encryption:</td>
                    <td>${conn.encoding || conn.cipher || 'Default'}</td>
                </tr>
            `;
        }
        
        // Add any remaining properties
        for (const [key, value] of Object.entries(conn)) {
            if (!['service', 'user', 'address', 'local_address', 'uptime', 'encoding', 'cipher', 'type', 'name'].includes(key)) {
                html += `
                    <tr>
                        <td class="fw-bold">${key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</td>
                        <td>${value}</td>
                    </tr>
                `;
            }
        }
        
        html += '</table></div>';
        detailsContainer.innerHTML = html;
        modal.show();
    };
    
    /**
     * Create or update VPN chart
     */
    function createOrUpdateVpnChart(connectionsByType) {
        const ctx = document.getElementById('vpn-chart').getContext('2d');
        
        // If chart exists, destroy it
        if (vpnChart) {
            vpnChart.destroy();
        }
        
        // Prepare data
        const data = {
            labels: ['PPTP', 'L2TP', 'SSTP', 'OpenVPN', 'IPsec'],
            datasets: [{
                label: 'Active Connections',
                data: [
                    connectionsByType.pptp,
                    connectionsByType.l2tp,
                    connectionsByType.sstp,
                    connectionsByType.ovpn,
                    connectionsByType.ipsec
                ],
                backgroundColor: [
                    'rgba(75, 192, 192, 0.5)',
                    'rgba(54, 162, 235, 0.5)',
                    'rgba(153, 102, 255, 0.5)',
                    'rgba(255, 159, 64, 0.5)',
                    'rgba(255, 99, 132, 0.5)'
                ],
                borderColor: [
                    'rgba(75, 192, 192, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)',
                    'rgba(255, 99, 132, 1)'
                ],
                borderWidth: 1
            }]
        };
        
        // Create new chart
        vpnChart = new Chart(ctx, {
            type: 'bar',
            data: data,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'VPN Connections by Type'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Toggle auto refresh on/off
     */
    function toggleAutoRefresh(event) {
        if (event.target.checked) {
            startAutoRefresh();
        } else {
            clearAutoRefresh();
        }
    }
    
    /**
     * Start auto refresh interval
     */
    function startAutoRefresh() {
        // Clear any existing interval
        clearAutoRefresh();
        
        // Only start if a device is selected
        if (selectedDeviceId) {
            // Refresh every 30 seconds
            autoRefreshInterval = setInterval(() => {
                refreshVpnData();
            }, 30000);
        }
    }
    
    /**
     * Clear auto refresh interval
     */
    function clearAutoRefresh() {
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = null;
        }
    }
    
    /**
     * Refresh VPN data
     */
    function refreshVpnData() {
        if (selectedDeviceId) {
            loadVpnData(selectedDeviceId);
        }
    }
    
    /**
     * Export VPN data
     */
    function exportVpnData() {
        if (!vpnData) return;
        
        const format = document.querySelector('input[name="exportFormat"]:checked').value;
        const includeConnections = document.getElementById('includeConnections').checked;
        const includeServerConfig = document.getElementById('includeServerConfig').checked;
        
        // Prepare export data
        const exportData = {
            device_name: vpnData.device_name,
            timestamp: vpnData.timestamp,
            total_connections: vpnData.total_connections,
            connections_by_type: vpnData.connections_by_type
        };
        
        if (includeConnections) {
            exportData.active_connections = vpnData.active_connections;
        }
        
        if (includeServerConfig) {
            exportData.server_config = vpnData.server_config;
        }
        
        // Convert to selected format and download
        if (format === 'json') {
            downloadFile(
                JSON.stringify(exportData, null, 2),
                `vpn_data_${vpnData.device_name}_${new Date().toISOString().slice(0,10)}.json`,
                'application/json'
            );
        } else {
            // CSV format
            let csv = 'data:text/csv;charset=utf-8,';
            
            // Add basic info
            csv += 'Device Name,Total Connections,PPTP Connections,L2TP Connections,SSTP Connections,OpenVPN Connections,IPsec Connections,Timestamp\n';
            csv += `${vpnData.device_name},${vpnData.total_connections},${vpnData.connections_by_type.pptp},${vpnData.connections_by_type.l2tp},${vpnData.connections_by_type.sstp},${vpnData.connections_by_type.ovpn},${vpnData.connections_by_type.ipsec},${vpnData.timestamp}\n\n`;
            
            // Add active connections if included
            if (includeConnections && vpnData.active_connections.length > 0) {
                csv += 'Active Connections\n';
                csv += 'Type,User,Address,Uptime,Encryption\n';
                
                vpnData.active_connections.forEach(conn => {
                    csv += `${conn.service},${conn.user || 'Unknown'},${conn.address || 'N/A'},${conn.uptime || 'N/A'},${conn.encoding || conn.cipher || 'Default'}\n`;
                });
                
                csv += '\n';
            }
            
            // Add server config if included
            if (includeServerConfig) {
                csv += 'Server Configuration\n';
                csv += 'Server Type,Enabled,Port\n';
                
                const config = vpnData.server_config;
                csv += `PPTP,${config.pptp.enabled},${config.pptp.port}\n`;
                csv += `L2TP,${config.l2tp.enabled},${config.l2tp.port}\n`;
                csv += `SSTP,${config.sstp.enabled},${config.sstp.port}\n`;
                csv += `OpenVPN,${config.ovpn.enabled},${config.ovpn.port}\n`;
                csv += `IPsec,${config.ipsec.enabled},N/A\n`;
            }
            
            // Download CSV
            const encodedUri = encodeURI(csv);
            const link = document.createElement('a');
            link.setAttribute('href', encodedUri);
            link.setAttribute('download', `vpn_data_${vpnData.device_name}_${new Date().toISOString().slice(0,10)}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }
    
    /**
     * Download a file
     */
    function downloadFile(content, fileName, contentType) {
        const a = document.createElement('a');
        const file = new Blob([content], {type: contentType});
        a.href = URL.createObjectURL(file);
        a.download = fileName;
        a.click();
        URL.revokeObjectURL(a.href);
    }
    
    /**
     * Show error message
     */
    function showError(message) {
        document.getElementById('vpn-loading').style.display = 'none';
        document.getElementById('vpn-content').style.display = 'none';
        document.getElementById('no-device-selected').style.display = 'none';
        
        document.getElementById('vpn-error').style.display = 'block';
        document.getElementById('vpn-error-message').textContent = message;
    }
});