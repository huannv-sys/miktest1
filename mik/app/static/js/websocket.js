/**
 * WebSocket JavaScript for MikroTik Monitoring System
 * Handles real-time updates via WebSocket connection
 */

// WebSocket connection
let socket = null;

// Setup WebSocket connection
function setupWebSocket() {
    // Check if WebSocket is already connected
    if (socket && socket.readyState === WebSocket.OPEN) {
        return;
    }
    
    // Create WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const socketUrl = `${protocol}//${host}/socket.io/?EIO=3&transport=websocket`;
    
    try {
        // Create WebSocket connection
        socket = new WebSocket(socketUrl);
        
        // Connection opened
        socket.addEventListener('open', function(event) {
            console.log('WebSocket connection established');
            
            // Send authentication if available
            const token = localStorage.getItem('access_token');
            if (token) {
                socket.send(JSON.stringify({
                    type: 'authenticate',
                    token: token
                }));
            }
        });
        
        // Listen for messages
        socket.addEventListener('message', function(event) {
            try {
                // Parse message data
                let data = event.data;
                
                // Handle Socket.IO engine.io handshake and ping packets
                if (data === '0') {
                    // Handshake response
                    return;
                } else if (data === '3') {
                    // Ping from server, respond with pong
                    socket.send('2');
                    return;
                } else if (data === '40') {
                    // Socket.IO connection established
                    return;
                } else if (data === '41') {
                    // Socket.IO disconnection
                    return;
                } else if (data === '42["connect"]') {
                    // Socket.IO connection event
                    return;
                }
                
                // Handle data messages (typically starts with 42[...]
                if (data.startsWith('42')) {
                    data = data.substring(2);
                    const parsedData = JSON.parse(data);
                    if (Array.isArray(parsedData) && parsedData.length >= 2) {
                        const eventName = parsedData[0];
                        const eventData = parsedData[1];
                        
                        // Handle different event types
                        if (eventName === 'device_update') {
                            // Device update event
                            handleDeviceUpdateEvent(eventData);
                        } else if (eventName === 'alert') {
                            // Alert event
                            handleAlertEvent(eventData);
                        }
                    }
                    return;
                }
                
                // For direct message passing without Socket.IO protocol
                handleWebSocketMessage({
                    data: data
                });
            } catch (error) {
                console.error('Error handling WebSocket message:', error);
            }
        });
        
        // Connection closed
        socket.addEventListener('close', function(event) {
            console.log('WebSocket connection closed');
            
            // Reconnect after a delay
            setTimeout(setupWebSocket, 5000);
        });
        
        // Connection error
        socket.addEventListener('error', function(event) {
            console.error('WebSocket error:', event);
            
            // Close the connection to trigger reconnect
            socket.close();
        });
    } catch (error) {
        console.error('Error setting up WebSocket:', error);
    }
}

// Handle device update event
function handleDeviceUpdateEvent(data) {
    try {
        // Create a message object for the page-specific handler
        const message = {
            data: JSON.stringify({
                type: 'device_update',
                device_id: data.device_id,
                metrics: data.metrics
            })
        };
        
        // Pass to page-specific handler if it exists
        if (typeof handleWebSocketMessage === 'function') {
            handleWebSocketMessage(message);
        }
    } catch (error) {
        console.error('Error handling device update event:', error);
    }
}

// Handle alert event
function handleAlertEvent(data) {
    try {
        // Create a message object for the page-specific handler
        const message = {
            data: JSON.stringify({
                type: 'alert',
                alert: data
            })
        };
        
        // Pass to page-specific handler if it exists
        if (typeof handleWebSocketMessage === 'function') {
            handleWebSocketMessage(message);
        }
        
        // Show alert notification
        showAlertNotification(data);
    } catch (error) {
        console.error('Error handling alert event:', error);
    }
}

// Show alert notification
function showAlertNotification(alert) {
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
    
    // Format timestamp
    const timestamp = new Date(alert.timestamp).toLocaleTimeString();
    
    // Add toast content
    toast.innerHTML = `
        <div class="toast-header bg-danger text-white">
            <strong class="me-auto">Alert: ${alert.rule_name || 'System Alert'}</strong>
            <small>${timestamp}</small>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            <strong>${alert.device_name || 'Unknown device'}</strong>: ${alert.metric} ${alert.condition} ${alert.threshold}<br>
            Current value: ${alert.value}
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

// Request device update via WebSocket
function requestDeviceUpdate(deviceId) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: 'request_update',
            device_id: deviceId
        }));
    }
}
