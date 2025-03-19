/**
 * Loading Animations for Network Data
 * Provides playful and informative loading animations for various network data components
 */

class LoadingAnimations {
    /**
     * Initialize the loading animations manager
     */
    constructor() {
        this.activeAnimations = new Map();
        this.initializeEventListeners();
    }

    /**
     * Initialize event listeners
     */
    initializeEventListeners() {
        // Listen for custom events that might trigger loading states
        document.addEventListener('data-loading-start', (e) => {
            const { containerId, type, message } = e.detail;
            this.showLoading(containerId, type, message);
        });

        document.addEventListener('data-loading-end', (e) => {
            const { containerId } = e.detail;
            this.hideLoading(containerId);
        });
    }

    /**
     * Show a loading animation in the specified container
     * @param {string} containerId - The ID of the container to show loading in
     * @param {string} type - Type of loading animation (network, vpn, scan, traffic, data, dots)
     * @param {string} message - Optional message to display
     */
    showLoading(containerId, type = 'dots', message = 'Đang tải dữ liệu...') {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container with ID ${containerId} not found`);
            return;
        }

        // Store original content
        const originalContent = container.innerHTML;
        this.activeAnimations.set(containerId, originalContent);

        // Create loading animation
        const loadingHtml = this.createLoadingAnimation(type, message);
        container.innerHTML = loadingHtml;

        // Add animation-specific behaviors
        if (type === 'network') {
            this.initNetworkAnimation(container);
        }
    }

    /**
     * Hide loading animation and restore original content
     * @param {string} containerId - The ID of the container
     */
    hideLoading(containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container with ID ${containerId} not found`);
            return;
        }

        // Restore original content if it exists
        if (this.activeAnimations.has(containerId)) {
            const originalContent = this.activeAnimations.get(containerId);
            container.innerHTML = originalContent;
            this.activeAnimations.delete(containerId);
        }
    }

    /**
     * Create HTML for a loading animation
     * @param {string} type - Animation type
     * @param {string} message - Loading message
     * @returns {string} HTML string
     */
    createLoadingAnimation(type, message) {
        let animationHtml = '';

        switch (type) {
            case 'network':
                animationHtml = `
                    <div class="loading-container">
                        <div class="network-loading">
                            <div class="network-node"></div>
                            <div class="network-node"></div>
                            <div class="network-node"></div>
                            <div class="network-node"></div>
                            <div class="network-node"></div>
                            <div id="network-links"></div>
                        </div>
                        <span class="loading-text">${message}</span>
                    </div>
                `;
                break;

            case 'vpn':
                animationHtml = `
                    <div class="loading-container">
                        <div class="vpn-loading"></div>
                        <span class="loading-text">${message}</span>
                    </div>
                `;
                break;

            case 'scan':
                animationHtml = `
                    <div class="loading-container">
                        <div class="scan-loading">
                            <div class="scan-line"></div>
                            <div class="scan-dot"></div>
                        </div>
                        <span class="loading-text">${message}</span>
                    </div>
                `;
                break;

            case 'traffic':
                animationHtml = `
                    <div class="loading-container">
                        <div class="traffic-loading">
                            <div class="traffic-arrow-container">
                                <div class="traffic-incoming-arrow"></div>
                                <div class="traffic-outgoing-arrow"></div>
                            </div>
                        </div>
                        <span class="loading-text">${message}</span>
                    </div>
                `;
                break;

            case 'data':
                animationHtml = `
                    <div class="loading-container">
                        <div class="data-loading">
                            <div class="data-loading-progress"></div>
                        </div>
                        <span class="loading-text">${message}</span>
                    </div>
                `;
                break;

            case 'grid':
                animationHtml = `
                    <div class="loading-container">
                        <div class="grid-loading">
                            ${Array(16).fill('<div class="grid-item"></div>').join('')}
                        </div>
                        <span class="loading-text">${message}</span>
                    </div>
                `;
                break;

            case 'dots':
            default:
                animationHtml = `
                    <div class="loading-container">
                        <div class="dots-loading">
                            <div class="dot"></div>
                            <div class="dot"></div>
                            <div class="dot"></div>
                        </div>
                        <span class="loading-text">${message}</span>
                    </div>
                `;
                break;
        }

        return animationHtml;
    }

    /**
     * Initialize the network animation with dynamic links
     * @param {HTMLElement} container - The container element
     */
    initNetworkAnimation(container) {
        const networkLoading = container.querySelector('.network-loading');
        if (!networkLoading) return;

        const nodes = networkLoading.querySelectorAll('.network-node');
        const linksContainer = networkLoading.querySelector('#network-links');

        // Create links between nodes
        if (linksContainer && nodes.length > 0) {
            // Get first (center) node position as reference
            const centerNode = nodes[0];
            const centerRect = centerNode.getBoundingClientRect();
            const containerRect = networkLoading.getBoundingClientRect();
            
            const centerX = centerRect.left - containerRect.left + centerRect.width / 2;
            const centerY = centerRect.top - containerRect.top + centerRect.height / 2;
            
            // Create links from center to each satellite node
            for (let i = 1; i < nodes.length; i++) {
                const node = nodes[i];
                const nodeRect = node.getBoundingClientRect();
                
                const nodeX = nodeRect.left - containerRect.left + nodeRect.width / 2;
                const nodeY = nodeRect.top - containerRect.top + nodeRect.height / 2;
                
                // Calculate angle and distance
                const dx = nodeX - centerX;
                const dy = nodeY - centerY;
                const angle = Math.atan2(dy, dx) * 180 / Math.PI;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                // Create link
                const link = document.createElement('div');
                link.className = 'network-link';
                link.style.width = `${distance}px`;
                link.style.left = `${centerX}px`;
                link.style.top = `${centerY}px`;
                link.style.transform = `rotate(${angle}deg)`;
                
                linksContainer.appendChild(link);
                
                // Add data packet
                this.createDataPacket(networkLoading, centerX, centerY, nodeX, nodeY);
            }
        }
    }

    /**
     * Create animated data packet
     * @param {HTMLElement} container - The network container
     * @param {number} x1 - Start X position
     * @param {number} y1 - Start Y position
     * @param {number} x2 - End X position
     * @param {number} y2 - End Y position
     */
    createDataPacket(container, x1, y1, x2, y2) {
        const packet = document.createElement('div');
        packet.className = 'data-packet';
        container.appendChild(packet);

        // Animation duration between 1.5 and 3 seconds
        const duration = 1500 + Math.random() * 1500;
        const startTime = Date.now();
        
        // Animate the packet
        const animatePacket = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Linear interpolation between points
            const x = x1 + (x2 - x1) * progress;
            const y = y1 + (y2 - y1) * progress;
            
            packet.style.left = `${x}px`;
            packet.style.top = `${y}px`;
            
            if (progress < 1) {
                requestAnimationFrame(animatePacket);
            } else {
                // When packet reaches destination, start over
                setTimeout(() => {
                    packet.style.left = `${x1}px`;
                    packet.style.top = `${y1}px`;
                    requestAnimationFrame(() => this.createDataPacket(container, x1, y1, x2, y2));
                }, Math.random() * 1000); // Random delay before restarting
                
                // Remove the old packet
                setTimeout(() => {
                    container.removeChild(packet);
                }, 100);
            }
        };
        
        requestAnimationFrame(animatePacket);
    }

    /**
     * Helper to disperse loading animations across page
     * Replaces all elements with the specified class with loading animations
     * @param {string} className - Class name to target
     * @param {string[]} types - Array of animation types to use
     */
    replaceLoadingPlaceholders(className = 'loading-placeholder', types = ['dots', 'network', 'vpn', 'scan', 'traffic', 'data', 'grid']) {
        const placeholders = document.querySelectorAll(`.${className}`);
        placeholders.forEach((placeholder, index) => {
            const type = types[index % types.length];
            const message = placeholder.getAttribute('data-loading-message') || 'Đang tải...';
            const loadingHtml = this.createLoadingAnimation(type, message);
            placeholder.innerHTML = loadingHtml;
            
            if (type === 'network') {
                this.initNetworkAnimation(placeholder);
            }
        });
    }
}

// Initialize loading animations when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.loadingAnimations = new LoadingAnimations();
    
    // Replace any loading placeholders in the page
    window.loadingAnimations.replaceLoadingPlaceholders();
});

/**
 * Utility functions for working with loading animations
 */

/**
 * Show loading animation in an element
 * @param {string} elementId - The element ID
 * @param {string} type - Animation type
 * @param {string} message - Loading message
 */
function showLoading(elementId, type = 'dots', message = 'Đang tải dữ liệu...') {
    if (window.loadingAnimations) {
        window.loadingAnimations.showLoading(elementId, type, message);
    } else {
        console.error('Loading animations not initialized');
    }
}

/**
 * Hide loading animation from an element
 * @param {string} elementId - The element ID
 */
function hideLoading(elementId) {
    if (window.loadingAnimations) {
        window.loadingAnimations.hideLoading(elementId);
    } else {
        console.error('Loading animations not initialized');
    }
}

/**
 * Wrap fetch API to automatically show/hide loading animations
 * @param {string} url - URL to fetch
 * @param {Object} options - Fetch options
 * @param {string} elementId - Element ID to show loading in
 * @param {string} type - Animation type
 * @param {string} message - Loading message
 * @returns {Promise} - Fetch promise
 */
function fetchWithLoading(url, options = {}, elementId, type = 'dots', message = 'Đang tải dữ liệu...') {
    showLoading(elementId, type, message);
    
    return fetch(url, options)
        .then(response => {
            hideLoading(elementId);
            return response;
        })
        .catch(error => {
            hideLoading(elementId);
            throw error;
        });
}