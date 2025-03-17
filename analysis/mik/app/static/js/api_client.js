/**
 * API Client for MikroTik Monitor
 * Handles communication with the backend API
 */

class ApiClient {
    constructor() {
        this.token = null;
        this.baseUrl = '';
        
        // Load token from localStorage
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
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            credentials: 'same-origin'
        };
        
        // Add authorization header if token exists
        if (this.token) {
            options.headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        // Add body for non-GET requests
        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }
        
        try {
            console.log(`API Request: ${method} ${endpoint}`);
            const response = await fetch(`${this.baseUrl}${endpoint}`, options);
            
            // Special handling for 401 Unauthorized (invalid/expired token)
            if (response.status === 401) {
                console.warn('Authentication token expired or invalid');
                this.clearToken();
                
                // Redirect to login page if not already there
                if (!window.location.pathname.includes('/auth/login')) {
                    window.location.href = '/auth/login';
                    return { error: 'Authentication required. Redirecting to login...' };
                }
                
                return { error: 'Authentication required' };
            }
            
            // Handle non-JSON responses (like text or no content)
            let responseData;
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                try {
                    responseData = await response.json();
                } catch (e) {
                    console.warn('Failed to parse JSON response:', e);
                    responseData = { error: 'Invalid JSON response' };
                }
            } else {
                try {
                    const text = await response.text();
                    responseData = { message: text || 'Success (no content)' };
                } catch (e) {
                    console.warn('Failed to get response text:', e);
                    responseData = { message: 'Success (no content)' };
                }
            }
            
            // Handle error responses
            if (!response.ok) {
                const errorMessage = responseData.error || responseData.message || `API error: ${response.status} ${response.statusText}`;
                console.error(`API Error (${response.status}):`, errorMessage);
                
                // Provide more user-friendly message for common errors
                let userMessage = errorMessage;
                if (response.status === 404) {
                    userMessage = 'The requested resource was not found. It may have been deleted or not yet created.';
                } else if (response.status === 403) {
                    userMessage = 'You do not have permission to perform this action.';
                } else if (response.status === 500) {
                    userMessage = 'An internal server error occurred. Please try again later.';
                }
                
                // Return error object instead of throwing
                return { 
                    error: userMessage, 
                    status: response.status,
                    originalError: errorMessage
                };
            }
            
            // Return response data (success)
            return responseData;
        } catch (error) {
            // This catch handles network errors (offline, CORS, etc.)
            console.error('API request network error:', error);
            
            // Determine if it's a network connectivity issue
            let errorMessage = 'Network error: Unable to connect to the server';
            if (error.message && error.message.includes('Failed to fetch')) {
                errorMessage = 'Unable to connect to the server. Please check your internet connection.';
            }
            
            // Return error object instead of throwing
            return { 
                error: errorMessage, 
                isNetworkError: true,
                originalError: error.message
            };
        }
    }
    
    /**
     * Login user
     * @param {string} username - Username
     * @param {string} password - Password
     * @returns {Promise} - Promise with login response
     */
    async login(username, password) {
        const response = await this.request('/auth/api/login', 'POST', { username, password });
        
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
        this.clearToken();
        return { success: true };
    }
    
    /**
     * Get all devices
     * @returns {Promise} - Promise with devices
     */
    async getDevices() {
        return this.request('/api/devices');
    }
    
    /**
     * Get device by ID
     * @param {number} deviceId - Device ID
     * @returns {Promise} - Promise with device
     */
    async getDevice(deviceId) {
        return this.request(`/api/devices/${deviceId}`);
    }
    
    /**
     * Create a new device
     * @param {object} deviceData - Device data
     * @returns {Promise} - Promise with creation response
     */
    async createDevice(deviceData) {
        return this.request('/api/devices', 'POST', deviceData);
    }
    
    /**
     * Update a device
     * @param {number} deviceId - Device ID
     * @param {object} deviceData - Device data
     * @returns {Promise} - Promise with update response
     */
    async updateDevice(deviceId, deviceData) {
        return this.request(`/api/devices/${deviceId}`, 'PUT', deviceData);
    }
    
    /**
     * Delete a device
     * @param {number} deviceId - Device ID
     * @returns {Promise} - Promise with deletion response
     */
    async deleteDevice(deviceId) {
        return this.request(`/api/devices/${deviceId}`, 'DELETE');
    }
    
    /**
     * Get device interfaces
     * @param {number} deviceId - Device ID
     * @returns {Promise} - Promise with interfaces
     */
    async getDeviceInterfaces(deviceId) {
        return this.request(`/api/devices/${deviceId}/interfaces`);
    }
    
    /**
     * Get device clients
     * @param {number} deviceId - Device ID
     * @returns {Promise} - Promise with clients
     */
    async getDeviceClients(deviceId) {
        return this.request(`/api/devices/${deviceId}/clients`);
    }
    
    /**
     * Refresh device data
     * @param {number} deviceId - Device ID
     * @returns {Promise} - Promise with refresh response
     */
    async refreshDevice(deviceId) {
        return this.request(`/api/devices/${deviceId}/refresh`, 'POST');
    }
    
    /**
     * Get network map data
     * @returns {Promise} - Promise with network map data
     */
    async getNetworkMap() {
        return this.request('/api/topology/map');
    }
    
    /**
     * Get device neighbors
     * @param {number} deviceId - Device ID
     * @returns {Promise} - Promise with device neighbors
     */
    async getDeviceNeighbors(deviceId) {
        return this.request(`/api/topology/neighbors/${deviceId}`);
    }
    
    /**
     * Create a backup of a device
     * @param {number} deviceId - Device ID
     * @returns {Promise} - Promise with backup response
     */
    async backupDevice(deviceId) {
        return this.request(`/api/devices/${deviceId}/backup`, 'POST');
    }
    
    /**
     * Get device backups
     * @param {number} deviceId - Device ID
     * @returns {Promise} - Promise with backups
     */
    async getDeviceBackups(deviceId) {
        return this.request(`/api/devices/${deviceId}/backups`);
    }
    
    /**
     * Run a command on a device
     * @param {number} deviceId - Device ID
     * @param {string} command - Command to run
     * @returns {Promise} - Promise with command response
     */
    async runCommand(deviceId, command) {
        return this.request(`/api/config/${deviceId}/command`, 'POST', { command });
    }
    
    /**
     * Discover devices on a network
     * @param {string} subnet - Network subnet
     * @returns {Promise} - Promise with discovered devices
     */
    async discoverDevices(subnet) {
        return this.request('/api/devices/discover', 'POST', { subnet });
    }
    
    /**
     * Get device metrics
     * @param {number} deviceId - Device ID
     * @returns {Promise} - Promise with device metrics
     */
    async getDeviceMetrics(deviceId) {
        return this.request(`/api/monitoring/${deviceId}/metrics`);
    }
    
    /**
     * Get device traffic data
     * @param {number} deviceId - Device ID
     * @param {string} interface - Interface name
     * @param {number} hours - Hours of history
     * @returns {Promise} - Promise with traffic data
     */
    async getDeviceTraffic(deviceId, interface_name = null, hours = 24) {
        let url = `/api/monitoring/${deviceId}/traffic`;
        if (interface_name) {
            url += `?interface=${encodeURIComponent(interface_name)}&hours=${hours}`;
        } else {
            url += `?hours=${hours}`;
        }
        return this.request(url);
    }
    
    /**
     * Get VPN data for a device
     * @param {number} deviceId - Device ID
     * @returns {Promise} - Promise with VPN data
     */
    async getDeviceVpnData(deviceId) {
        return this.request(`/api/monitoring/vpn/${deviceId}`);
    }
    
    /**
     * Get dashboard data
     * @returns {Promise} - Promise with dashboard data
     */
    async getDashboardData() {
        return this.request('/api/monitoring/dashboard');
    }
    
    /**
     * Get alerts
     * @param {string} status - Alert status filter
     * @param {number} deviceId - Device ID filter
     * @returns {Promise} - Promise with alerts
     */
    async getAlerts(status = null, deviceId = null) {
        let url = '/api/monitoring/alerts';
        const params = [];
        
        if (status) {
            params.push(`status=${encodeURIComponent(status)}`);
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
     * Get alert rules
     * @returns {Promise} - Promise with alert rules
     */
    async getAlertRules() {
        return this.request('/api/monitoring/alert-rules');
    }
    
    /**
     * Create an alert rule
     * @param {object} ruleData - Rule data
     * @returns {Promise} - Promise with creation response
     */
    async createAlertRule(ruleData) {
        return this.request('/api/monitoring/alert-rules', 'POST', ruleData);
    }
    
    /**
     * Update an alert rule
     * @param {number} ruleId - Rule ID
     * @param {object} ruleData - Rule data
     * @returns {Promise} - Promise with update response
     */
    async updateAlertRule(ruleId, ruleData) {
        return this.request(`/api/monitoring/alert-rules/${ruleId}`, 'PUT', ruleData);
    }
    
    /**
     * Delete an alert rule
     * @param {number} ruleId - Rule ID
     * @returns {Promise} - Promise with deletion response
     */
    async deleteAlertRule(ruleId) {
        return this.request(`/api/monitoring/alert-rules/${ruleId}`, 'DELETE');
    }
    
    /**
     * Get all users
     * @returns {Promise} - Promise with users
     */
    async getUsers() {
        return this.request('/auth/users');
    }
    
    /**
     * Get user by ID
     * @param {number} userId - User ID
     * @returns {Promise} - Promise with user
     */
    async getUser(userId) {
        return this.request(`/auth/users/${userId}`);
    }
    
    /**
     * Create a new user
     * @param {object} userData - User data (username, email, password, role)
     * @returns {Promise} - Promise with creation response
     */
    async createUser(userData) {
        return this.request('/auth/users', 'POST', userData);
    }
    
    /**
     * Update a user
     * @param {number} userId - User ID
     * @param {object} userData - User data (username, email, password (optional), role)
     * @returns {Promise} - Promise with update response
     */
    async updateUser(userId, userData) {
        return this.request(`/auth/users/${userId}`, 'PUT', userData);
    }
    
    /**
     * Delete a user
     * @param {number} userId - User ID
     * @returns {Promise} - Promise with deletion response
     */
    async deleteUser(userId) {
        return this.request(`/auth/users/${userId}`, 'DELETE');
    }
    
    /**
     * Get current user profile
     * @returns {Promise} - Promise with current user's profile
     */
    async getCurrentUser() {
        return this.request('/auth/profile');
    }
}