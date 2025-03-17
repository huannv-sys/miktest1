/**
 * Dashboard functionality
 * Handles the main dashboard view and metrics display
 */

// API client instance
const apiClient = new ApiClient();

// Chart objects
let cpuChart = null;
let clientChart = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    
    // Refresh button click handler
    const refreshBtn = document.getElementById('refreshDashboardBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshDashboard);
    }
});

/**
 * Initialize the dashboard
 */
async function initializeDashboard() {
    try {
        showLoading();
        
        // Get dashboard data
        const data = await apiClient.getDashboardData();
        
        if (data) {
            // Update device stats
            updateDeviceStats(data.device_stats);
            
            // Initialize charts
            createCPUChart(data.cpu_usage);
            createClientChart(data.client_count);
            
            // Update recent alerts
            updateRecentAlerts(data.recent_alerts);
        }
        
        hideLoading();
    } catch (error) {
        console.error('Error initializing dashboard:', error);
        hideLoading();
        showError('Error loading dashboard data');
    }
}

/**
 * Refresh the dashboard data
 */
async function refreshDashboard() {
    try {
        const refreshBtn = document.getElementById('refreshDashboardBtn');
        
        // Show loading state
        if (refreshBtn) {
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Refreshing...';
        }
        
        // Get dashboard data
        const data = await apiClient.getDashboardData();
        
        if (data) {
            // Update device stats
            updateDeviceStats(data.device_stats);
            
            // Update charts
            updateCPUChart(data.cpu_usage);
            updateClientChart(data.client_count);
            
            // Update recent alerts
            updateRecentAlerts(data.recent_alerts);
        }
        
        // Reset button
        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt me-1"></i> Refresh';
        }
    } catch (error) {
        console.error('Error refreshing dashboard:', error);
        
        // Reset button
        const refreshBtn = document.getElementById('refreshDashboardBtn');
        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt me-1"></i> Refresh';
        }
        
        showError('Error refreshing dashboard data');
    }
}

/**
 * Update device statistics
 * @param {object} deviceStats - Device statistics
 */
function updateDeviceStats(deviceStats) {
    if (!deviceStats) return;
    
    // Update device count
    const deviceCount = document.getElementById('deviceCount');
    if (deviceCount) {
        deviceCount.textContent = deviceStats.total || 0;
    }
    
    // Update alert count
    const alertCount = document.getElementById('alertCount');
    if (alertCount) {
        alertCount.textContent = deviceStats.alerts || 0;
    }
    
    // Update client count
    const clientCount = document.getElementById('clientCount');
    if (clientCount) {
        clientCount.textContent = deviceStats.clients || 0;
    }
    
    // Update bandwidth
    const totalBandwidth = document.getElementById('totalBandwidth');
    if (totalBandwidth) {
        totalBandwidth.textContent = formatTraffic(deviceStats.total_bandwidth || 0);
    }
    
    // Update device status table
    const deviceStatusTable = document.getElementById('deviceStatusTable');
    if (deviceStatusTable && deviceStats.devices && deviceStats.devices.length > 0) {
        let html = '';
        
        deviceStats.devices.forEach(device => {
            html += `
                <tr>
                    <td>${device.name}</td>
                    <td>${device.ip_address}</td>
                    <td>
                        ${device.online ? 
                            '<span class="badge bg-success">Online</span>' : 
                            '<span class="badge bg-danger">Offline</span>'}
                    </td>
                    <td>
                        <div class="progress" style="height: 5px;">
                            <div class="progress-bar ${device.cpu_load > 80 ? 'bg-danger' : (device.cpu_load > 60 ? 'bg-warning' : 'bg-success')}" 
                                role="progressbar" style="width: ${device.cpu_load}%;" 
                                aria-valuenow="${device.cpu_load}" aria-valuemin="0" aria-valuemax="100">
                            </div>
                        </div>
                        <small>${device.cpu_load}%</small>
                    </td>
                    <td>
                        <div class="progress" style="height: 5px;">
                            <div class="progress-bar ${device.memory_used > 80 ? 'bg-danger' : (device.memory_used > 60 ? 'bg-warning' : 'bg-success')}" 
                                role="progressbar" style="width: ${device.memory_used}%;" 
                                aria-valuenow="${device.memory_used}" aria-valuemin="0" aria-valuemax="100">
                            </div>
                        </div>
                        <small>${device.memory_used}%</small>
                    </td>
                </tr>
            `;
        });
        
        deviceStatusTable.innerHTML = html;
    } else if (deviceStatusTable) {
        deviceStatusTable.innerHTML = '<tr><td colspan="5" class="text-center">No devices available</td></tr>';
    }
}

/**
 * Create CPU usage chart
 * @param {array} cpuData - CPU usage data
 */
function createCPUChart(cpuData) {
    const ctx = document.getElementById('cpuChart');
    if (!ctx) return;
    
    // Create default data if none provided
    if (!cpuData || !cpuData.labels || !cpuData.values) {
        cpuData = {
            labels: Array.from({length: 24}, (_, i) => `${i}h`),
            values: Array.from({length: 24}, () => 0)
        };
    }
    
    // Destroy existing chart
    if (cpuChart) {
        cpuChart.destroy();
    }
    
    // Check if Chart is defined
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded');
        return;
    }
    
    // Create new chart
    cpuChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: cpuData.labels,
            datasets: [{
                label: 'CPU Usage (%)',
                data: cpuData.values,
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            }
        }
    });
}

/**
 * Update CPU usage chart
 * @param {array} cpuData - CPU usage data
 */
function updateCPUChart(cpuData) {
    if (!cpuChart || !cpuData || !cpuData.labels || !cpuData.values) return;
    
    cpuChart.data.labels = cpuData.labels;
    cpuChart.data.datasets[0].data = cpuData.values;
    cpuChart.update();
}

/**
 * Create client count chart
 * @param {array} clientData - Client count data
 */
function createClientChart(clientData) {
    const ctx = document.getElementById('clientChart');
    if (!ctx) return;
    
    // Create default data if none provided
    if (!clientData || !clientData.labels || !clientData.values) {
        clientData = {
            labels: Array.from({length: 24}, (_, i) => `${i}h`),
            values: Array.from({length: 24}, () => 0)
        };
    }
    
    // Destroy existing chart
    if (clientChart) {
        clientChart.destroy();
    }
    
    // Check if Chart is defined
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded');
        return;
    }
    
    // Create new chart
    clientChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: clientData.labels,
            datasets: [{
                label: 'Connected Clients',
                data: clientData.values,
                borderColor: '#198754',
                backgroundColor: 'rgba(25, 135, 84, 0.1)',
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            }
        }
    });
}

/**
 * Update client count chart
 * @param {array} clientData - Client count data
 */
function updateClientChart(clientData) {
    if (!clientChart || !clientData || !clientData.labels || !clientData.values) return;
    
    clientChart.data.labels = clientData.labels;
    clientChart.data.datasets[0].data = clientData.values;
    clientChart.update();
}

/**
 * Update recent alerts section
 * @param {array} alerts - Recent alerts
 */
function updateRecentAlerts(alerts) {
    const alertsTable = document.getElementById('recentAlertsTable');
    if (!alertsTable) return;
    
    if (!alerts || alerts.length === 0) {
        alertsTable.innerHTML = '<tr><td colspan="4" class="text-center">No recent alerts</td></tr>';
        return;
    }
    
    let html = '';
    alerts.forEach(alert => {
        html += `
            <tr>
                <td>${alert.device_name}</td>
                <td>${alert.metric}</td>
                <td>
                    <span class="badge ${getStatusBadgeClass(alert.status)}">${formatAlertStatus(alert.status)}</span>
                </td>
                <td>${formatTimeAgo(new Date(alert.timestamp))}</td>
            </tr>
        `;
    });
    
    alertsTable.innerHTML = html;
}

/**
 * Helper function to get alert class based on status
 * @param {string} status - Alert status
 * @returns {string} - CSS class
 */
function getAlertClass(status) {
    switch (status) {
        case 'active':
            return 'danger';
        case 'acknowledged':
            return 'warning';
        case 'resolved':
            return 'success';
        default:
            return 'secondary';
    }
}

/**
 * Helper function to get badge class for alert status
 * @param {string} status - Alert status
 * @returns {string} - CSS class
 */
function getStatusBadgeClass(status) {
    switch (status) {
        case 'active':
            return 'bg-danger';
        case 'acknowledged':
            return 'bg-warning';
        case 'resolved':
            return 'bg-success';
        default:
            return 'bg-secondary';
    }
}

/**
 * Format alert status for display
 * @param {string} status - Alert status
 * @returns {string} - Formatted status
 */
function formatAlertStatus(status) {
    switch (status) {
        case 'active':
            return 'Active';
        case 'acknowledged':
            return 'Acknowledged';
        case 'resolved':
            return 'Resolved';
        default:
            return 'Unknown';
    }
}

/**
 * Format relative time (time ago)
 * @param {Date} date - Date to format
 * @returns {string} - Formatted time ago
 */
function formatTimeAgo(date) {
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) {
        return `${diffInSeconds} second${diffInSeconds !== 1 ? 's' : ''} ago`;
    }
    
    const diffInMinutes = Math.floor(diffInSeconds / 60);
    if (diffInMinutes < 60) {
        return `${diffInMinutes} minute${diffInMinutes !== 1 ? 's' : ''} ago`;
    }
    
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) {
        return `${diffInHours} hour${diffInHours !== 1 ? 's' : ''} ago`;
    }
    
    const diffInDays = Math.floor(diffInHours / 24);
    return `${diffInDays} day${diffInDays !== 1 ? 's' : ''} ago`;
}

/**
 * Show loading indicators
 */
function showLoading() {
    // Add loading indicators to dashboard widgets
    const deviceCount = document.getElementById('deviceCount');
    const alertCount = document.getElementById('alertCount');
    const clientCount = document.getElementById('clientCount');
    const totalBandwidth = document.getElementById('totalBandwidth');
    
    if (deviceCount) deviceCount.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span>';
    if (alertCount) alertCount.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span>';
    if (clientCount) clientCount.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span>';
    if (totalBandwidth) totalBandwidth.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span>';
    
    // Add loading indicators to tables
    const deviceStatusTable = document.getElementById('deviceStatusTable');
    const recentAlertsTable = document.getElementById('recentAlertsTable');
    
    if (deviceStatusTable) {
        deviceStatusTable.innerHTML = `
            <tr>
                <td colspan="5" class="text-center">
                    <span class="spinner-border spinner-border-sm" role="status"></span> Loading...
                </td>
            </tr>
        `;
    }
    
    if (recentAlertsTable) {
        recentAlertsTable.innerHTML = `
            <tr>
                <td colspan="4" class="text-center">
                    <span class="spinner-border spinner-border-sm" role="status"></span> Loading...
                </td>
            </tr>
        `;
    }
}

/**
 * Hide loading indicators
 */
function hideLoading() {
    // Just let the content replace the loading indicators
}

/**
 * Show error message
 * @param {string} message - Error message
 */
function showError(message) {
    const alertHtml = `
        <div class="alert alert-danger alert-dismissible fade show flash-message" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    const flashContainer = document.querySelector('.flash-messages');
    if (flashContainer) {
        flashContainer.innerHTML += alertHtml;
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            const alerts = document.querySelectorAll('.flash-message');
            if (alerts.length > 0) {
                const lastAlert = alerts[alerts.length - 1];
                const bsAlert = new bootstrap.Alert(lastAlert);
                bsAlert.close();
            }
        }, 5000);
    }
}

/**
 * Helper function to format traffic
 */
function formatTraffic(bitsPerSecond) {
    if (bitsPerSecond < 1000) {
        return bitsPerSecond.toFixed(0) + ' bps';
    } else if (bitsPerSecond < 1000000) {
        return (bitsPerSecond / 1000).toFixed(1) + ' Kbps';
    } else if (bitsPerSecond < 1000000000) {
        return (bitsPerSecond / 1000000).toFixed(1) + ' Mbps';
    } else {
        return (bitsPerSecond / 1000000000).toFixed(2) + ' Gbps';
    }
}