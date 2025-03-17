/**
 * Main JavaScript file for MikroTik Monitoring System
 * Handles JWT token management and common utility functions
 */

// Check if token exists and is valid
function isAuthenticated() {
    const token = localStorage.getItem('access_token');
    if (!token) return false;
    
    // Simple token validation (check if expired)
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const expiryTime = payload.exp * 1000; // Convert to milliseconds
        
        if (Date.now() >= expiryTime) {
            // Token expired, try to refresh
            refreshToken();
            return false;
        }
        
        return true;
    } catch (error) {
        console.error('Token validation error:', error);
        return false;
    }
}

// Refresh token when expired
async function refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
        redirectToLogin();
        return;
    }
    
    try {
        const response = await fetch('/auth/refresh', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${refreshToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            return true;
        } else {
            redirectToLogin();
            return false;
        }
    } catch (error) {
        console.error('Token refresh error:', error);
        redirectToLogin();
        return false;
    }
}

// Redirect to login page
function redirectToLogin() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    
    if (window.location.pathname !== '/auth/login') {
        window.location.href = '/auth/login';
    }
}

// Set up fetch interceptor to include JWT
async function fetchWithAuth(url, options = {}) {
    if (!isAuthenticated()) {
        await refreshToken();
    }
    
    const token = localStorage.getItem('access_token');
    
    // Set default options
    options.headers = options.headers || {};
    
    // Add authorization header
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Set content type if it's a JSON request
    if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(options.body);
    }
    
    try {
        const response = await fetch(url, options);
        
        // Handle unauthorized responses (token expired)
        if (response.status === 401) {
            const refreshed = await refreshToken();
            if (refreshed) {
                // Retry the request with the new token
                return await fetchWithAuth(url, options);
            } else {
                redirectToLogin();
                throw new Error('Unauthorized');
            }
        }
        
        return response;
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
}

// Format date/time
function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Format bytes to human-readable format
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Format traffic to human-readable format
function formatTraffic(bitsPerSecond) {
    if (bitsPerSecond === 0) return '0 bps';
    
    const k = 1000; // Use 1000 for network rates
    const sizes = ['bps', 'Kbps', 'Mbps', 'Gbps', 'Tbps'];
    
    const i = Math.floor(Math.log(bitsPerSecond) / Math.log(k));
    
    return parseFloat((bitsPerSecond / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Display error messages
function showError(message) {
    // Check if we have a toast container, if not create one
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.id = toastId;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    // Add toast content
    toast.innerHTML = `
        <div class="toast-header bg-danger text-white">
            <strong class="me-auto">Error</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    // Add toast to container
    toastContainer.appendChild(toast);
    
    // Initialize and show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Display success messages
function showSuccess(message) {
    // Check if we have a toast container, if not create one
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.id = toastId;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    // Add toast content
    toast.innerHTML = `
        <div class="toast-header bg-success text-white">
            <strong class="me-auto">Success</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    // Add toast to container
    toastContainer.appendChild(toast);
    
    // Initialize and show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check authentication status on page load
    if (window.location.pathname !== '/auth/login') {
        if (!isAuthenticated()) {
            redirectToLogin();
        } else {
            // Update username in navbar if available
            const user = localStorage.getItem('user');
            if (user) {
                try {
                    const userData = JSON.parse(user);
                    const usernameElement = document.getElementById('username');
                    if (usernameElement && userData.username) {
                        usernameElement.textContent = userData.username;
                    }
                } catch (error) {
                    console.error('Error parsing user data:', error);
                }
            }
        }
    }
});
