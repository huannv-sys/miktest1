/**
 * Main JavaScript file for MikroTik Monitoring System
 * Handles JWT token management and common utility functions
 * Optimized for performance and reliability
 */

// Cache for storing API responses to reduce server load and improve performance
const apiCache = (() => {
    const cache = new Map();
    const timestamps = new Map();
    
    return {
        // Get cached data if not expired
        get(key, maxAge = 30000) { // Default 30 seconds
            const timestamp = timestamps.get(key);
            if (timestamp && (Date.now() - timestamp) < maxAge) {
                return cache.get(key);
            }
            return null;
        },
        
        // Cache data with timestamp
        set(key, data, maxAge = null) {
            cache.set(key, data);
            timestamps.set(key, Date.now());
            
            // Auto-cleanup if maxAge provided
            if (maxAge) {
                setTimeout(() => {
                    if (timestamps.get(key) && (Date.now() - timestamps.get(key)) >= maxAge) {
                        this.delete(key);
                    }
                }, maxAge);
            }
        },
        
        // Remove specific cache entry
        delete(key) {
            cache.delete(key);
            timestamps.delete(key);
        },
        
        // Clear all cache entries matching a pattern
        clearPattern(pattern) {
            for (const key of cache.keys()) {
                if (key.includes(pattern)) {
                    this.delete(key);
                }
            }
        },
        
        // Clear all cache
        clear() {
            cache.clear();
            timestamps.clear();
        }
    };
})();

// Token management service with validation
const tokenService = (() => {
    // Token storage keys
    const ACCESS_TOKEN_KEY = 'access_token';
    const REFRESH_TOKEN_KEY = 'refresh_token';
    const USER_KEY = 'user';
    
    // Store tokens securely (could be enhanced with HttpOnly cookies for production)
    return {
        // Get access token
        getAccessToken() {
            return localStorage.getItem(ACCESS_TOKEN_KEY);
        },
        
        // Get refresh token
        getRefreshToken() {
            return localStorage.getItem(REFRESH_TOKEN_KEY);
        },
        
        // Store tokens
        setTokens(accessToken, refreshToken = null) {
            if (accessToken) {
                localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
            }
            
            if (refreshToken) {
                localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
            }
        },
        
        // Clear all auth data
        clearTokens() {
            localStorage.removeItem(ACCESS_TOKEN_KEY);
            localStorage.removeItem(REFRESH_TOKEN_KEY);
            localStorage.removeItem(USER_KEY);
        },
        
        // Decode JWT payload without validation
        decodeToken(token) {
            try {
                return JSON.parse(atob(token.split('.')[1]));
            } catch (error) {
                console.error('Invalid token format:', error);
                return null;
            }
        },
        
        // Set user data
        setUser(userData) {
            if (userData) {
                localStorage.setItem(USER_KEY, JSON.stringify(userData));
            }
        },
        
        // Get user data
        getUser() {
            try {
                const userData = localStorage.getItem(USER_KEY);
                return userData ? JSON.parse(userData) : null;
            } catch (error) {
                console.error('Error parsing user data:', error);
                return null;
            }
        }
    };
})();

// Enhanced Authentication Check with JWT validation
function isAuthenticated() {
    const token = tokenService.getAccessToken();
    if (!token) return false;
    
    try {
        // Decode token and check expiration
        const payload = tokenService.decodeToken(token);
        if (!payload || !payload.exp) {
            console.warn('Invalid token format (missing expiration)');
            return false;
        }
        
        const expiryTime = payload.exp * 1000; // Convert to milliseconds
        const currentTime = Date.now();
        
        // Add a buffer of 30 seconds to account for clock differences
        if (currentTime >= (expiryTime - 30000)) {
            console.log('Token expired or about to expire, refreshing...');
            // Fire and forget refresh - don't block the UI
            refreshToken().catch(error => {
                console.error('Background token refresh failed:', error);
            });
            
            // Check if completely expired (not just within buffer)
            return currentTime < expiryTime;
        }
        
        return true;
    } catch (error) {
        console.error('Token validation error:', error);
        return false;
    }
}

// Improved token refresh with retries
async function refreshToken(retries = 1) {
    const refreshToken = tokenService.getRefreshToken();
    if (!refreshToken) {
        console.warn('No refresh token available');
        redirectToLogin();
        return false;
    }
    
    // Track attempts for retry logic
    let attempts = 0;
    let lastError = null;
    
    while (attempts <= retries) {
        try {
            console.log(`Refreshing token (attempt ${attempts + 1}/${retries + 1})...`);
            
            // Create AbortController for timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout
            
            const response = await fetch('/auth/refresh', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${refreshToken}`
                },
                signal: controller.signal
            });
            
            // Clear timeout
            clearTimeout(timeoutId);
            
            if (response.ok) {
                const data = await response.json();
                
                // Validate response contains token
                if (!data.access_token) {
                    throw new Error('Invalid token response format');
                }
                
                // Save new tokens
                tokenService.setTokens(data.access_token, data.refresh_token || null);
                console.log('Token refreshed successfully');
                return true;
            } else {
                // Handle specific HTTP errors
                if (response.status === 401 || response.status === 403) {
                    console.warn('Authentication failed during token refresh');
                    redirectToLogin();
                    return false;
                }
                
                // Server errors might be temporary, so retry
                lastError = new Error(`Token refresh failed: ${response.status} ${response.statusText}`);
                attempts++;
                
                if (attempts <= retries) {
                    // Wait before retrying (exponential backoff)
                    await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, attempts - 1)));
                    continue;
                }
            }
        } catch (error) {
            lastError = error;
            
            // Abort errors are from timeout
            if (error.name === 'AbortError') {
                console.warn('Token refresh request timed out');
            } else {
                console.error('Token refresh error:', error);
            }
            
            attempts++;
            if (attempts <= retries) {
                // Wait before retrying (exponential backoff)
                await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, attempts - 1)));
                continue;
            }
        }
    }
    
    // If we get here, all retries failed
    console.error('Token refresh failed after all retries', lastError);
    redirectToLogin();
    return false;
}

// Enhanced redirect to login with return URL support
function redirectToLogin() {
    // Clear auth data
    tokenService.clearTokens();
    
    // Store current path for redirect after login (if not already on login page)
    if (window.location.pathname !== '/auth/login') {
        const returnUrl = window.location.pathname + window.location.search;
        sessionStorage.setItem('returnUrl', returnUrl);
        window.location.href = '/auth/login';
    }
}

// Enhanced fetch with authentication, retry, timeouts, caching and error handling
async function fetchWithAuth(url, options = {}) {
    // Default configuration
    const defaultOptions = {
        credentials: 'same-origin',
        cache: 'no-store',   // Disable cache (using valid enum value)
        cacheTime: 30000,    // Cache time in ms (30s default)
        timeout: 30000,      // Request timeout in ms (30s default)
        retries: 1,          // Number of retries for failed requests
        backoff: true,       // Use exponential backoff for retries
        refreshOnUnauth: true, // Try to refresh token on 401 responses
        showErrors: true     // Show error notifications
    };
    
    // Merge with defaults and extract special options
    const config = { ...defaultOptions, ...options };
    const { 
        cache, cacheTime, timeout, retries, backoff, 
        refreshOnUnauth, showErrors, ...fetchOptions 
    } = config;
    
    // Authentication check with auto-refresh for near-expiry tokens
    if (!isAuthenticated()) {
        // Force refresh only for initial requests, not retries
        if (!options._isRetry) {
            await refreshToken();
            if (!isAuthenticated()) {
                redirectToLogin();
                return null;
            }
        }
    }
    
    // Use cache for GET requests if enabled
    const cacheKey = `${url}-${JSON.stringify(fetchOptions)}`;
    if (cache && (!fetchOptions.method || fetchOptions.method === 'GET')) {
        const cachedResponse = apiCache.get(cacheKey, cacheTime);
        if (cachedResponse) {
            console.log(`Using cached response for: ${url}`);
            return cachedResponse;
        }
    }
    
    // Add auth token to headers
    const token = tokenService.getAccessToken();
    fetchOptions.headers = fetchOptions.headers || {};
    if (token) {
        fetchOptions.headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Auto-serialize JSON body
    if (fetchOptions.body && typeof fetchOptions.body === 'object' && 
        !(fetchOptions.body instanceof FormData) && 
        !(fetchOptions.body instanceof Blob) && 
        !(fetchOptions.body instanceof ArrayBuffer)) {
        
        fetchOptions.headers['Content-Type'] = 'application/json';
        fetchOptions.body = JSON.stringify(fetchOptions.body);
    }
    
    // Add timeout
    let controller;
    if (timeout) {
        controller = new AbortController();
        fetchOptions.signal = controller.signal;
        
        // Set timeout
        const timeoutId = setTimeout(() => {
            controller.abort();
        }, timeout);
        
        // Store timeout ID for cleanup
        fetchOptions._timeoutId = timeoutId;
    }
    
    // Retry logic
    let attempt = 0;
    let lastError = null;
    let response = null;
    
    while (attempt <= retries) {
        try {
            // Clear previous timeout if exists
            if (fetchOptions._timeoutId) {
                clearTimeout(fetchOptions._timeoutId);
            }
            
            // Set new timeout if needed
            if (timeout) {
                controller = new AbortController();
                fetchOptions.signal = controller.signal;
                
                const timeoutId = setTimeout(() => {
                    controller.abort();
                }, timeout);
                
                fetchOptions._timeoutId = timeoutId;
            }
            
            // Execute fetch
            response = await fetch(url, fetchOptions);
            
            // Handle auth errors (token expired or invalid)
            if (response.status === 401 && refreshOnUnauth) {
                // Try to refresh token
                const refreshed = await refreshToken();
                if (refreshed) {
                    // Update auth header with new token
                    fetchOptions.headers['Authorization'] = `Bearer ${tokenService.getAccessToken()}`;
                    
                    // Mark as retry to avoid infinite loop
                    fetchOptions._isRetry = true;
                    
                    // Retry the request with the new token
                    return await fetchWithAuth(url, fetchOptions);
                } else {
                    redirectToLogin();
                    return null;
                }
            }
            
            // Cache successful GET responses
            if (response.ok && cache && (!fetchOptions.method || fetchOptions.method === 'GET')) {
                // Clone response before using
                const clonedResponse = response.clone();
                
                try {
                    // Attempt to parse and cache
                    const data = await clonedResponse.json();
                    
                    // Create a response-like object that can be returned from cache
                    const cachedResponseObj = {
                        ok: true,
                        status: response.status,
                        statusText: response.statusText,
                        headers: response.headers,
                        json: async () => data,
                        text: async () => JSON.stringify(data),
                        clone: () => ({ ...cachedResponseObj }),
                        _cached: true
                    };
                    
                    // Store in cache
                    apiCache.set(cacheKey, cachedResponseObj, cacheTime);
                } catch (e) {
                    console.warn('Could not cache response:', e);
                }
            }
            
            // Handle general HTTP errors
            if (!response.ok) {
                // Retry server errors (5xx) but not client errors (4xx except 401 which is handled above)
                if (response.status >= 500 && attempt < retries) {
                    attempt++;
                    
                    // Wait before retry using exponential backoff if enabled
                    if (backoff) {
                        const delay = 1000 * Math.pow(2, attempt - 1);
                        console.log(`Request failed with ${response.status}, retrying in ${delay}ms...`);
                        await new Promise(resolve => setTimeout(resolve, delay));
                    } else {
                        console.log(`Request failed with ${response.status}, retrying immediately...`);
                    }
                    
                    continue;
                }
                
                // For non-retryable errors, show error message
                if (showErrors) {
                    try {
                        const errorData = await response.json();
                        showError(errorData.message || `Error: ${response.status} ${response.statusText}`);
                    } catch (e) {
                        showError(`Error: ${response.status} ${response.statusText}`);
                    }
                }
            }
            
            // Return the response
            return response;
            
        } catch (error) {
            // Clear timeout
            if (fetchOptions._timeoutId) {
                clearTimeout(fetchOptions._timeoutId);
            }
            
            lastError = error;
            
            // Handle abort errors (timeouts)
            if (error.name === 'AbortError') {
                console.warn(`Request timeout after ${timeout}ms:`, url);
                if (showErrors) {
                    showError('Request timed out. Please try again.');
                }
            } else {
                console.error('Fetch error:', error);
                if (showErrors) {
                    showError('Network error. Please check your connection.');
                }
            }
            
            // Retry on network errors
            if (attempt < retries) {
                attempt++;
                
                // Wait before retry using exponential backoff if enabled
                if (backoff) {
                    const delay = 1000 * Math.pow(2, attempt - 1);
                    console.log(`Request failed, retrying in ${delay}ms (${attempt}/${retries})...`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                } else {
                    console.log(`Request failed, retrying immediately (${attempt}/${retries})...`);
                }
                
                continue;
            }
            
            // If we get here, all retries failed
            throw error;
        }
    }
    
    // This should only be reached if all retries have been exhausted
    console.error('All fetch retries failed:', url, lastError);
    return response;
}

// Optimized date formatting with cache
const dateFormatter = (() => {
    const cache = new Map();
    const RTF = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
    
    return {
        // Format date/time with caching
        formatDateTime(dateString, options = {}) {
            if (!dateString) return 'N/A';
            
            // Generate cache key from dateString and options
            const cacheKey = `${dateString}-${JSON.stringify(options)}`;
            
            // Return from cache if available
            if (cache.has(cacheKey)) {
                return cache.get(cacheKey);
            }
            
            // Default options
            const defaultOptions = {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            };
            
            // Merge options
            const formatOptions = { ...defaultOptions, ...options };
            
            try {
                const date = new Date(dateString);
                const formatted = date.toLocaleString(undefined, formatOptions);
                
                // Cache result
                cache.set(cacheKey, formatted);
                return formatted;
            } catch (error) {
                console.error('Date formatting error:', error);
                return dateString || 'N/A';
            }
        },
        
        // Format relative time (e.g., "2 hours ago")
        formatTimeAgo(dateString) {
            if (!dateString) return 'N/A';
            
            try {
                const date = new Date(dateString);
                const now = new Date();
                const diffMs = now - date;
                
                if (isNaN(diffMs)) return 'Invalid date';
                
                // Less than a minute
                if (diffMs < 60 * 1000) return 'just now';
                
                // Less than an hour
                if (diffMs < 60 * 60 * 1000) {
                    const minutes = Math.floor(diffMs / (60 * 1000));
                    return RTF.format(-minutes, 'minute');
                }
                
                // Less than a day
                if (diffMs < 24 * 60 * 60 * 1000) {
                    const hours = Math.floor(diffMs / (60 * 60 * 1000));
                    return RTF.format(-hours, 'hour');
                }
                
                // Less than a week
                if (diffMs < 7 * 24 * 60 * 60 * 1000) {
                    const days = Math.floor(diffMs / (24 * 60 * 60 * 1000));
                    return RTF.format(-days, 'day');
                }
                
                // Fallback to date format for older dates
                return this.formatDateTime(dateString, { 
                    year: 'numeric', 
                    month: 'short', 
                    day: 'numeric' 
                });
            } catch (error) {
                console.error('Time ago formatting error:', error);
                return dateString || 'N/A';
            }
        },
        
        // Clear formatter cache
        clearCache() {
            cache.clear();
        }
    };
})();

// Export the format function for backward compatibility
function formatDateTime(dateString) {
    return dateFormatter.formatDateTime(dateString);
}

// Optimized bytes formatter with memoization
const bytesFormatter = (() => {
    const cache = new Map();
    
    return function formatBytes(bytes, decimals = 2) {
        // Handle edge cases
        if (bytes === 0 || bytes === null || bytes === undefined) return '0 Bytes';
        if (isNaN(parseFloat(bytes))) return 'Invalid size';
        
        // Ensure numeric value
        bytes = parseFloat(bytes);
        
        // Check cache for this exact call
        const cacheKey = `${bytes}-${decimals}`;
        if (cache.has(cacheKey)) {
            return cache.get(cacheKey);
        }
        
        // Calculate the appropriate unit
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];
        
        const i = Math.floor(Math.log(Math.abs(bytes)) / Math.log(k));
        const value = parseFloat((bytes / Math.pow(k, Math.min(i, sizes.length - 1))).toFixed(dm));
        const unit = sizes[Math.min(i, sizes.length - 1)];
        
        const result = `${value} ${unit}`;
        
        // Cache the result for future calls
        if (cache.size > 1000) { // Prevent unbounded growth
            for (const key of cache.keys()) {
                cache.delete(key);
                if (cache.size < 750) break; // Clear about 25%
            }
        }
        cache.set(cacheKey, result);
        
        return result;
    };
})();

// Export the format function for backward compatibility
function formatBytes(bytes, decimals = 2) {
    return bytesFormatter(bytes, decimals);
}

// Optimized traffic formatter with memoization
const trafficFormatter = (() => {
    const cache = new Map();
    
    return function formatTraffic(bitsPerSecond, decimals = 2) {
        // Handle edge cases
        if (bitsPerSecond === 0 || bitsPerSecond === null || bitsPerSecond === undefined) return '0 bps';
        if (isNaN(parseFloat(bitsPerSecond))) return 'Invalid rate';
        
        // Ensure numeric value
        bitsPerSecond = parseFloat(bitsPerSecond);
        
        // Check cache for this exact call
        const cacheKey = `${bitsPerSecond}-${decimals}`;
        if (cache.has(cacheKey)) {
            return cache.get(cacheKey);
        }
        
        // Calculate the appropriate unit
        const k = 1000; // Use 1000 for network speeds
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['bps', 'Kbps', 'Mbps', 'Gbps', 'Tbps'];
        
        const i = Math.floor(Math.log(Math.abs(bitsPerSecond)) / Math.log(k));
        const value = parseFloat((bitsPerSecond / Math.pow(k, Math.min(i, sizes.length - 1))).toFixed(dm));
        const unit = sizes[Math.min(i, sizes.length - 1)];
        
        const result = `${value} ${unit}`;
        
        // Cache the result for future calls
        if (cache.size > 1000) { // Prevent unbounded growth
            for (const key of cache.keys()) {
                cache.delete(key);
                if (cache.size < 750) break; // Clear about 25%
            }
        }
        cache.set(cacheKey, result);
        
        return result;
    };
})();

// Export the format function for backward compatibility
function formatTraffic(bitsPerSecond, decimals = 2) {
    return trafficFormatter(bitsPerSecond, decimals);
}

// Optimized notification system with debouncing
const notificationSystem = (() => {
    // Configuration
    const config = {
        maxNotifications: 3,     // Maximum simultaneous notifications
        defaultTimeout: 5000,    // Default timeout in ms
        debounceTime: 500,       // Debounce time for duplicate messages
        errorPrefix: '❌ ',      // Error icon
        successPrefix: '✅ ',    // Success icon
        warningPrefix: '⚠️ ',    // Warning icon
        infoPrefix: 'ℹ️ '        // Info icon
    };
    
    // State
    const state = {
        activeNotifications: new Set(),
        recentMessages: new Map(),
        toastContainer: null
    };
    
    // Helper method to create or get the toast container
    function getToastContainer() {
        if (state.toastContainer) return state.toastContainer;
        
        // Check if we have a toast container, if not create one
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(container);
        }
        
        state.toastContainer = container;
        return container;
    }
    
    // Helper to check for duplicate messages
    function isDuplicate(message, type) {
        const key = `${type}:${message}`;
        const now = Date.now();
        const lastTime = state.recentMessages.get(key);
        
        if (lastTime && (now - lastTime) < config.debounceTime) {
            return true;
        }
        
        // Update the last time for this message
        state.recentMessages.set(key, now);
        
        // Clean up old messages
        if (state.recentMessages.size > 100) {
            const oldEntries = [...state.recentMessages.entries()]
                .filter(([, time]) => now - time > config.debounceTime * 10)
                .map(([key]) => key);
                
            for (const key of oldEntries) {
                state.recentMessages.delete(key);
            }
        }
        
        return false;
    }
    
    // Helper to create a toast notification
    function createToast(message, type, options = {}) {
        // Don't create duplicates within debounce time
        if (isDuplicate(message, type)) {
            console.log(`Duplicate ${type} notification suppressed: ${message}`);
            return null;
        }
        
        // Remove oldest notification if we have too many
        if (state.activeNotifications.size >= config.maxNotifications) {
            const oldest = state.activeNotifications.values().next().value;
            if (oldest && oldest.remove) {
                oldest.remove();
                state.activeNotifications.delete(oldest);
            }
        }
        
        // Prepare toast content based on type
        let iconClass = '';
        let headerClass = '';
        let title = '';
        let prefix = '';
        
        switch (type) {
            case 'error':
                headerClass = 'bg-danger text-white';
                title = 'Error';
                prefix = config.errorPrefix;
                break;
            case 'success':
                headerClass = 'bg-success text-white';
                title = 'Success';
                prefix = config.successPrefix;
                break;
            case 'warning':
                headerClass = 'bg-warning text-dark';
                title = 'Warning';
                prefix = config.warningPrefix;
                break;
            case 'info':
                headerClass = 'bg-info text-white';
                title = 'Information';
                prefix = config.infoPrefix;
                break;
            default:
                headerClass = 'bg-secondary text-white';
                title = 'Notification';
        }
        
        // Create toast element
        const toastId = 'toast-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.id = toastId;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        // Add toast content
        toast.innerHTML = `
            <div class="toast-header ${headerClass}">
                <strong class="me-auto">${title}</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${prefix}${message}
            </div>
        `;
        
        // Add to container
        const container = getToastContainer();
        container.appendChild(toast);
        
        // Track active notification
        state.activeNotifications.add(toast);
        
        // Initialize toast
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: options.timeout || config.defaultTimeout
        });
        
        // Handle toast hidden event
        toast.addEventListener('hidden.bs.toast', () => {
            // Remove from active notifications
            state.activeNotifications.delete(toast);
            
            // Remove from DOM
            if (toast.parentNode) {
                toast.remove();
            }
        });
        
        // Show the toast
        bsToast.show();
        
        // Return the toast for reference
        return toast;
    }
    
    // Public API
    return {
        showError(message, options = {}) {
            return createToast(message, 'error', options);
        },
        
        showSuccess(message, options = {}) {
            return createToast(message, 'success', options);
        },
        
        showWarning(message, options = {}) {
            return createToast(message, 'warning', options);
        },
        
        showInfo(message, options = {}) {
            return createToast(message, 'info', options);
        },
        
        // Clear all notifications
        clearAll() {
            state.activeNotifications.forEach(toast => {
                // Use Bootstrap's hide method if available
                try {
                    const bsToast = bootstrap.Toast.getInstance(toast);
                    if (bsToast) bsToast.hide();
                } catch (e) {
                    // Fallback to direct removal
                    if (toast.parentNode) {
                        toast.remove();
                    }
                }
            });
            
            state.activeNotifications.clear();
        },
        
        // Update configuration
        configure(newConfig) {
            Object.assign(config, newConfig);
        }
    };
})();

// Export notification functions for backward compatibility
function showError(message, options = {}) {
    return notificationSystem.showError(message, options);
}

function showSuccess(message, options = {}) {
    return notificationSystem.showSuccess(message, options);
}

// Utility for performance measurement
const performanceTracker = (() => {
    const metrics = new Map();
    
    return {
        // Start timing
        start(label) {
            metrics.set(label, performance.now());
            return label;
        },
        
        // End timing and return duration
        end(label) {
            if (!metrics.has(label)) {
                console.warn(`No performance metric started for: ${label}`);
                return 0;
            }
            
            const startTime = metrics.get(label);
            const endTime = performance.now();
            const duration = endTime - startTime;
            
            metrics.delete(label);
            return duration;
        },
        
        // Log performance metric
        measure(label, thresholdMs = 100) {
            const duration = this.end(label);
            
            if (duration > thresholdMs) {
                console.warn(`Performance: ${label} took ${duration.toFixed(2)}ms`);
            } else {
                console.log(`Performance: ${label} took ${duration.toFixed(2)}ms`);
            }
            
            return duration;
        }
    };
})();

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    const perfLabel = performanceTracker.start('page-initialization');
    
    // Check authentication status on page load
    if (window.location.pathname !== '/auth/login') {
        if (!isAuthenticated()) {
            redirectToLogin();
        } else {
            // Update username in navbar if available
            const user = tokenService.getUser();
            if (user) {
                const usernameElement = document.getElementById('username');
                if (usernameElement && user.username) {
                    usernameElement.textContent = user.username;
                }
            }
            
            // Preemptively refresh token if it's close to expiry
            const token = tokenService.getAccessToken();
            if (token) {
                try {
                    const payload = tokenService.decodeToken(token);
                    if (payload && payload.exp) {
                        const expiryTime = payload.exp * 1000;
                        const timeUntilExpiry = expiryTime - Date.now();
                        
                        // If token expires in less than 5 minutes, refresh it
                        if (timeUntilExpiry > 0 && timeUntilExpiry < 5 * 60 * 1000) {
                            console.log('Token expires soon, refreshing preemptively');
                            refreshToken().catch(error => {
                                console.error('Preemptive token refresh failed:', error);
                            });
                        }
                    }
                } catch (error) {
                    console.error('Error checking token expiry:', error);
                }
            }
        }
    } else {
        // On login page, check for return URL
        const returnUrl = sessionStorage.getItem('returnUrl');
        if (returnUrl) {
            // Store it in a form field if it exists
            const returnUrlField = document.querySelector('input[name="returnUrl"]');
            if (returnUrlField) {
                returnUrlField.value = returnUrl;
            }
        }
    }
    
    performanceTracker.measure(perfLabel);
});
