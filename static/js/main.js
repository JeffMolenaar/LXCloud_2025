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
    fetch('/api/controllers/status')
        .then(response => response.json())
        .then(data => {
            data.forEach(controller => {
                updateControllerStatusIndicator(controller);
            });
        })
        .catch(error => {
            console.error('Error updating controller status:', error);
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
    fetch('/api/stats/overview')
        .then(response => response.json())
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
            console.error('Error updating dashboard stats:', error);
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

function createControllerMarker(controller, map) {
    const markerIcons = {
        speedradar: L.divIcon({
            html: '<i class="fas fa-tachometer-alt"></i>',
            iconSize: [30, 30],
            className: 'custom-div-icon custom-marker-speedradar'
        }),
        beaufortmeter: L.divIcon({
            html: '<i class="fas fa-wind"></i>',
            iconSize: [30, 30],
            className: 'custom-div-icon custom-marker-beaufortmeter'
        }),
        weatherstation: L.divIcon({
            html: '<i class="fas fa-cloud-sun"></i>',
            iconSize: [30, 30],
            className: 'custom-div-icon custom-marker-weatherstation'
        }),
        aicamera: L.divIcon({
            html: '<i class="fas fa-camera"></i>',
            iconSize: [30, 30],
            className: 'custom-div-icon custom-marker-aicamera'
        }),
        default: L.divIcon({
            html: '<i class="fas fa-microchip"></i>',
            iconSize: [30, 30],
            className: 'custom-div-icon custom-marker-default'
        })
    };
    
    const icon = markerIcons[controller.type] || markerIcons.default;
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
    refreshDashboardData
};