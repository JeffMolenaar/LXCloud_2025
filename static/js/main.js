// LXCloud Main JavaScript

// Global variables
let refreshInterval;
let isRefreshing = false;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize real-time updates
    initializeRealTimeUpdates();
    
    // Initialize form validations
    initializeFormValidations();
    
    // Initialize auto-refresh
    startAutoRefresh();
}

function initializeTooltips() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function initializeRealTimeUpdates() {
    // Update controller status indicators
    updateControllerStatus();
    
    // Update dashboard statistics
    updateDashboardStats();
}

function initializeFormValidations() {
    // Add custom form validation
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

function startAutoRefresh() {
    // Refresh data every 30 seconds
    refreshInterval = setInterval(function() {
        if (!isRefreshing) {
            refreshDashboardData();
        }
    }, 30000);
}

function refreshDashboardData() {
    if (isRefreshing) return;
    
    isRefreshing = true;
    
    // Update controller status
    updateControllerStatus();
    
    // Update statistics
    updateDashboardStats();
    
    setTimeout(() => {
        isRefreshing = false;
    }, 1000);
}

function updateControllerStatus() {
    // Only update if user is authenticated
    if (!document.querySelector('.navbar')) {
        console.log('User not authenticated, skipping controller status update');
        return;
    }
    
    fetch('/api/controllers/status')
        .then(response => {
            if (!response.ok) {
                throw new Error('Not authenticated or API unavailable');
            }
            return response.json();
        })
        .then(data => {
            data.forEach(controller => {
                updateControllerStatusIndicator(controller);
            });
        })
        .catch(error => {
            console.log('Controller status update skipped:', error.message);
        });
}

function updateControllerStatusIndicator(controller) {
    // Update status indicators on the page
    const statusElements = document.querySelectorAll(`[data-controller-id="${controller.id}"]`);
    
    statusElements.forEach(element => {
        const statusClass = controller.is_online ? 'status-online' : 'status-offline';
        const statusBadge = element.querySelector('.status-badge');
        const statusIndicator = element.querySelector('.controller-status');
        
        if (statusBadge) {
            statusBadge.className = `badge ${controller.is_online ? 'bg-success' : 'bg-danger'}`;
            statusBadge.innerHTML = `<i class="fas fa-circle"></i> ${controller.is_online ? 'Online' : 'Offline'}`;
        }
        
        if (statusIndicator) {
            statusIndicator.className = `controller-status ${statusClass}`;
        }
    });
}

function updateDashboardStats() {
    // Only update if user is authenticated
    if (!document.querySelector('.navbar')) {
        console.log('User not authenticated, skipping dashboard stats update');
        return;
    }
    
    fetch('/api/stats/overview')
        .then(response => {
            if (!response.ok) {
                throw new Error('Not authenticated or API unavailable');
            }
            return response.json();
        })
        .then(data => {
            // Update statistics cards
            updateStatCard('total-controllers', data.total_controllers);
            updateStatCard('online-controllers', data.online_controllers);
            updateStatCard('offline-controllers', data.offline_controllers);
            
            if (data.total_users !== null) {
                updateStatCard('total-users', data.total_users);
            }
            
            if (data.unbound_controllers !== null) {
                updateStatCard('unbound-controllers', data.unbound_controllers);
            }
        })
        .catch(error => {
            console.log('Dashboard stats update skipped:', error.message);
        });
}

function updateStatCard(cardId, value) {
    const element = document.getElementById(cardId);
    if (element) {
        element.textContent = value;
        
        // Add animation effect
        element.style.transform = 'scale(1.1)';
        setTimeout(() => {
            element.style.transform = 'scale(1)';
        }, 200);
    }
}

// Utility functions
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alert-container') || createAlertContainer();
    
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type} alert-dismissible fade show`;
    alertElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alertElement);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertElement.parentNode) {
            alertElement.remove();
        }
    }, 5000);
}

function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alert-container';
    container.className = 'container-fluid mt-3';
    
    const main = document.querySelector('main');
    if (main) {
        main.insertBefore(container, main.firstChild);
    }
    
    return container;
}

function addLoadingState(element) {
    if (element) {
        element.classList.add('loading');
        element.disabled = true;
    }
}

function removeLoadingState(element) {
    if (element) {
        element.classList.remove('loading');
        element.disabled = false;
    }
}

// Controller-specific functions
function bindController(serialNumber) {
    const formData = new FormData();
    formData.append('serial_number', serialNumber);
    
    fetch('/controllers/bind', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            showAlert('Controller bound successfully!', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            response.text().then(text => {
                showAlert('Error binding controller: ' + text, 'danger');
            });
        }
    })
    .catch(error => {
        showAlert('Error binding controller: ' + error.message, 'danger');
    });
}

function unbindController(controllerId) {
    if (!confirm('Are you sure you want to unbind this controller?')) {
        return;
    }
    
    fetch(`/controllers/${controllerId}/unbind`, {
        method: 'POST'
    })
    .then(response => {
        if (response.ok) {
            showAlert('Controller unbound successfully!', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showAlert('Error unbinding controller', 'danger');
        }
    })
    .catch(error => {
        showAlert('Error unbinding controller: ' + error.message, 'danger');
    });
}

// Map utilities
function initializeMap(elementId, options = {}) {
    const defaultOptions = {
        center: [52.3676, 4.9041], // Default to Netherlands
        zoom: 8,
        zoomControl: true,
        scrollWheelZoom: true
    };
    
    const mapOptions = Object.assign(defaultOptions, options);
    const map = L.map(elementId, mapOptions);
    
    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    return map;
}

// Global marker configuration
let markerConfig = null;

// Load marker configuration from server
async function loadMarkerConfig() {
    try {
        const response = await fetch('/admin/api/marker-config');
        if (response.ok) {
            markerConfig = await response.json();
            console.log('Marker configuration loaded:', markerConfig);
        } else {
            console.warn('Failed to load marker configuration, using defaults');
            markerConfig = getDefaultMarkerConfig();
        }
    } catch (error) {
        console.warn('Error loading marker configuration:', error);
        markerConfig = getDefaultMarkerConfig();
    }
}

// Default marker configuration
function getDefaultMarkerConfig() {
    return {
        speedradar: {
            online: { icon: 'fas fa-tachometer-alt', color: '#17a2b8', size: '30' },
            offline: { icon: 'fas fa-tachometer-alt', color: '#dc3545', size: '30' }
        },
        beaufortmeter: {
            online: { icon: 'fas fa-wind', color: '#28a745', size: '30' },
            offline: { icon: 'fas fa-wind', color: '#dc3545', size: '30' }
        },
        weatherstation: {
            online: { icon: 'fas fa-cloud-sun', color: '#ffc107', size: '30' },
            offline: { icon: 'fas fa-cloud-sun', color: '#dc3545', size: '30' }
        },
        aicamera: {
            online: { icon: 'fas fa-camera', color: '#dc3545', size: '30' },
            offline: { icon: 'fas fa-camera', color: '#6c757d', size: '30' }
        },
        default: {
            online: { icon: 'fas fa-microchip', color: '#6c757d', size: '30' },
            offline: { icon: 'fas fa-microchip', color: '#dc3545', size: '30' }
        }
    };
}

function createControllerMarker(controller, map) {
    // Ensure marker config is loaded
    if (!markerConfig) {
        markerConfig = getDefaultMarkerConfig();
    }
    
    const controllerType = controller.type || 'default';
    const isOnline = controller.is_online;
    const state = isOnline ? 'online' : 'offline';
    
    // Get marker configuration for this controller type and state
    const typeConfig = markerConfig[controllerType] || markerConfig.default;
    const stateConfig = typeConfig[state];
    
    const iconSize = parseInt(stateConfig.size) || 30;
    const icon = L.divIcon({
        html: `<i class="${stateConfig.icon}" style="color: ${stateConfig.color};"></i>`,
        iconSize: [iconSize, iconSize],
        className: `custom-div-icon custom-marker-${controllerType}-${state}`,
        iconAnchor: [iconSize / 2, iconSize / 2]
    });
    
    const marker = L.marker([controller.latitude, controller.longitude], { icon: icon }).addTo(map);
    
    // Create popup content
    const popupContent = `
        <div class="marker-popup">
            <h6>${controller.name}</h6>
            <p class="mb-1">
                <span class="controller-status ${controller.is_online ? 'status-online' : 'status-offline'}"></span>
                ${controller.is_online ? 'Online' : 'Offline'}
            </p>
            <p class="mb-1"><strong>Type:</strong> ${controller.type.charAt(0).toUpperCase() + controller.type.slice(1)}</p>
            <p class="mb-1"><strong>Serial:</strong> ${controller.serial_number}</p>
            ${controller.last_seen ? `<p class="mb-2"><strong>Last Seen:</strong> ${new Date(controller.last_seen).toLocaleString()}</p>` : ''}
            <div class="text-center">
                <a href="/controllers/${controller.id}/data" class="btn btn-sm btn-primary">
                    <i class="fas fa-chart-line"></i> View Data
                </a>
                <a href="/controllers/${controller.id}/edit" class="btn btn-sm btn-outline-secondary">
                    <i class="fas fa-edit"></i> Edit
                </a>
            </div>
        </div>
    `;
    
    marker.bindPopup(popupContent);
    return marker;
}

// Format utilities
function formatDateTime(dateString) {
    if (!dateString) return 'Never';
    
    const date = new Date(dateString);
    return date.toLocaleString();
}

function formatControllerType(type) {
    const types = {
        speedradar: 'Speed Radar',
        beaufortmeter: 'Beaufort Meter',
        weatherstation: 'Weather Station',
        aicamera: 'AI Camera'
    };
    
    return types[type] || type.charAt(0).toUpperCase() + type.slice(1);
}

// Export for global access
window.LXCloud = {
    showAlert,
    addLoadingState,
    removeLoadingState,
    bindController,
    unbindController,
    initializeMap,
    createControllerMarker,
    formatDateTime,
    formatControllerType,
    refreshDashboardData,
    loadMarkerConfig,
    getDefaultMarkerConfig
};