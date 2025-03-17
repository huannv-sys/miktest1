/**
 * Network Map Visualization
 * Uses D3.js to create an interactive network topology visualization
 */

// Global variables
let networkMap;
let simulation;
let svg;
let width;
let height;
let nodesData = [];
let linksData = [];
let nodeElements;
let linkElements;
let labelElements;
let zoomHandler;

/**
 * Initialize the network map
 */
function initNetworkMap() {
    // Get container dimensions
    const container = document.getElementById('network-map-container');
    width = container.clientWidth;
    height = container.clientHeight || 500; // Default height if not set
    
    // Create SVG
    svg = d3.select('#network-map-container')
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('class', 'network-map');
    
    // Add zoom capabilities
    zoomHandler = d3.zoom()
        .on('zoom', (event) => {
            svg.select('g').attr('transform', event.transform);
        });
    
    svg.call(zoomHandler);
    
    // Create a group for the network elements
    networkMap = svg.append('g');
    
    // Create legend
    createLegend();
    
    // Load initial data
    loadNetworkData();
    
    // Set up window resize handler
    window.addEventListener('resize', handleResize);
}

/**
 * Handle window resize events
 */
function handleResize() {
    const container = document.getElementById('network-map-container');
    width = container.clientWidth;
    height = container.clientHeight || 500;
    
    svg.attr('width', width)
       .attr('height', height);
    
    if (simulation) {
        simulation.force('center', d3.forceCenter(width / 2, height / 2))
                 .restart();
    }
}

/**
 * Create a legend for the network map
 */
function createLegend() {
    const legend = svg.append('g')
        .attr('class', 'legend')
        .attr('transform', 'translate(20, 20)');
    
    // Router icon
    legend.append('circle')
        .attr('r', 8)
        .attr('cx', 10)
        .attr('cy', 10)
        .attr('class', 'node-router');
    
    legend.append('text')
        .attr('x', 25)
        .attr('y', 14)
        .text('Router');
    
    // Wireless link
    legend.append('line')
        .attr('x1', 0)
        .attr('y1', 40)
        .attr('x2', 20)
        .attr('y2', 40)
        .attr('class', 'link-wireless');
    
    legend.append('text')
        .attr('x', 25)
        .attr('y', 44)
        .text('Wireless Link');
    
    // Wired link
    legend.append('line')
        .attr('x1', 0)
        .attr('y1', 70)
        .attr('x2', 20)
        .attr('y2', 70)
        .attr('class', 'link-wired');
    
    legend.append('text')
        .attr('x', 25)
        .attr('y', 74)
        .text('Wired Link');
}

/**
 * Load network map data from API
 */
async function loadNetworkData() {
    try {
        showLoading();
        
        const response = await apiClient.getNetworkMap();
        
        updateNetworkMapData(response);
        renderNetworkMap();
        
        hideLoading();
    } catch (error) {
        console.error('Error loading network map data:', error);
        hideLoading();
        showError('Error loading network map: ' + error.message);
    }
}

/**
 * Refresh network map data
 */
function refreshNetworkMap() {
    loadNetworkData();
}

/**
 * Update network map data
 * @param {object} data - Network map data
 */
function updateNetworkMapData(data) {
    nodesData = data.nodes || [];
    linksData = data.links || [];
    
    // Process nodes to add type and color
    nodesData.forEach(node => {
        // Set default node properties if not provided
        node.radius = node.radius || 12;
        node.color = node.color || getNodeColor(node.type || 'router');
        node.group = node.group || 1;
    });
    
    // Process links to add strength and type
    linksData.forEach(link => {
        // Set default link properties if not provided
        link.value = link.value || 1;
        link.type = link.type || 'wired';
    });
}

/**
 * Get color for node based on type
 * @param {string} type - Node type
 * @returns {string} - Color value
 */
function getNodeColor(type) {
    switch (type) {
        case 'router':
            return '#3498db';
        case 'switch':
            return '#2ecc71';
        case 'ap':
            return '#f39c12';
        case 'client':
            return '#95a5a6';
        default:
            return '#3498db';
    }
}

/**
 * Render the network map with current data
 */
function renderNetworkMap() {
    // Clear previous elements
    networkMap.selectAll('*').remove();
    
    // Add link elements
    linkElements = networkMap.append('g')
        .attr('class', 'links')
        .selectAll('line')
        .data(linksData)
        .enter()
        .append('line')
        .attr('class', d => `link ${d.type ? 'link-' + d.type : 'link-wired'}`)
        .attr('stroke-width', d => Math.sqrt(d.value));
    
    // Add node elements
    nodeElements = networkMap.append('g')
        .attr('class', 'nodes')
        .selectAll('circle')
        .data(nodesData)
        .enter()
        .append('circle')
        .attr('r', d => d.radius)
        .attr('fill', d => d.color)
        .attr('class', d => `node node-${d.type || 'router'}`)
        .call(drag(simulation))
        .on('click', handleNodeClick)
        .on('mouseover', handleNodeMouseOver)
        .on('mouseout', handleNodeMouseOut);
    
    // Add label elements
    labelElements = networkMap.append('g')
        .attr('class', 'labels')
        .selectAll('text')
        .data(nodesData)
        .enter()
        .append('text')
        .text(d => d.name)
        .attr('class', 'node-label')
        .attr('font-size', 12)
        .attr('dx', 15)
        .attr('dy', 4);
    
    // Create force simulation
    simulation = d3.forceSimulation(nodesData)
        .force('link', d3.forceLink(linksData).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(30))
        .on('tick', ticked);
    
    // Center the view
    const initialTransform = d3.zoomIdentity.translate(width/2, height/2).scale(0.8);
    svg.call(zoomHandler.transform, initialTransform);
    
    // Function to update positions on each tick
    function ticked() {
        linkElements
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        nodeElements
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);
        
        labelElements
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    }
}

/**
 * Handle node click event
 * @param {event} event - Click event
 * @param {object} d - Node data
 */
function handleNodeClick(event, d) {
    // Prevent event bubbling
    event.stopPropagation();
    
    // Show device details
    if (typeof showDeviceDetails === 'function') {
        showDeviceDetails(d.id);
    } else {
        console.log('Device details:', d);
    }
}

/**
 * Handle node mouseover event
 * @param {event} event - Mouseover event
 * @param {object} d - Node data
 */
function handleNodeMouseOver(event, d) {
    // Highlight the node
    d3.select(event.currentTarget)
        .attr('r', d => d.radius * 1.2)
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);
    
    // Show tooltip with device info
    const tooltip = d3.select('#network-map-tooltip');
    tooltip.html(`
        <strong>${d.name}</strong><br>
        IP: ${d.ip_address}<br>
        Model: ${d.model || 'Unknown'}<br>
        Click for details
    `);
    
    // Position the tooltip
    const bounds = event.currentTarget.getBoundingClientRect();
    const mapContainer = document.getElementById('network-map-container');
    const containerBounds = mapContainer.getBoundingClientRect();
    
    tooltip.style('left', (bounds.x - containerBounds.x + bounds.width/2) + 'px')
           .style('top', (bounds.y - containerBounds.y - 70) + 'px')
           .style('opacity', 1);
}

/**
 * Handle node mouseout event
 * @param {event} event - Mouseout event
 * @param {object} d - Node data
 */
function handleNodeMouseOut(event, d) {
    // Restore node appearance
    d3.select(event.currentTarget)
        .attr('r', d => d.radius)
        .attr('stroke', null)
        .attr('stroke-width', null);
    
    // Hide tooltip
    d3.select('#network-map-tooltip')
        .style('opacity', 0);
}

/**
 * Create a drag behavior for nodes
 * @param {object} simulation - Force simulation
 * @returns {object} - Drag behavior
 */
function drag(simulation) {
    function dragstarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
    }
    
    function dragged(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
    }
    
    function dragended(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
    }
    
    return d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended);
}

/**
 * Show loading indicator
 */
function showLoading() {
    const loadingEl = document.getElementById('network-map-loading');
    if (loadingEl) {
        loadingEl.style.display = 'flex';
    }
}

/**
 * Hide loading indicator
 */
function hideLoading() {
    const loadingEl = document.getElementById('network-map-loading');
    if (loadingEl) {
        loadingEl.style.display = 'none';
    }
}

/**
 * Show error message
 * @param {string} message - Error message
 */
function showError(message) {
    const errorEl = document.getElementById('network-map-error');
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.style.display = 'block';
        
        // Hide after 5 seconds
        setTimeout(() => {
            errorEl.style.display = 'none';
        }, 5000);
    }
}

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('network-map-container')) {
        initNetworkMap();
    }
});