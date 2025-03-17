/**
 * Monitoring JavaScript for MikroTik Monitoring System
 * Handles metrics, charts, and alert rules
 */

// Chart objects
let cpuChart = null;
let memoryChart = null;
let diskChart = null;
let trafficChart = null;

// Selected device ID
let selectedDeviceId = null;

// Current time range (hours)
let timeRange = 24;

// Initialize monitoring components
document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts
    initCharts();
    
    // Load devices for selection
    loadDevices();
    
    // Load alert rules
    loadAlertRules();
    
    // Load recent alerts
    loadRecentAlerts();
    
    // Set up event listeners
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Device selection change
    document.getElementById('device-select').addEventListener('change', function() {
        selectedDeviceId = this.value;
        if (selectedDeviceId) {
            loadDeviceOverview(selectedDeviceId);
            loadMetrics(selectedDeviceId);
        } else {
            clearDeviceOverview();
            clearMetrics();
        }
    });
    
    // Time range selection change
    document.getElementById('time-range').addEventListener('change', function() {
        timeRange = parseInt(this.value);
        if (selectedDeviceId) {
            loadMetrics(selectedDeviceId);
        }
    });
    
    // Refresh metrics button
    document.getElementById('refresh-metrics-btn').addEventListener('click', function() {
        if (selectedDeviceId) {
            loadDeviceOverview(selectedDeviceId);
            loadMetrics(selectedDeviceId);
        }
    });
    
    // Interface selection change
    document.getElementById('interface-select').addEventListener('change', function() {
        const selectedInterface = this.value;
        if (selectedDeviceId && selectedInterface) {
            loadTrafficData(selectedDeviceId, selectedInterface);
        }
    });
    
    // Add alert rule button
    document.getElementById('save-alert-rule-btn').addEventListener('click', saveAlertRule);
    
    // Update alert rule button
    document.getElementById('update-alert-rule-btn').addEventListener('click', updateAlertRule);
    
    // Delete alert rule button
    document.getElementById('delete-alert-rule-btn').addEventListener('click', deleteAlertRule);
    
    // Email notification checkbox
    document.getElementById('notify-email').addEventListener('change', function() {
        document.getElementById('email-recipients-container').style.display = this.checked ? 'block' : 'none';
    });
    
    // Email notification checkbox (edit form)
    document.getElementById('edit-notify-email').addEventListener('change', function() {
        document.getElementById('edit-email-recipients-container').style.display = this.checked ? 'block' : 'none';
    });
}

// Initialize charts
function initCharts() {
    // CPU Chart
    const cpuCtx = document.getElementById('cpu-chart').getContext('2d');
    cpuChart = new Chart(cpuCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'CPU Load (%)',
                data: [],
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 2,
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
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y + '%';
                        }
                    }
                }
            }
        }
    });
    
    // Memory Chart
    const memoryCtx = document.getElementById('memory-chart').getContext('2d');
    memoryChart = new Chart(memoryCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Memory Usage (%)',
                data: [],
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 2,
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
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y + '%';
                        }
                    }
                }
            }
        }
    });
    
    // Disk Chart
    const diskCtx = document.getElementById('disk-chart').getContext('2d');
    diskChart = new Chart(diskCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Disk Usage (%)',
                data: [],
                backgroundColor: 'rgba(255, 206, 86, 0.2)',
                borderColor: 'rgba(255, 206, 86, 1)',
                borderWidth: 2,
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
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y + '%';
                        }
                    }
                }
            }
        }
    });
    
    // Traffic Chart
    const trafficCtx = document.getElementById('traffic-chart').getContext('2d');
    trafficChart = new Chart(trafficCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Rx (bits/s)',
                    data: [],
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Tx (bits/s)',
                    data: [],
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatTraffic(value);
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + formatTraffic(context.parsed.y);
                        }
                    }
                }
            }
        }
    });
}

// Load devices for selection dropdown
async function loadDevices() {
    try {
        const response = await fetchWithAuth('/api/devices/');
        
        if (!response.ok) {
            throw new Error('Failed to load devices');
        }
        
        const devices = await response.json();
        
        // Update device select dropdown
        const deviceSelect = document.getElementById('device-select');
        const ruleDeviceSelect = document.getElementById('rule-device');
        const editRuleDeviceSelect = document.getElementById('edit-rule-device');
        
        let deviceOptions = '<option value="" selected>Choose a device...</option>';
        
        devices.forEach(device => {
            deviceOptions += `<option value="${device.id}">${device.name} (${device.ip_address})</option>`;
        });
        
        deviceSelect.innerHTML = deviceOptions;
        ruleDeviceSelect.innerHTML = deviceOptions;
        editRuleDeviceSelect.innerHTML = deviceOptions;
        
    } catch (error) {
        console.error('Error loading devices:', error);
        showError('Failed to load devices. Please try refreshing the page.');
    }
}

// Load device overview
async function loadDeviceOverview(deviceId) {
    try {
        const response = await fetchWithAuth(`/api/devices/${deviceId}/metrics`);
        
        if (!response.ok) {
            throw new Error('Failed to load device metrics');
        }
        
        const metrics = await response.json();
        
        // Update device overview
        const overviewContainer = document.getElementById('device-overview');
        
        if (!metrics.online) {
            overviewContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Device is currently offline
                </div>
            `;
            return;
        }
        
        // Get interfaces for dropdown
        await loadInterfaces(deviceId);
        
        // Display device overview
        overviewContainer.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <div class="card mb-3">
                        <div class="card-body">
                            <h5 class="card-title">System Information</h5>
                            <table class="table table-sm">
                                <tr>
                                    <td>Identity</td>
                                    <td>${metrics.identity || 'Unknown'}</td>
                                </tr>
                                <tr>
                                    <td>Model</td>
                                    <td>${metrics.model || 'Unknown'}</td>
                                </tr>
                                <tr>
                                    <td>Version</td>
                                    <td>${metrics.version || 'Unknown'}</td>
                                </tr>
                                <tr>
                                    <td>Uptime</td>
                                    <td>${metrics.uptime || 'Unknown'}</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card mb-3">
                        <div class="card-body">
                            <h5 class="card-title">Current Resource Usage</h5>
                            <div class="mb-3">
                                <label class="form-label">CPU Usage: ${metrics.cpu_load}%</label>
                                <div class="progress">
                                    <div class="progress-bar bg-${metrics.cpu_load > 80 ? 'danger' : metrics.cpu_load > 50 ? 'warning' : 'primary'}" 
                                         role="progressbar" 
                                         style="width: ${metrics.cpu_load}%;" 
                                         aria-valuenow="${metrics.cpu_load}" 
                                         aria-valuemin="0" 
                                         aria-valuemax="100">
                                        ${metrics.cpu_load}%
                                    </div>
                                </div>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Memory Usage: ${metrics.memory_usage}%</label>
                                <div class="progress">
                                    <div class="progress-bar bg-${metrics.memory_usage > 80 ? 'danger' : metrics.memory_usage > 50 ? 'warning' : 'success'}" 
                                         role="progressbar" 
                                         style="width: ${metrics.memory_usage}%;" 
                                         aria-valuenow="${metrics.memory_usage}" 
                                         aria-valuemin="0" 
                                         aria-valuemax="100">
                                        ${metrics.memory_usage}%
                                    </div>
                                </div>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Disk Usage: ${metrics.disk_usage}%</label>
                                <div class="progress">
                                    <div class="progress-bar bg-${metrics.disk_usage > 80 ? 'danger' : metrics.disk_usage > 50 ? 'warning' : 'info'}" 
                                         role="progressbar" 
                                         style="width: ${metrics.disk_usage}%;" 
                                         aria-valuenow="${metrics.disk_usage}" 
                                         aria-valuemin="0" 
                                         aria-valuemax="100">
                                        ${metrics.disk_usage}%
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Error loading device overview:', error);
        const overviewContainer = document.getElementById('device-overview');
        overviewContainer.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>
                Failed to load device overview: ${error.message || 'Unknown error'}
            </div>
        `;
    }
}

// Load interfaces for the selected device
async function loadInterfaces(deviceId) {
    try {
        const response = await fetchWithAuth(`/api/monitoring/traffic/${deviceId}`);
        
        if (!response.ok) {
            throw new Error('Failed to load interfaces');
        }
        
        const data = await response.json();
        
        // Update interface select dropdown
        const interfaceSelect = document.getElementById('interface-select');
        
        if (!data.online || !data.interfaces || data.interfaces.length === 0) {
            interfaceSelect.innerHTML = '<option value="" selected>No interfaces available</option>';
            return;
        }
        
        let interfaceOptions = '<option value="" selected>Select an interface...</option>';
        
        data.interfaces.forEach(iface => {
            if (iface.type === 'ether' || iface.type === 'wlan') {
                interfaceOptions += `<option value="${iface.name}">${iface.name} (${iface.type})</option>`;
            }
        });
        
        interfaceSelect.innerHTML = interfaceOptions;
        
    } catch (error) {
        console.error('Error loading interfaces:', error);
        const interfaceSelect = document.getElementById('interface-select');
        interfaceSelect.innerHTML = '<option value="" selected>Failed to load interfaces</option>';
    }
}

// Clear device overview
function clearDeviceOverview() {
    const overviewContainer = document.getElementById('device-overview');
    overviewContainer.innerHTML = `
        <div class="text-center py-5">
            <p class="text-muted">Select a device to view metrics</p>
        </div>
    `;
}

// Clear all metrics
function clearMetrics() {
    // Clear CPU chart
    cpuChart.data.labels = [];
    cpuChart.data.datasets[0].data = [];
    cpuChart.update();
    
    // Clear Memory chart
    memoryChart.data.labels = [];
    memoryChart.data.datasets[0].data = [];
    memoryChart.update();
    
    // Clear Disk chart
    diskChart.data.labels = [];
    diskChart.data.datasets[0].data = [];
    diskChart.update();
    
    // Clear Traffic chart
    trafficChart.data.labels = [];
    trafficChart.data.datasets[0].data = [];
    trafficChart.data.datasets[1].data = [];
    trafficChart.update();
    
    // Clear stats
    document.getElementById('cpu-current').textContent = '-';
    document.getElementById('cpu-avg').textContent = '-';
    document.getElementById('cpu-max').textContent = '-';
    document.getElementById('cpu-min').textContent = '-';
    
    document.getElementById('memory-current').textContent = '-';
    document.getElementById('memory-avg').textContent = '-';
    document.getElementById('memory-max').textContent = '-';
    document.getElementById('memory-min').textContent = '-';
    
    document.getElementById('disk-current').textContent = '-';
    document.getElementById('disk-avg').textContent = '-';
    document.getElementById('disk-max').textContent = '-';
    document.getElementById('disk-min').textContent = '-';
    
    document.getElementById('rx-current').textContent = '-';
    document.getElementById('tx-current').textContent = '-';
}

// Load metrics for the selected device
async function loadMetrics(deviceId) {
    // Load metrics for each tab
    await loadCpuMetrics(deviceId);
    await loadMemoryMetrics(deviceId);
    await loadDiskMetrics(deviceId);
    
    // Interface traffic is loaded when an interface is selected
}

// Load CPU metrics
async function loadCpuMetrics(deviceId) {
    try {
        const response = await fetchWithAuth(`/api/monitoring/history/${deviceId}?metric=cpu_load&hours=${timeRange}`);
        
        if (!response.ok) {
            throw new Error('Failed to load CPU metrics');
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Reset chart data
        cpuChart.data.labels = [];
        cpuChart.data.datasets[0].data = [];
        
        // Process data points
        if (data.values && data.values.length > 0) {
            // Sort by timestamp
            const sortedValues = data.values.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
            
            // Extract values for chart
            sortedValues.forEach(point => {
                const date = new Date(point.timestamp);
                const label = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                
                cpuChart.data.labels.push(label);
                cpuChart.data.datasets[0].data.push(point.value);
            });
            
            // Calculate statistics
            const values = sortedValues.map(point => point.value);
            const current = values[values.length - 1] || 0;
            const avg = values.reduce((a, b) => a + b, 0) / values.length;
            const max = Math.max(...values);
            const min = Math.min(...values);
            
            document.getElementById('cpu-current').textContent = `${current.toFixed(1)}%`;
            document.getElementById('cpu-avg').textContent = `${avg.toFixed(1)}%`;
            document.getElementById('cpu-max').textContent = `${max.toFixed(1)}%`;
            document.getElementById('cpu-min').textContent = `${min.toFixed(1)}%`;
        } else {
            document.getElementById('cpu-current').textContent = 'No data';
            document.getElementById('cpu-avg').textContent = 'No data';
            document.getElementById('cpu-max').textContent = 'No data';
            document.getElementById('cpu-min').textContent = 'No data';
        }
        
        // Update chart
        cpuChart.update();
        
    } catch (error) {
        console.error('Error loading CPU metrics:', error);
        document.getElementById('cpu-current').textContent = 'Error';
        document.getElementById('cpu-avg').textContent = 'Error';
        document.getElementById('cpu-max').textContent = 'Error';
        document.getElementById('cpu-min').textContent = 'Error';
    }
}

// Load Memory metrics
async function loadMemoryMetrics(deviceId) {
    try {
        const response = await fetchWithAuth(`/api/monitoring/history/${deviceId}?metric=memory_usage&hours=${timeRange}`);
        
        if (!response.ok) {
            throw new Error('Failed to load Memory metrics');
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Reset chart data
        memoryChart.data.labels = [];
        memoryChart.data.datasets[0].data = [];
        
        // Process data points
        if (data.values && data.values.length > 0) {
            // Sort by timestamp
            const sortedValues = data.values.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
            
            // Extract values for chart
            sortedValues.forEach(point => {
                const date = new Date(point.timestamp);
                const label = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                
                memoryChart.data.labels.push(label);
                memoryChart.data.datasets[0].data.push(point.value);
            });
            
            // Calculate statistics
            const values = sortedValues.map(point => point.value);
            const current = values[values.length - 1] || 0;
            const avg = values.reduce((a, b) => a + b, 0) / values.length;
            const max = Math.max(...values);
            const min = Math.min(...values);
            
            document.getElementById('memory-current').textContent = `${current.toFixed(1)}%`;
            document.getElementById('memory-avg').textContent = `${avg.toFixed(1)}%`;
            document.getElementById('memory-max').textContent = `${max.toFixed(1)}%`;
            document.getElementById('memory-min').textContent = `${min.toFixed(1)}%`;
        } else {
            document.getElementById('memory-current').textContent = 'No data';
            document.getElementById('memory-avg').textContent = 'No data';
            document.getElementById('memory-max').textContent = 'No data';
            document.getElementById('memory-min').textContent = 'No data';
        }
        
        // Update chart
        memoryChart.update();
        
    } catch (error) {
        console.error('Error loading Memory metrics:', error);
        document.getElementById('memory-current').textContent = 'Error';
        document.getElementById('memory-avg').textContent = 'Error';
        document.getElementById('memory-max').textContent = 'Error';
        document.getElementById('memory-min').textContent = 'Error';
    }
}

// Load Disk metrics
async function loadDiskMetrics(deviceId) {
    try {
        const response = await fetchWithAuth(`/api/monitoring/history/${deviceId}?metric=disk_usage&hours=${timeRange}`);
        
        if (!response.ok) {
            throw new Error('Failed to load Disk metrics');
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Reset chart data
        diskChart.data.labels = [];
        diskChart.data.datasets[0].data = [];
        
        // Process data points
        if (data.values && data.values.length > 0) {
            // Sort by timestamp
            const sortedValues = data.values.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
            
            // Extract values for chart
            sortedValues.forEach(point => {
                const date = new Date(point.timestamp);
                const label = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                
                diskChart.data.labels.push(label);
                diskChart.data.datasets[0].data.push(point.value);
            });
            
            // Calculate statistics
            const values = sortedValues.map(point => point.value);
            const current = values[values.length - 1] || 0;
            const avg = values.reduce((a, b) => a + b, 0) / values.length;
            const max = Math.max(...values);
            const min = Math.min(...values);
            
            document.getElementById('disk-current').textContent = `${current.toFixed(1)}%`;
            document.getElementById('disk-avg').textContent = `${avg.toFixed(1)}%`;
            document.getElementById('disk-max').textContent = `${max.toFixed(1)}%`;
            document.getElementById('disk-min').textContent = `${min.toFixed(1)}%`;
        } else {
            document.getElementById('disk-current').textContent = 'No data';
            document.getElementById('disk-avg').textContent = 'No data';
            document.getElementById('disk-max').textContent = 'No data';
            document.getElementById('disk-min').textContent = 'No data';
        }
        
        // Update chart
        diskChart.update();
        
    } catch (error) {
        console.error('Error loading Disk metrics:', error);
        document.getElementById('disk-current').textContent = 'Error';
        document.getElementById('disk-avg').textContent = 'Error';
        document.getElementById('disk-max').textContent = 'Error';
        document.getElementById('disk-min').textContent = 'Error';
    }
}

// Load Traffic data for the selected interface
async function loadTrafficData(deviceId, interfaceName) {
    try {
        const response = await fetchWithAuth(`/api/monitoring/traffic/${deviceId}?interface=${interfaceName}`);
        
        if (!response.ok) {
            throw new Error('Failed to load Traffic data');
        }
        
        const data = await response.json();
        
        if (!data.online || !data.interfaces || data.interfaces.length === 0) {
            throw new Error('No traffic data available');
        }
        
        const iface = data.interfaces[0];
        
        // For a real implementation, we would load historical traffic data here
        // For this example, we'll generate some sample data based on the current traffic values
        
        // Reset chart data
        trafficChart.data.labels = [];
        trafficChart.data.datasets[0].data = [];
        trafficChart.data.datasets[1].data = [];
        
        // Generate sample data for the past hours
        const hours = timeRange;
        const now = new Date();
        const rxBytes = iface.rx_byte || 0;
        const txBytes = iface.tx_byte || 0;
        
        // Calculate bits per second (rough approximation)
        const rxBps = rxBytes * 8 / (hours * 3600);
        const txBps = txBytes * 8 / (hours * 3600);
        
        for (let i = 0; i < 24; i++) {
            const time = new Date(now.getTime() - (hours - i) * 3600000 / 24);
            const label = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            
            // Add some random variation for the example
            const rxVariation = 0.8 + Math.random() * 0.4;
            const txVariation = 0.8 + Math.random() * 0.4;
            
            trafficChart.data.labels.push(label);
            trafficChart.data.datasets[0].data.push(rxBps * rxVariation);
            trafficChart.data.datasets[1].data.push(txBps * txVariation);
        }
        
        // Update current traffic rates
        document.getElementById('rx-current').textContent = formatTraffic(rxBps);
        document.getElementById('tx-current').textContent = formatTraffic(txBps);
        
        // Update chart
        trafficChart.update();
        
    } catch (error) {
        console.error('Error loading Traffic data:', error);
        document.getElementById('rx-current').textContent = 'Error';
        document.getElementById('tx-current').textContent = 'Error';
        
        // Clear chart
        trafficChart.data.labels = [];
        trafficChart.data.datasets[0].data = [];
        trafficChart.data.datasets[1].data = [];
        trafficChart.update();
    }
}

// Load alert rules
async function loadAlertRules() {
    try {
        const response = await fetchWithAuth('/api/monitoring/alert-rules');
        
        if (!response.ok) {
            throw new Error('Failed to load alert rules');
        }
        
        const rules = await response.json();
        
        // Update alert rules container
        const rulesContainer = document.getElementById('alert-rules-container');
        
        if (!rules || rules.length === 0) {
            rulesContainer.innerHTML = '<div class="text-center py-3">No alert rules defined</div>';
            return;
        }
        
        let html = '';
        rules.forEach(rule => {
            const badgeClass = rule.enabled ? 'success' : 'secondary';
            const badgeText = rule.enabled ? 'Enabled' : 'Disabled';
            
            html += `
                <div class="card mb-3">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <span>${rule.name}</span>
                        <span class="badge bg-${badgeClass}">${badgeText}</span>
                    </div>
                    <div class="card-body">
                        <p class="mb-1">Device: <strong>${rule.device_name || 'Unknown'}</strong></p>
                        <p class="mb-1">Metric: <strong>${rule.metric}</strong></p>
                        <p class="mb-1">Condition: <strong>${rule.condition} ${rule.threshold}</strong></p>
                        <p class="mb-0">
                            Notifications: 
                            ${rule.notify_email ? '<span class="badge bg-info me-1">Email</span>' : ''}
                            ${rule.notify_telegram ? '<span class="badge bg-primary me-1">Telegram</span>' : ''}
                        </p>
                    </div>
                    <div class="card-footer text-end">
                        <button class="btn btn-sm btn-primary" onclick="showEditAlertRuleModal(${rule.id})">
                            <i class="fas fa-edit me-1"></i> Edit
                        </button>
                    </div>
                </div>
            `;
        });
        
        rulesContainer.innerHTML = html;
        
    } catch (error) {
        console.error('Error loading alert rules:', error);
        const rulesContainer = document.getElementById('alert-rules-container');
        rulesContainer.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>
                Failed to load alert rules: ${error.message || 'Unknown error'}
            </div>
        `;
    }
}

// Load recent alerts
async function loadRecentAlerts() {
    try {
        const response = await fetchWithAuth('/api/monitoring/alerts?limit=10');
        
        if (!response.ok) {
            throw new Error('Failed to load recent alerts');
        }
        
        const alerts = await response.json();
        
        // Update recent alerts container
        const alertsContainer = document.getElementById('recent-alerts-container');
        
        if (!alerts || alerts.length === 0) {
            alertsContainer.innerHTML = '<div class="text-center py-3">No recent alerts</div>';
            return;
        }
        
        let html = '';
        alerts.forEach(alert => {
            const timestamp = new Date(alert.timestamp).toLocaleString();
            let severity = 'info';
            
            // Determine severity based on the metric and value
            if (alert.metric === 'cpu_load' || alert.metric === 'memory_usage' || alert.metric === 'disk_usage') {
                if (alert.value > 90) {
                    severity = 'critical';
                } else if (alert.value > 75) {
                    severity = 'warning';
                }
            }
            
            html += `
                <div class="card mb-2 alert-card alert-${severity}">
                    <div class="card-body py-2">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <strong>${alert.device_name || 'Unknown device'}</strong>: ${alert.metric}
                                <span class="badge bg-danger ms-1">${alert.condition} ${alert.threshold}</span>
                            </div>
                            <small class="text-muted">${timestamp}</small>
                        </div>
                        <small>Current value: ${alert.value}</small>
                    </div>
                </div>
            `;
        });
        
        alertsContainer.innerHTML = html;
        
    } catch (error) {
        console.error('Error loading recent alerts:', error);
        const alertsContainer = document.getElementById('recent-alerts-container');
        alertsContainer.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>
                Failed to load recent alerts: ${error.message || 'Unknown error'}
            </div>
        `;
    }
}

// Save new alert rule
async function saveAlertRule() {
    const name = document.getElementById('rule-name').value;
    const deviceId = document.getElementById('rule-device').value;
    const metric = document.getElementById('rule-metric').value;
    const condition = document.getElementById('rule-condition').value;
    const threshold = parseFloat(document.getElementById('rule-threshold').value);
    const duration = parseInt(document.getElementById('rule-duration').value);
    const enabled = document.getElementById('rule-enabled').checked;
    const notifyEmail = document.getElementById('notify-email').checked;
    const notifyTelegram = document.getElementById('notify-telegram').checked;
    const emailRecipients = document.getElementById('email-recipients').value;
    const messageTemplate = document.getElementById('message-template').value;
    
    // Validate required fields
    if (!name || !deviceId || !metric || isNaN(threshold)) {
        showError('Please fill in all required fields');
        return;
    }
    
    try {
        const response = await fetchWithAuth('/api/monitoring/alert-rules', {
            method: 'POST',
            body: {
                name: name,
                device_id: deviceId,
                metric: metric,
                condition: condition,
                threshold: threshold,
                duration: duration,
                enabled: enabled,
                notify_email: notifyEmail,
                notify_telegram: notifyTelegram,
                email_recipients: emailRecipients,
                message_template: messageTemplate
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to add alert rule');
        }
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('addAlertRuleModal'));
        modal.hide();
        
        // Clear form
        document.getElementById('add-alert-rule-form').reset();
        document.getElementById('email-recipients-container').style.display = 'none';
        
        // Reload alert rules
        loadAlertRules();
        
        showSuccess('Alert rule added successfully');
    } catch (error) {
        console.error('Error adding alert rule:', error);
        showError(error.message || 'Failed to add alert rule');
    }
}

// Show edit alert rule modal
async function showEditAlertRuleModal(ruleId) {
    try {
        const response = await fetchWithAuth(`/api/monitoring/alert-rules`);
        
        if (!response.ok) {
            throw new Error('Failed to get alert rules');
        }
        
        const rules = await response.json();
        const rule = rules.find(r => r.id === ruleId);
        
        if (!rule) {
            throw new Error('Alert rule not found');
        }
        
        // Fill form fields
        document.getElementById('edit-rule-id').value = rule.id;
        document.getElementById('edit-rule-name').value = rule.name;
        document.getElementById('edit-rule-device').value = rule.device_id;
        document.getElementById('edit-rule-metric').value = rule.metric;
        document.getElementById('edit-rule-condition').value = rule.condition;
        document.getElementById('edit-rule-threshold').value = rule.threshold;
        document.getElementById('edit-rule-duration').value = rule.duration;
        document.getElementById('edit-rule-enabled').checked = rule.enabled;
        document.getElementById('edit-notify-email').checked = rule.notify_email;
        document.getElementById('edit-notify-telegram').checked = rule.notify_telegram;
        document.getElementById('edit-email-recipients').value = rule.email_recipients || '';
        document.getElementById('edit-message-template').value = rule.message_template || '';
        
        // Show/hide email recipients field
        document.getElementById('edit-email-recipients-container').style.display = rule.notify_email ? 'block' : 'none';
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('editAlertRuleModal'));
        modal.show();
    } catch (error) {
        console.error('Error getting alert rule details:', error);
        showError('Failed to get alert rule details');
    }
}

// Update alert rule
async function updateAlertRule() {
    const ruleId = document.getElementById('edit-rule-id').value;
    const name = document.getElementById('edit-rule-name').value;
    const deviceId = document.getElementById('edit-rule-device').value;
    const metric = document.getElementById('edit-rule-metric').value;
    const condition = document.getElementById('edit-rule-condition').value;
    const threshold = parseFloat(document.getElementById('edit-rule-threshold').value);
    const duration = parseInt(document.getElementById('edit-rule-duration').value);
    const enabled = document.getElementById('edit-rule-enabled').checked;
    const notifyEmail = document.getElementById('edit-notify-email').checked;
    const notifyTelegram = document.getElementById('edit-notify-telegram').checked;
    const emailRecipients = document.getElementById('edit-email-recipients').value;
    const messageTemplate = document.getElementById('edit-message-template').value;
    
    // Validate required fields
    if (!name || !deviceId || !metric || isNaN(threshold)) {
        showError('Please fill in all required fields');
        return;
    }
    
    try {
        const response = await fetchWithAuth(`/api/monitoring/alert-rules/${ruleId}`, {
            method: 'PUT',
            body: {
                name: name,
                device_id: deviceId,
                metric: metric,
                condition: condition,
                threshold: threshold,
                duration: duration,
                enabled: enabled,
                notify_email: notifyEmail,
                notify_telegram: notifyTelegram,
                email_recipients: emailRecipients,
                message_template: messageTemplate
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to update alert rule');
        }
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('editAlertRuleModal'));
        modal.hide();
        
        // Reload alert rules
        loadAlertRules();
        
        showSuccess('Alert rule updated successfully');
    } catch (error) {
        console.error('Error updating alert rule:', error);
        showError(error.message || 'Failed to update alert rule');
    }
}

// Delete alert rule
async function deleteAlertRule() {
    const ruleId = document.getElementById('edit-rule-id').value;
    
    if (!confirm('Are you sure you want to delete this alert rule? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetchWithAuth(`/api/monitoring/alert-rules/${ruleId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to delete alert rule');
        }
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('editAlertRuleModal'));
        modal.hide();
        
        // Reload alert rules
        loadAlertRules();
        
        showSuccess('Alert rule deleted successfully');
    } catch (error) {
        console.error('Error deleting alert rule:', error);
        showError(error.message || 'Failed to delete alert rule');
    }
}
