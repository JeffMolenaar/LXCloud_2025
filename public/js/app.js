// LXCloud Frontend JavaScript

// Global variables
let socket = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize Socket.IO if available
    if (typeof io !== 'undefined') {
        socket = io();
        setupSocketListeners();
    }
    
    // Initialize common components
    initializeTooltips();
    initializeModals();
    initializeFormatting();
    
    // Initialize page-specific components
    const currentPage = getCurrentPage();
    switch(currentPage) {
        case 'dashboard':
            initializeDashboard();
            break;
        case 'map':
            initializeMap();
            break;
        case 'controllers':
            initializeControllers();
            break;
        case 'analytics':
            initializeAnalytics();
            break;
    }
}

function getCurrentPage() {
    const path = window.location.pathname;
    if (path.includes('/dashboard/map')) return 'map';
    if (path.includes('/dashboard/analytics')) return 'analytics';
    if (path.includes('/dashboard/controller')) return 'controller-details';
    if (path.includes('/dashboard')) return 'dashboard';
    if (path.includes('/controllers')) return 'controllers';
    if (path.includes('/admin')) return 'admin';
    return 'unknown';
}

function setupSocketListeners() {
    if (!socket) return;
    
    socket.on('connect', function() {
        console.log('Connected to server');
        
        // Join user room if user is logged in
        const userElement = document.querySelector('[data-user-id]');
        if (userElement) {
            const userId = userElement.getAttribute('data-user-id');
            socket.emit('join-user-room', userId);
        }
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
    });
    
    socket.on('controller-updated', function(controller) {
        handleControllerUpdate(controller);
    });
    
    socket.on('controller-data', function(data) {
        handleControllerData(data);
    });
}

function handleControllerUpdate(controller) {
    // Update controller status in UI
    updateControllerStatus(controller);
    
    // Show notification for status changes
    if (controller.status === 'online') {
        showNotification(`Controller ${controller.name || controller.serialNumber} is now online`, 'success');
    } else if (controller.status === 'offline') {
        showNotification(`Controller ${controller.name || controller.serialNumber} went offline`, 'warning');
    }
}

function handleControllerData(data) {
    // Update real-time data displays
    updateControllerData(data);
    
    // Update charts if visible
    updateCharts(data);
}

function updateControllerStatus(controller) {
    // Find status elements and update them
    const statusElements = document.querySelectorAll(`[data-controller-id="${controller.id}"] .status-indicator`);
    statusElements.forEach(element => {
        if (controller.isOnline) {
            element.className = 'status-indicator online';
        } else {
            element.className = 'status-indicator offline';
        }
    });
    
    const statusTexts = document.querySelectorAll(`[data-controller-id="${controller.id}"] .status-text`);
    statusTexts.forEach(element => {
        element.textContent = controller.isOnline ? 'Online' : 'Offline';
        element.className = controller.isOnline ? 'status-online' : 'status-offline';
    });
}

function updateControllerData(data) {
    // Update data displays for specific controller
    const dataElements = document.querySelectorAll(`[data-controller-id="${data.controllerId}"] .latest-data`);
    dataElements.forEach(element => {
        element.textContent = JSON.stringify(data.data, null, 2);
    });
    
    // Update last update timestamp
    const timestampElements = document.querySelectorAll(`[data-controller-id="${data.controllerId}"] .last-update`);
    timestampElements.forEach(element => {
        element.textContent = formatTimestamp(data.timestamp);
        element.setAttribute('data-timestamp', data.timestamp);
    });
}

function initializeTooltips() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function initializeModals() {
    // Initialize Bootstrap modals
    const modalTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="modal"]'));
    modalTriggerList.map(function (modalTriggerEl) {
        return new bootstrap.Modal(modalTriggerEl);
    });
}

function initializeFormatting() {
    // Format all timestamps on page load
    updateAllTimestamps();
    
    // Update timestamps every minute
    setInterval(updateAllTimestamps, 60000);
}

function updateAllTimestamps() {
    document.querySelectorAll('[data-timestamp]').forEach(element => {
        const timestamp = element.getAttribute('data-timestamp');
        if (timestamp) {
            element.textContent = formatTimestamp(timestamp);
        }
    });
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) { // Less than 1 minute
        return 'Just now';
    } else if (diff < 3600000) { // Less than 1 hour
        const minutes = Math.floor(diff / 60000);
        return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
    } else if (diff < 86400000) { // Less than 1 day
        const hours = Math.floor(diff / 3600000);
        return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
    } else if (diff < 604800000) { // Less than 1 week
        const days = Math.floor(diff / 86400000);
        return `${days} day${days !== 1 ? 's' : ''} ago`;
    } else {
        return date.toLocaleDateString();
    }
}

function showNotification(message, type = 'info') {
    // Create toast notification
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast element after it's hidden
    toast.addEventListener('hidden.bs.toast', function () {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// API helper functions
async function apiCall(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, mergedOptions);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        showNotification(`API Error: ${error.message}`, 'danger');
        throw error;
    }
}

// Form helpers
function serializeForm(form) {
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        if (data[key]) {
            // Handle multiple values (checkboxes, multi-select)
            if (Array.isArray(data[key])) {
                data[key].push(value);
            } else {
                data[key] = [data[key], value];
            }
        } else {
            data[key] = value;
        }
    }
    
    return data;
}

function validateForm(form) {
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Loading indicators
function showLoading(element) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    
    if (element) {
        element.innerHTML = `
            <div class="d-flex justify-content-center align-items-center py-4">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span class="ms-2">Loading...</span>
            </div>
        `;
    }
}

function hideLoading(element, content = '') {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    
    if (element) {
        element.innerHTML = content;
    }
}

// Export functions for use in other scripts
window.LXCloud = {
    apiCall,
    showNotification,
    formatTimestamp,
    updateAllTimestamps,
    serializeForm,
    validateForm,
    showLoading,
    hideLoading,
    debounce,
    throttle
};