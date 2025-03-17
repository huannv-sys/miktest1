/**
 * Devices management functionality
 */

// API client instance
const apiClient = new ApiClient();

// Global variables
let currentDeviceId = null;

// Initialize when DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    loadDevices();
});

/**
 * Set up all event listeners
 */
function setupEventListeners() {
    // View toggles
    const listViewBtn = document.getElementById('listViewBtn');
    const gridViewBtn = document.getElementById('gridViewBtn');
    
    if (listViewBtn && gridViewBtn) {
        listViewBtn.addEventListener('click', function() {
            document.getElementById('deviceGrid').classList.add('d-none');
            document.getElementById('deviceList').classList.remove('d-none');
            listViewBtn.classList.add('active');
            gridViewBtn.classList.remove('active');
        });
        
        gridViewBtn.addEventListener('click', function() {
            document.getElementById('deviceList').classList.add('d-none');
            document.getElementById('deviceGrid').classList.remove('d-none');
            gridViewBtn.classList.add('active');
            listViewBtn.classList.remove('active');
        });
    }
    
    // Network scan button
    const scanNetworkBtn = document.getElementById('scanNetworkBtn');
    if (scanNetworkBtn) {
        scanNetworkBtn.addEventListener('click', function() {
            // Show the network scan modal
            const scanModal = new bootstrap.Modal(document.getElementById('scanNetworkModal'));
            scanModal.show();
        });
    }
    
    // Start scan button
    const startScanBtn = document.getElementById('startScanBtn');
    if (startScanBtn) {
        startScanBtn.addEventListener('click', startNetworkScan);
    }
    
    // Save device button
    const saveDeviceBtn = document.getElementById('saveDeviceBtn');
    if (saveDeviceBtn) {
        saveDeviceBtn.addEventListener('click', saveDevice);
    }
    
    // Update device button
    const updateDeviceBtn = document.getElementById('updateDeviceBtn');
    if (updateDeviceBtn) {
        updateDeviceBtn.addEventListener('click', updateDevice);
    }
    
    // Delete device button
    const deleteDeviceBtn = document.getElementById('deleteDeviceBtn');
    if (deleteDeviceBtn) {
        deleteDeviceBtn.addEventListener('click', function() {
            const deviceId = document.getElementById('editDeviceId').value;
            const deviceName = document.getElementById('editDeviceName').value;
            
            // Set device name in confirmation modal
            document.getElementById('deleteDeviceName').textContent = deviceName;
            
            // Show delete confirmation modal
            const deleteModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
            deleteModal.show();
            
            // Hide edit modal
            const editModal = bootstrap.Modal.getInstance(document.getElementById('editDeviceModal'));
            editModal.hide();
        });
    }
    
    // Confirm delete button
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', deleteDevice);
    }
    
    // Console command button
    const runCommandBtn = document.getElementById('runCommandBtn');
    if (runCommandBtn) {
        runCommandBtn.addEventListener('click', runCommand);
    }
    
    // Backup config button
    const createBackupBtn = document.getElementById('createBackupBtn');
    if (createBackupBtn) {
        createBackupBtn.addEventListener('click', backupConfig);
    }
    
    // Restore backup button
    const restoreBackupBtn = document.getElementById('restoreBackupBtn');
    if (restoreBackupBtn) {
        restoreBackupBtn.addEventListener('click', restoreConfig);
    }
}

/**
 * Load devices from API
 */
async function loadDevices() {
    // Show loading indicators
    document.getElementById('deviceTableBody').innerHTML = `
        <tr>
            <td colspan="6" class="text-center">
                <span class="spinner-border spinner-border-sm" role="status"></span> Loading devices...
            </td>
        </tr>
    `;
    
    document.getElementById('deviceGrid').innerHTML = `
        <div class="col-12 text-center py-5">
            <span class="spinner-border" role="status"></span>
            <p class="mt-2">Loading devices...</p>
        </div>
    `;
    
    // Get devices from API
    const devices = await apiClient.getDevices();
    
    // Check for error response
    if (devices && devices.error) {
        console.error('Error loading devices:', devices.error);
        
        // Show error message
        document.getElementById('deviceTableBody').innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-danger">
                    ${devices.error}
                    <button class="btn btn-sm btn-primary ms-3" onclick="loadDevices()">
                        <i class="fas fa-sync-alt me-1"></i> Retry
                    </button>
                </td>
            </tr>
        `;
        
        document.getElementById('deviceGrid').innerHTML = `
            <div class="col-12 text-center py-5">
                <p class="text-danger">${devices.error}</p>
                <button type="button" class="btn btn-primary" onclick="loadDevices()">
                    <i class="fas fa-sync-alt me-1"></i> Retry
                </button>
            </div>
        `;
        return;
    }
    
    // Handle successful response
    if (devices && Array.isArray(devices) && devices.length > 0) {
        updateDeviceList(devices);
        updateDeviceGrid(devices);
    } else {
        // No devices found or empty array
        document.getElementById('deviceTableBody').innerHTML = `
            <tr>
                <td colspan="6" class="text-center">No devices found. Add your first device.</td>
            </tr>
        `;
        
        document.getElementById('deviceGrid').innerHTML = `
            <div class="col-12 text-center py-5">
                <p>No devices found. Add your first device.</p>
                <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addDeviceModal">
                    <i class="fas fa-plus me-1"></i> Add Device
                </button>
            </div>
        `;
    }
}

/**
 * Update device list view with data
 */
function updateDeviceList(devices) {
    const tableBody = document.getElementById('deviceTableBody');
    
    if (!tableBody) return;
    
    let html = '';
    
    devices.forEach(device => {
        html += `
            <tr data-device-id="${device.id}" onclick="showEditDeviceModal(${device.id})">
                <td>${device.name}</td>
                <td>${device.ip_address}</td>
                <td>${device.model || '-'}</td>
                <td id="device-status-${device.id}">
                    <span class="badge bg-secondary">Unknown</span>
                    <button class="btn btn-sm btn-outline-secondary ms-2" onclick="event.stopPropagation(); checkDeviceStatus(${device.id})">
                        <i class="fas fa-sync-alt"></i>
                    </button>
                </td>
                <td>${device.location || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-primary me-1" onclick="event.stopPropagation(); showDeviceDetails(${device.id})">
                        <i class="fas fa-info-circle"></i>
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="event.stopPropagation(); showEditDeviceModal(${device.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                </td>
            </tr>
        `;
        
        // Check device status after rendering
        setTimeout(() => checkDeviceStatus(device.id), 500 * devices.indexOf(device));
    });
    
    tableBody.innerHTML = html;
}

/**
 * Update device grid view with data
 */
function updateDeviceGrid(devices) {
    const grid = document.getElementById('deviceGrid');
    
    if (!grid) return;
    
    let html = '';
    
    devices.forEach(device => {
        html += `
            <div class="col-md-4 col-lg-3 mb-4">
                <div class="card device-card h-100" onclick="showDeviceDetails(${device.id})">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <h5 class="card-title mb-0 text-truncate">${device.name}</h5>
                            <span id="device-grid-status-${device.id}">
                                <span class="status-indicator bg-secondary"></span>
                            </span>
                        </div>
                        <p class="card-text mb-2">
                            <i class="fas fa-network-wired me-2"></i>${device.ip_address}
                        </p>
                        <p class="card-text mb-2">
                            <i class="fas fa-server me-2"></i>${device.model || 'Unknown Model'}
                        </p>
                        <p class="card-text mb-0">
                            <i class="fas fa-map-marker-alt me-2"></i>${device.location || 'No Location'}
                        </p>
                    </div>
                    <div class="card-footer d-flex justify-content-between">
                        <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); showDeviceDetails(${device.id})">
                            <i class="fas fa-info-circle me-1"></i>Details
                        </button>
                        <button class="btn btn-sm btn-secondary" onclick="event.stopPropagation(); showEditDeviceModal(${device.id})">
                            <i class="fas fa-edit me-1"></i>Edit
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Check device status after rendering
        setTimeout(() => checkDeviceGridStatus(device.id), 500 * devices.indexOf(device));
    });
    
    grid.innerHTML = html;
}

/**
 * Check device status for list view
 */
async function checkDeviceStatus(deviceId) {
    const statusCell = document.getElementById(`device-status-${deviceId}`);
    
    if (!statusCell) return;
    
    try {
        // Show loading indicator
        statusCell.innerHTML = `
            <span class="spinner-border spinner-border-sm text-secondary" role="status">
                <span class="visually-hidden">Loading...</span>
            </span>
        `;
        
        // Get device metrics to check status
        const metrics = await apiClient.getDeviceMetrics(deviceId);
        
        if (metrics) {
            statusCell.innerHTML = `
                <span class="badge bg-success">Online</span>
            `;
        } else {
            statusCell.innerHTML = `
                <span class="badge bg-danger">Offline</span>
            `;
        }
    } catch (error) {
        console.error(`Error checking device ${deviceId} status:`, error);
        statusCell.innerHTML = `
            <span class="badge bg-danger">Offline</span>
            <button class="btn btn-sm btn-outline-secondary ms-2" onclick="checkDeviceStatus(${deviceId})">
                <i class="fas fa-sync-alt"></i>
            </button>
        `;
    }
}

/**
 * Check device status for grid view
 */
async function checkDeviceGridStatus(deviceId) {
    const statusIndicator = document.getElementById(`device-grid-status-${deviceId}`);
    
    if (!statusIndicator) return;
    
    try {
        // Show loading indicator
        statusIndicator.innerHTML = `
            <span class="spinner-border spinner-border-sm text-secondary" role="status">
                <span class="visually-hidden">Loading...</span>
            </span>
        `;
        
        // Get device metrics to check status
        const metrics = await apiClient.getDeviceMetrics(deviceId);
        
        if (metrics) {
            statusIndicator.innerHTML = `
                <span class="status-indicator status-online" title="Online"></span>
            `;
        } else {
            statusIndicator.innerHTML = `
                <span class="status-indicator status-offline" title="Offline"></span>
            `;
        }
    } catch (error) {
        console.error(`Error checking device ${deviceId} grid status:`, error);
        statusIndicator.innerHTML = `
            <span class="status-indicator status-offline" title="Offline"></span>
        `;
    }
}

/**
 * Save new device
 */
async function saveDevice() {
    const form = document.getElementById('addDeviceForm');
    
    // Check form validity
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    // Get form data
    const deviceData = {
        name: document.getElementById('deviceName').value,
        ip_address: document.getElementById('deviceIp').value,
        username: document.getElementById('deviceUsername').value,
        password: document.getElementById('devicePassword').value,
        model: document.getElementById('deviceModel').value,
        location: document.getElementById('deviceLocation').value,
        notes: document.getElementById('deviceNotes').value
    };
    
    // Disable save button
    const saveBtn = document.getElementById('saveDeviceBtn');
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
    
    // Create device
    const response = await apiClient.createDevice(deviceData);
    
    // Re-enable save button
    saveBtn.disabled = false;
    saveBtn.innerHTML = 'Save Device';
    
    // Check for error response
    if (response && response.error) {
        console.error('Error saving device:', response.error);
        showError(response.error || 'Error adding device. Please try again.');
        return;
    }
    
    // Handle success
    const modal = bootstrap.Modal.getInstance(document.getElementById('addDeviceModal'));
    if (modal) modal.hide();
    
    // Show success message
    showSuccess('Device added successfully');
    
    // Reset form
    form.reset();
    
    // Reload devices
    loadDevices();
}

/**
 * Show edit device modal
 */
async function showEditDeviceModal(deviceId) {
    try {
        // Get device details
        const device = await apiClient.getDevice(deviceId);
        
        if (!device) {
            showError('Error loading device details');
            return;
        }
        
        // Fill form with device data
        document.getElementById('editDeviceId').value = device.id;
        document.getElementById('editDeviceName').value = device.name;
        document.getElementById('editDeviceIp').value = device.ip_address;
        document.getElementById('editDeviceUsername').value = device.username;
        document.getElementById('editDevicePassword').value = ''; // Don't show password
        document.getElementById('editDeviceModel').value = device.model || '';
        document.getElementById('editDeviceLocation').value = device.location || '';
        document.getElementById('editDeviceNotes').value = device.notes || '';
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('editDeviceModal'));
        modal.show();
    } catch (error) {
        console.error('Error loading device details:', error);
        showError('Error loading device details. Please try again.');
    }
}

/**
 * Update device
 */
async function updateDevice() {
    const form = document.getElementById('editDeviceForm');
    
    // Check form validity
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    const deviceId = document.getElementById('editDeviceId').value;
    
    // Get form data
    const deviceData = {
        name: document.getElementById('editDeviceName').value,
        ip_address: document.getElementById('editDeviceIp').value,
        username: document.getElementById('editDeviceUsername').value,
        model: document.getElementById('editDeviceModel').value,
        location: document.getElementById('editDeviceLocation').value,
        notes: document.getElementById('editDeviceNotes').value
    };
    
    // Add password only if provided (not empty)
    const password = document.getElementById('editDevicePassword').value;
    if (password) {
        deviceData.password = password;
    }
    
    try {
        // Disable update button
        const updateBtn = document.getElementById('updateDeviceBtn');
        updateBtn.disabled = true;
        updateBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Updating...';
        
        // Update device
        await apiClient.updateDevice(deviceId, deviceData);
        
        // Hide modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('editDeviceModal'));
        modal.hide();
        
        // Show success message
        showSuccess('Device updated successfully');
        
        // Reload devices
        loadDevices();
    } catch (error) {
        console.error('Error updating device:', error);
        showError('Error updating device. Please try again.');
    } finally {
        // Re-enable update button
        const updateBtn = document.getElementById('updateDeviceBtn');
        updateBtn.disabled = false;
        updateBtn.innerHTML = 'Update Device';
    }
}

/**
 * Delete device
 */
async function deleteDevice() {
    const deviceId = document.getElementById('editDeviceId').value;
    
    try {
        // Disable delete button
        const deleteBtn = document.getElementById('confirmDeleteBtn');
        deleteBtn.disabled = true;
        deleteBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Deleting...';
        
        // Delete device
        await apiClient.deleteDevice(deviceId);
        
        // Hide modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('deleteConfirmModal'));
        modal.hide();
        
        // Show success message
        showSuccess('Device deleted successfully');
        
        // Reload devices
        loadDevices();
    } catch (error) {
        console.error('Error deleting device:', error);
        showError('Error deleting device. Please try again.');
    } finally {
        // Re-enable delete button
        const deleteBtn = document.getElementById('confirmDeleteBtn');
        deleteBtn.disabled = false;
        deleteBtn.innerHTML = 'Delete Device';
    }
}

/**
 * Start network scan
 */
async function startNetworkScan() {
    const subnet = document.getElementById('networkSubnet').value;
    const progressBar = document.getElementById('scanProgress');
    const scanResultsDiv = document.getElementById('scanResults');
    const discoveredDevicesTable = document.getElementById('discoveredDevices');
    
    // Validate subnet
    if (!subnet || !subnet.match(/^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/([0-9]|[1-2][0-9]|3[0-2])$/)) {
        showError('Invalid subnet format. Please use CIDR notation (e.g., 192.168.1.0/24)');
        return;
    }
    
    try {
        // Show progress bar
        progressBar.classList.remove('d-none');
        scanResultsDiv.classList.add('d-none');
        discoveredDevicesTable.innerHTML = '';
        
        // Update progress bar
        const progressBarInner = progressBar.querySelector('.progress-bar');
        progressBarInner.style.width = '25%';
        progressBarInner.setAttribute('aria-valuenow', '25');
        
        // Start scan
        const devices = await apiClient.discoverDevices(subnet);
        
        // Update progress bar
        progressBarInner.style.width = '100%';
        progressBarInner.setAttribute('aria-valuenow', '100');
        
        // Show results
        scanResultsDiv.classList.remove('d-none');
        
        if (devices && devices.length > 0) {
            let html = '';
            devices.forEach(device => {
                html += `
                    <tr>
                        <td>${device.ip_address}</td>
                        <td>${device.hostname || '-'}</td>
                        <td>
                            <button class="btn btn-sm btn-primary" onclick="addScannedDevice('${device.ip_address}', '${device.hostname || 'MikroTik Device'}')">
                                <i class="fas fa-plus me-1"></i> Add
                            </button>
                        </td>
                    </tr>
                `;
            });
            discoveredDevicesTable.innerHTML = html;
        } else {
            discoveredDevicesTable.innerHTML = `
                <tr>
                    <td colspan="3" class="text-center">No MikroTik devices found on the network.</td>
                </tr>
            `;
        }
    } catch (error) {
        console.error('Error scanning network:', error);
        showError('Error scanning network. Please try again.');
        
        // Update progress bar to indicate error
        const progressBarInner = progressBar.querySelector('.progress-bar');
        progressBarInner.style.width = '100%';
        progressBarInner.setAttribute('aria-valuenow', '100');
        progressBarInner.classList.remove('bg-primary', 'bg-success');
        progressBarInner.classList.add('bg-danger');
        
        // Show empty results
        scanResultsDiv.classList.remove('d-none');
        discoveredDevicesTable.innerHTML = `
            <tr>
                <td colspan="3" class="text-center text-danger">Error scanning network. Please try again.</td>
            </tr>
        `;
    }
}

/**
 * Add discovered device
 */
function addScannedDevice(ipAddress, hostname) {
    // Fill add device form
    document.getElementById('deviceName').value = hostname;
    document.getElementById('deviceIp').value = ipAddress;
    document.getElementById('deviceUsername').value = 'admin';
    document.getElementById('deviceModel').value = 'RouterOS';
    
    // Focus on password field
    document.getElementById('devicePassword').value = '';
    
    // Hide scan modal
    const scanModal = bootstrap.Modal.getInstance(document.getElementById('scanNetworkModal'));
    scanModal.hide();
    
    // Show add device modal
    const addModal = new bootstrap.Modal(document.getElementById('addDeviceModal'));
    addModal.show();
    
    // Focus on password field
    setTimeout(() => {
        document.getElementById('devicePassword').focus();
    }, 500);
}

/**
 * Show device details
 */
async function showDeviceDetails(deviceId) {
    currentDeviceId = deviceId;
    
    // Show loading state in tabs
    document.getElementById('deviceDetailModel').textContent = 'Loading...';
    document.getElementById('deviceDetailSerial').textContent = 'Loading...';
    document.getElementById('deviceDetailFirmware').textContent = 'Loading...';
    document.getElementById('deviceDetailUptime').textContent = 'Loading...';
    document.getElementById('deviceDetailLastUpdated').textContent = 'Loading...';
    
    document.getElementById('deviceDetailCpuLoad').style.width = '0%';
    document.getElementById('deviceDetailCpuLoad').textContent = '0%';
    document.getElementById('deviceDetailMemoryUsage').style.width = '0%';
    document.getElementById('deviceDetailMemoryUsage').textContent = '0%';
    document.getElementById('deviceDetailDiskUsage').style.width = '0%';
    document.getElementById('deviceDetailDiskUsage').textContent = '0%';
    
    document.getElementById('interfacesTable').innerHTML = '<tr><td colspan="5" class="text-center">Loading interfaces...</td></tr>';
    document.getElementById('clientsTable').innerHTML = '<tr><td colspan="5" class="text-center">Loading clients...</td></tr>';
    document.getElementById('commandOutput').textContent = 'Command output will appear here...';
    
    try {
        // Get device details
        const device = await apiClient.getDevice(deviceId);
        
        if (!device) {
            showError('Error loading device details');
            return;
        }
        
        // Update modal title
        document.getElementById('deviceDetailModalLabel').textContent = `Device Details: ${device.name}`;
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('deviceDetailModal'));
        modal.show();
        
        // Get device metrics
        const metrics = await apiClient.getDeviceMetrics(deviceId);
        
        // Update system info
        updateSystemInfo(device, metrics);
        
        // Update resource usage
        if (metrics) {
            updateResourceUsage(metrics);
        }
        
        // Get device interfaces
        const interfaces = await apiClient.getDeviceInterfaces(deviceId);
        if (interfaces) {
            updateInterfaces(interfaces);
        }
        
        // Get device clients
        const clients = await apiClient.getDeviceClients(deviceId);
        if (clients) {
            updateClients(clients);
        }
        
        // Get device backups
        const backups = await apiClient.getDeviceBackups(deviceId);
        if (backups && backups.length > 0) {
            let html = '';
            backups.forEach(backup => {
                html += `
                    <tr>
                        <td>${new Date(backup.created_at).toLocaleString()}</td>
                        <td>${formatBytes(backup.size)}</td>
                        <td>
                            <a href="${backup.download_url}" class="btn btn-sm btn-primary me-1" download>
                                <i class="fas fa-download me-1"></i>Download
                            </a>
                            <button class="btn btn-sm btn-warning" onclick="restoreBackup('${backup.id}')">
                                <i class="fas fa-upload me-1"></i>Restore
                            </button>
                        </td>
                    </tr>
                `;
            });
            document.getElementById('backupHistoryTable').innerHTML = html;
        } else {
            document.getElementById('backupHistoryTable').innerHTML = '<tr><td colspan="3" class="text-center">No backups available</td></tr>';
        }
    } catch (error) {
        console.error('Error loading device details:', error);
        showError('Error loading device details. Please try again.');
    }
}

/**
 * Update system info in device details modal
 */
function updateSystemInfo(device, metrics) {
    document.getElementById('deviceDetailModel').textContent = metrics && metrics.system ? metrics.system.model : device.model || 'Unknown';
    document.getElementById('deviceDetailSerial').textContent = metrics && metrics.system ? metrics.system.serial_number : 'Unknown';
    document.getElementById('deviceDetailFirmware').textContent = metrics && metrics.system ? metrics.system.version : 'Unknown';
    document.getElementById('deviceDetailUptime').textContent = metrics && metrics.system ? metrics.system.uptime : 'Unknown';
    document.getElementById('deviceDetailLastUpdated').textContent = new Date().toLocaleString();
}

/**
 * Update resource usage in device details modal
 */
function updateResourceUsage(metrics) {
    if (metrics.cpu) {
        const cpuLoad = metrics.cpu.load;
        document.getElementById('deviceDetailCpuLoad').style.width = `${cpuLoad}%`;
        document.getElementById('deviceDetailCpuLoad').textContent = `${cpuLoad}%`;
        
        // Change color based on load
        const cpuBar = document.getElementById('deviceDetailCpuLoad');
        if (cpuLoad > 80) {
            cpuBar.className = 'progress-bar bg-danger';
        } else if (cpuLoad > 60) {
            cpuBar.className = 'progress-bar bg-warning';
        } else {
            cpuBar.className = 'progress-bar bg-success';
        }
    }
    
    if (metrics.memory) {
        const memoryUsage = metrics.memory.used_percent;
        document.getElementById('deviceDetailMemoryUsage').style.width = `${memoryUsage}%`;
        document.getElementById('deviceDetailMemoryUsage').textContent = `${memoryUsage}%`;
        
        // Change color based on usage
        const memoryBar = document.getElementById('deviceDetailMemoryUsage');
        if (memoryUsage > 80) {
            memoryBar.className = 'progress-bar bg-danger';
        } else if (memoryUsage > 60) {
            memoryBar.className = 'progress-bar bg-warning';
        } else {
            memoryBar.className = 'progress-bar bg-success';
        }
    }
    
    if (metrics.disk) {
        const diskUsage = metrics.disk.used_percent;
        document.getElementById('deviceDetailDiskUsage').style.width = `${diskUsage}%`;
        document.getElementById('deviceDetailDiskUsage').textContent = `${diskUsage}%`;
        
        // Change color based on usage
        const diskBar = document.getElementById('deviceDetailDiskUsage');
        if (diskUsage > 80) {
            diskBar.className = 'progress-bar bg-danger';
        } else if (diskUsage > 60) {
            diskBar.className = 'progress-bar bg-warning';
        } else {
            diskBar.className = 'progress-bar bg-info';
        }
    }
}

/**
 * Update interfaces table in device details modal
 */
function updateInterfaces(data) {
    const interfacesTable = document.getElementById('interfacesTable');
    
    if (!data || data.length === 0) {
        interfacesTable.innerHTML = '<tr><td colspan="5" class="text-center">No interfaces found</td></tr>';
        return;
    }
    
    let html = '';
    data.forEach(iface => {
        html += `
            <tr>
                <td>${iface.name}</td>
                <td>${iface.type}</td>
                <td>
                    ${iface.running ? 
                        '<span class="badge bg-success">Up</span>' : 
                        '<span class="badge bg-danger">Down</span>'}
                </td>
                <td>${iface.mac_address || '-'}</td>
                <td>
                    <small>TX: ${formatTraffic(iface.tx_byte_rate || 0)}</small><br>
                    <small>RX: ${formatTraffic(iface.rx_byte_rate || 0)}</small>
                </td>
            </tr>
        `;
    });
    
    interfacesTable.innerHTML = html;
}

/**
 * Update clients table in device details modal
 */
function updateClients(data) {
    const clientsTable = document.getElementById('clientsTable');
    
    if (!data || data.length === 0) {
        clientsTable.innerHTML = '<tr><td colspan="5" class="text-center">No clients found</td></tr>';
        return;
    }
    
    let html = '';
    data.forEach(client => {
        html += `
            <tr>
                <td>${client.hostname || '-'}</td>
                <td>${client.mac_address}</td>
                <td>${client.ip_address}</td>
                <td>${client.interface}</td>
                <td>${new Date(client.last_seen).toLocaleString()}</td>
            </tr>
        `;
    });
    
    clientsTable.innerHTML = html;
}

/**
 * Run command on device
 */
async function runCommand() {
    if (!currentDeviceId) return;
    
    const commandInput = document.getElementById('commandInput');
    const command = commandInput.value.trim();
    
    if (!command) {
        commandInput.focus();
        return;
    }
    
    const commandOutput = document.getElementById('commandOutput');
    
    try {
        // Show loading
        commandOutput.textContent = 'Running command...';
        
        // Run command
        const result = await apiClient.runCommand(currentDeviceId, command);
        
        // Display result
        if (result && result.output) {
            commandOutput.textContent = result.output;
        } else {
            commandOutput.textContent = 'Command executed successfully with no output.';
        }
    } catch (error) {
        console.error('Error running command:', error);
        commandOutput.textContent = `Error: ${error.message || 'Failed to run command'}`;
    }
}

/**
 * Backup device configuration
 */
async function backupConfig() {
    if (!currentDeviceId) return;
    
    const createBackupBtn = document.getElementById('createBackupBtn');
    
    try {
        // Disable button
        createBackupBtn.disabled = true;
        createBackupBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Creating backup...';
        
        // Create backup
        const result = await apiClient.backupDevice(currentDeviceId);
        
        if (result && result.success) {
            showSuccess('Backup created successfully');
            
            // Refresh backup list
            const backups = await apiClient.getDeviceBackups(currentDeviceId);
            if (backups && backups.length > 0) {
                let html = '';
                backups.forEach(backup => {
                    html += `
                        <tr>
                            <td>${new Date(backup.created_at).toLocaleString()}</td>
                            <td>${formatBytes(backup.size)}</td>
                            <td>
                                <a href="${backup.download_url}" class="btn btn-sm btn-primary me-1" download>
                                    <i class="fas fa-download me-1"></i>Download
                                </a>
                                <button class="btn btn-sm btn-warning" onclick="restoreBackup('${backup.id}')">
                                    <i class="fas fa-upload me-1"></i>Restore
                                </button>
                            </td>
                        </tr>
                    `;
                });
                document.getElementById('backupHistoryTable').innerHTML = html;
            }
        } else {
            showError('Error creating backup');
        }
    } catch (error) {
        console.error('Error creating backup:', error);
        showError('Error creating backup. Please try again.');
    } finally {
        // Re-enable button
        createBackupBtn.disabled = false;
        createBackupBtn.innerHTML = '<i class="fas fa-download me-1"></i> Create Backup';
    }
}

/**
 * Restore device configuration
 */
function restoreConfig() {
    // This function would handle the file upload and call the API to restore the config
    alert('Restore configuration functionality is not implemented yet.');
}

/**
 * Helper function to format bytes
 */
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
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

/**
 * Display error message
 */
function showError(message) {
    const alertHtml = `
        <div class="alert alert-danger alert-dismissible fade show flash-message" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    const flashContainer = document.querySelector('.flash-messages');
    flashContainer.innerHTML += alertHtml;
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        const alerts = document.querySelectorAll('.flash-message');
        if (alerts.length > 0) {
            const lastAlert = alerts[alerts.length - 1];
            bootstrap.Alert.getInstance(lastAlert)?.close();
        }
    }, 5000);
}

/**
 * Display success message
 */
function showSuccess(message) {
    const alertHtml = `
        <div class="alert alert-success alert-dismissible fade show flash-message" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    const flashContainer = document.querySelector('.flash-messages');
    flashContainer.innerHTML += alertHtml;
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        const alerts = document.querySelectorAll('.flash-message');
        if (alerts.length > 0) {
            const lastAlert = alerts[alerts.length - 1];
            bootstrap.Alert.getInstance(lastAlert)?.close();
        }
    }, 5000);
}