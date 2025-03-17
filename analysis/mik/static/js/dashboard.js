/**
 * Dashboard functionality
 * Handles the main dashboard view and metrics display
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard
    initializeDashboard();
    
    // Set refresh interval
    setInterval(function() {
        refreshDashboard();
    }, 60000); // Refresh every minute
});

/**
 * Initialize the dashboard
 */
async function initializeDashboard() {
    try {
        // Show loading indicators
        showLoading();
        
        // Fetch dashboard data
        const dashboardData = await api.getDashboardData();
        
        // Update device stats
        updateDeviceStats(dashboardData.devices);
        
        // Update CPU chart
        createCPUChart(dashboardData.top_cpu_devices);
        
        // Update client chart
        createClientChart(dashboardData.top_client_devices);
        
        // Update recent alerts
        updateRecentAlerts(dashboardData.recent_alerts);
        
        // Hide loading indicators
        hideLoading();
        
    } catch (error) {
        console.error('Error initializing dashboard:', error);
        showError('Failed to load dashboard data. Please try refreshing the page.');
        hideLoading();
    }
}

/**
 * Refresh the dashboard data
 */
async function refreshDashboard() {
    try {
        // Fetch dashboard data
        const dashboardData = await api.getDashboardData();
        
        // Update device stats
        updateDeviceStats(dashboardData.devices);
        
        // Update CPU chart
        updateCPUChart(dashboardData.top_cpu_devices);
        
        // Update client chart
        updateClientChart(dashboardData.top_client_devices);
        
        // Update recent alerts
        updateRecentAlerts(dashboardData.recent_alerts);
        
    } catch (error) {
        console.error('Error refreshing dashboard:', error);
    }
}

/**
 * Update device statistics
 * @param {object} deviceStats - Device statistics
 */
function updateDeviceStats(deviceStats) {
    const totalDevicesEl = document.getElementById('total-devices');
    const onlineDevicesEl = document.getElementById('online-devices');
    const offlineDevicesEl = document.getElementById('offline-devices');
    
    if (totalDevicesEl) totalDevicesEl.textContent = deviceStats.total;
    if (onlineDevicesEl) onlineDevicesEl.textContent = deviceStats.online;
    if (offlineDevicesEl) offlineDevicesEl.textContent = deviceStats.offline;
    
    // Update progress bar
    const onlinePercentage = deviceStats.total > 0 ? (deviceStats.online / deviceStats.total) * 100 : 0;
    const deviceStatusBar = document.querySelector('.device-status-bar');
    
    if (deviceStatusBar) {
        deviceStatusBar.style.width = `${onlinePercentage}%`;
        deviceStatusBar.setAttribute('aria-valuenow', onlinePercentage);
    }
}

/**
 * Create CPU usage chart
 * @param {array} cpuData - CPU usage data
 */
function createCPUChart(cpuData) {
    const ctx = document.getElementById('cpu-chart');
    
    if (!ctx) return;
    
    // Prepare chart data
    const labels = cpuData.map(device => device.name);
    const data = cpuData.map(device => device.cpu_load);
    
    // Create chart
    window.cpuChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'CPU Load (%)',
                data: data,
                backgroundColor: 'rgba(75, 192, 192, 0.6)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
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
            }
        }
    });
}

/**
 * Update CPU usage chart
 * @param {array} cpuData - CPU usage data
 */
function updateCPUChart(cpuData) {
    if (!window.cpuChart) {
        createCPUChart(cpuData);
        return;
    }
    
    // Update chart data
    window.cpuChart.data.labels = cpuData.map(device => device.name);
    window.cpuChart.data.datasets[0].data = cpuData.map(device => device.cpu_load);
    
    // Update chart
    window.cpuChart.update();
}

/**
 * Create client count chart
 * @param {array} clientData - Client count data
 */
function createClientChart(clientData) {
    const ctx = document.getElementById('client-chart');
    
    if (!ctx) return;
    
    // Prepare chart data
    const labels = clientData.map(device => device.name);
    const data = clientData.map(device => device.client_count);
    
    // Create chart
    window.clientChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Client Count',
                data: data,
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
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
    if (!window.clientChart) {
        createClientChart(clientData);
        return;
    }
    
    // Update chart data
    window.clientChart.data.labels = clientData.map(device => device.name);
    window.clientChart.data.datasets[0].data = clientData.map(device => device.client_count);
    
    // Update chart
    window.clientChart.update();
}

/**
 * Update recent alerts section
 * @param {array} alerts - Recent alerts
 */
function updateRecentAlerts(alerts) {
    const alertsContainer = document.getElementById('recent-alerts');
    
    if (!alertsContainer) return;
    
    // Clear existing alerts
    alertsContainer.innerHTML = '';
    
    if (alerts.length === 0) {
        alertsContainer.innerHTML = '<div class="text-center text-muted p-3">No recent alerts</div>';
        return;
    }
    
    // Add alerts to container
    alerts.forEach(alert => {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert ${getAlertClass(alert.status)} d-flex align-items-center`;
        
        const timeAgo = formatTimeAgo(new Date(alert.created_at));
        
        alertDiv.innerHTML = `
            <div class="flex-grow-1">
                <strong>${alert.device_name}</strong>: ${alert.message}
                <div class="small text-muted">${timeAgo}</div>
            </div>
            <div>
                <span class="badge ${getStatusBadgeClass(alert.status)}">${formatAlertStatus(alert.status)}</span>
            </div>
        `;
        
        alertsContainer.appendChild(alertDiv);
    });
}

/**
 * Helper function to get alert class based on status
 * @param {string} status - Alert status
 * @returns {string} - CSS class
 */
function getAlertClass(status) {
    switch (status) {
        case 'active':
            return 'alert-danger';
        case 'acknowledged':
            return 'alert-warning';
        case 'resolved':
            return 'alert-success';
        default:
            return 'alert-info';
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
    return status.charAt(0).toUpperCase() + status.slice(1);
}

/**
 * Format relative time (time ago)
 * @param {Date} date - Date to format
 * @returns {string} - Formatted time ago
 */
function formatTimeAgo(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffSecs < 60) {
        return `${diffSecs} second${diffSecs !== 1 ? 's' : ''} ago`;
    } else if (diffMins < 60) {
        return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
        return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else {
        return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    }
}

/**
 * Show loading indicators
 */
function showLoading() {
    const loadingElements = document.querySelectorAll('.dashboard-loading');
    loadingElements.forEach(el => {
        el.style.display = 'flex';
    });
}

/**
 * Hide loading indicators
 */
function hideLoading() {
    const loadingElements = document.querySelectorAll('.dashboard-loading');
    loadingElements.forEach(el => {
        el.style.display = 'none';
    });
}

/**
 * Show error message
 * @param {string} message - Error message
 */
function showError(message) {
    const errorContainer = document.getElementById('dashboard-error');
    
    if (errorContainer) {
        errorContainer.textContent = message;
        errorContainer.style.display = 'block';
    }
}
