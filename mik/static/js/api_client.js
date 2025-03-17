/**
 * API Client for MikroTik Monitor
 * Handles communication with the backend API
 */

class ApiClient {
    constructor() {
        this.baseUrl = '/api';
        this.token = localStorage.getItem('access_token');
    }

    /**
     * Set the authentication token
     * @param {string} token - JWT token
     */
    setToken(token) {
        this.token = token;
        localStorage.setItem('access_token', token);
    }

    /**
     * Clear the authentication token
     */
    clearToken() {
        this.token = null;
        localStorage.removeItem('access_token');
    }

    /**
     * Make an API request
     * @param {string} endpoint - API endpoint
     * @param {string} method - HTTP method
     * @param {object} data - Request data
     * @returns {Promise} - Promise with API response
     */
    async request(endpoint, method = 'GET', data = null) {
        const url = `${this.baseUrl}${endpoint}`;
        
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        const options = {
            method,
            headers,
            credentials: 'same-origin'
        };
        
        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(url, options);
            
            // Handle token expiration
            if (response.status === 401) {
                this.clearToken();
                window.location.href = '/login';
                return null;
            }
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || 'API request failed');
            }
            
            return result;
        } catch (error) {
            console.error('API request error:', error);
            throw error;
        }
    }

    /**
     * Login user
     * @param {string} username - Username
     * @param {string} password - Password
     * @returns {Promise} - Promise with login response
     */
    async login(username, password) {
        const response = await this.request('/auth/login', 'POST', { username, password });
        
        if (response && response.access_token) {
            this.setToken(response.access_token);
        }
        
        return response;
    }

    /**
     * Logout user
     * @returns {Promise} - Promise with logout response
     */
    async logout() {
        const response = await this.request('/auth/logout', 'POST');
        this.clearToken();
        return response;
    }

    // Device endpoints
    
    /**
     * Get all devices
     * @returns {Promise} - Promise with devices
     */
    async getDevices() {
        return this.request('/devices');
    }
    
    /**
     * Get device by ID
     * @param {number} deviceId - Device ID
     * @returns {Promise} - Promise with device
     */
    async getDevice(deviceId) {
        return this.request(`/devices/${deviceId}`);
    }
    
    /**
     * Create a new device
     * @param {object} deviceData - Device data
     * @returns {Promise} - Promise with creation response
     */
    async createDevice(deviceData) {
        return this.request('/devices', 'POST', deviceData);
    }
    
    /**
     * Update a device
     * @param {number} deviceId - Device ID
     * @param {object} deviceData - Device data
     * @returns {Promise} - Promise with update response
     */
    async updateDevice(deviceId, deviceData) {
        return this.request(`/devices/${deviceId}`, 'PUT', deviceData);
    }
    
    /**
     * Delete a device
     * @param {number} deviceId - Device ID
     * @returns {Promise} - Promise with deletion response
     */
    async deleteDevice(deviceId) {
        return this.request(`/devices/${deviceId}`, 'DELETE');
    }
    
    /**
     * Get device interfaces
     * @param {number} deviceId - Device ID
     * @returns {Promise} - Promise with interfaces
     */
    async getDeviceInterfaces(deviceId) {
        return this.request(`/devices/${deviceId}/interfaces`);
    }
    
    /**
     * Get device clients
     * @param {number} deviceId - Device ID
     * @returns {Promise} - Promise with clients
     */
    async getDeviceClients(deviceId) {
        return this.request(`/devices/${deviceId}/clients`);
    }
    
    /**
     * Refresh device data
     * @param {number} deviceId - Device ID
     * @returns {Promise} - Promise with refresh response
     */
    async refreshDevice(deviceId) {
        return this.request(`/devices/${deviceId}/refresh`, 'POST');
    }
    
    /**
     * Create a backup of a device
     * @param {number} deviceId - Device ID
     * @returns {Promise} - Promise with backup response
     */
    async backupDevice(deviceId) {
        return this.request(`/devices/${deviceId}/backup`, 'POST');
    }
    
    /**
     * Get device backups
     * @param {number} deviceId - Device ID
     * @returns {Promise} - Promise with backups
     */
    async getDeviceBackups(deviceId) {
        return this.request(`/devices/${deviceId}/backups`);
    }
    
    /**
     * Run a command on a device
     * @param {number} deviceId - Device ID
     * @param {string} command - Command to run
     * @returns {Promise} - Promise with command response
     */
    async runCommand(deviceId, command) {
        return this.request(`/devices/${deviceId}/command`, 'POST', { command });
    }
    
    /**
     * Get device groups
     * @returns {Promise} - Promise with device groups
     */
    async getDeviceGroups() {
        return this.request('/device-groups');
    }
    
    /**
     * Create a device group
     * @param {object} groupData - Group data
     * @returns {Promise} - Promise with creation response
     */
    async createDeviceGroup(groupData) {
        return this.request('/device-groups', 'POST', groupData);
    }
    
    /**
     * Discover devices on a network
     * @param {string} subnet - Network subnet
     * @returns {Promise} - Promise with discovered devices
     */
    async discoverDevices(subnet) {
        return this.request('/discover', 'POST', { subnet });
    }
    
    /**
     * Add a discovered device
     * @param {object} deviceData - Device data
     * @returns {Promise} - Promise with addition response
     */
    async addDiscoveredDevice(deviceData) {
        return this.request('/discover/add', 'POST', deviceData);
    }
    
    /**
     * Get network map data
     * @returns {Promise} - Promise with network map data
     */
    async getNetworkMap() {
        return this.request('/network-map');
    }
    
    // Monitoring endpoints
    
    /**
     * Get monitoring overview
     * @returns {Promise} - Promise with monitoring overview
     */
    async getMonitoringOverview() {
        return this.request('/monitoring/overview');
    }
    
    /**
     * Get device metrics
     * @param {number} deviceId - Device ID
     * @param {number} hours - Hours of history
     * @returns {Promise} - Promise with device metrics
     */
    async getDeviceMetrics(deviceId, hours = 24) {
        return this.request(`/monitoring/devices/${deviceId}?hours=${hours}`);
    }
    
    /**
     * Get device traffic data
     * @param {number} deviceId - Device ID
     * @param {string} interface - Interface name
     * @param {number} hours - Hours of history
     * @returns {Promise} - Promise with traffic data
     */
    async getDeviceTraffic(deviceId, interface = null, hours = 24) {
        let url = `/monitoring/devices/${deviceId}/traffic?hours=${hours}`;
        if (interface) {
            url += `&interface=${interface}`;
        }
        return this.request(url);
    }
    
    /**
     * Get all clients
     * @returns {Promise} - Promise with clients
     */
    async getAllClients() {
        return this.request('/monitoring/clients');
    }
    
    /**
     * Get dashboard data
     * @returns {Promise} - Promise with dashboard data
     */
    async getDashboardData() {
        return this.request('/monitoring/dashboard');
    }
    
    // Alert endpoints
    
    /**
     * Get alerts
     * @param {string} status - Filter by status
     * @param {number} deviceId - Filter by device
     * @returns {Promise} - Promise with alerts
     */
    async getAlerts(status = null, deviceId = null) {
        let url = '/alerts';
        const params = [];
        
        if (status) {
            params.push(`status=${status}`);
        }
        
        if (deviceId) {
            params.push(`device_id=${deviceId}`);
        }
        
        if (params.length > 0) {
            url += `?${params.join('&')}`;
        }
        
        return this.request(url);
    }
    
    /**
     * Acknowledge an alert
     * @param {number} alertId - Alert ID
     * @returns {Promise} - Promise with acknowledgment response
     */
    async acknowledgeAlert(alertId) {
        return this.request(`/alerts/${alertId}/acknowledge`, 'POST');
    }
    
    /**
     * Resolve an alert
     * @param {number} alertId - Alert ID
     * @returns {Promise} - Promise with resolution response
     */
    async resolveAlert(alertId) {
        return this.request(`/alerts/${alertId}/resolve`, 'POST');
    }
    
    /**
     * Get alert rules
     * @returns {Promise} - Promise with alert rules
     */
    async getAlertRules() {
        return this.request('/config/alerts');
    }
    
    /**
     * Create an alert rule
     * @param {object} ruleData - Rule data
     * @returns {Promise} - Promise with creation response
     */
    async createAlertRule(ruleData) {
        return this.request('/config/alerts', 'POST', ruleData);
    }
    
    /**
     * Update an alert rule
     * @param {number} ruleId - Rule ID
     * @param {object} ruleData - Rule data
     * @returns {Promise} - Promise with update response
     */
    async updateAlertRule(ruleId, ruleData) {
        return this.request(`/config/alerts/${ruleId}`, 'PUT', ruleData);
    }
    
    /**
     * Delete an alert rule
     * @param {number} ruleId - Rule ID
     * @returns {Promise} - Promise with deletion response
     */
    async deleteAlertRule(ruleId) {
        return this.request(`/config/alerts/${ruleId}`, 'DELETE');
    }
    
    // User endpoints
    
    /**
     * Get all users
     * @returns {Promise} - Promise with users
     */
    async getUsers() {
        return this.request('/users');
    }
    
    /**
     * Get user by ID
     * @param {number} userId - User ID
     * @returns {Promise} - Promise with user
     */
    async getUser(userId) {
        return this.request(`/users/${userId}`);
    }
    
    /**
     * Create a new user
     * @param {object} userData - User data
     * @returns {Promise} - Promise with creation response
     */
    async createUser(userData) {
        return this.request('/users', 'POST', userData);
    }
    
    /**
     * Update a user
     * @param {number} userId - User ID
     * @param {object} userData - User data
     * @returns {Promise} - Promise with update response
     */
    async updateUser(userId, userData) {
        return this.request(`/users/${userId}`, 'PUT', userData);
    }
    
    /**
     * Delete a user
     * @param {number} userId - User ID
     * @returns {Promise} - Promise with deletion response
     */
    async deleteUser(userId) {
        return this.request(`/users/${userId}`, 'DELETE');
    }
    
    /**
     * Get all roles
     * @returns {Promise} - Promise with roles
     */
    async getRoles() {
        return this.request('/roles');
    }
}

// Create global API client instance
const api = new ApiClient();
