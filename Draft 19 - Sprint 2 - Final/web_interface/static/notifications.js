/**
 * Notification System for ElderSafe Connect
 * 
 * This file provides a reusable notification system that can be included in all pages.
 * It allows showing popup notifications for success, error, warning, and info messages.
 */

// Initialize notification container
function initializeNotificationSystem() {
    // Only create the container if it doesn't exist yet
    if (!document.querySelector('.notification-container')) {
        // Create the notification container
        const container = document.createElement('div');
        container.className = 'notification-container';
        document.body.appendChild(container);
    }
}

// Get the icon based on notification type
function getNotificationIcon(type) {
    switch (type) {
        case 'success':
            return '✓';
        case 'error':
            return '✕';
        case 'warning':
            return '⚠';
        case 'info':
            return 'ℹ';
        default:
            return '';
    }
}

// Show a notification
function showNotification(message, type = 'info', duration = 5000) {
    // Make sure the notification system is initialized
    initializeNotificationSystem();
    
    // Get the container
    const container = document.querySelector('.notification-container');
    
    // Create the notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // Create icon element
    const iconElement = document.createElement('span');
    iconElement.className = 'notification-icon';
    iconElement.textContent = getNotificationIcon(type);
    notification.appendChild(iconElement);
    
    // Create message element
    const messageElement = document.createElement('span');
    messageElement.className = 'notification-message';
    messageElement.textContent = message;
    notification.appendChild(messageElement);
    
    // Create close button
    const closeButton = document.createElement('span');
    closeButton.className = 'notification-close';
    closeButton.innerHTML = '&times;';
    closeButton.addEventListener('click', () => {
        removeNotification(notification);
    });
    notification.appendChild(closeButton);
    
    // Add the notification to the container
    container.appendChild(notification);
    
    // Auto-dismiss after the specified duration
    if (duration > 0) {
        setTimeout(() => {
            removeNotification(notification);
        }, duration);
    }
    
    return notification;
}

// Remove a notification with animation
function removeNotification(notification) {
    notification.style.animation = 'notification-fade-out 0.3s forwards';
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 300);
}

// Convenience methods for different notification types
function showSuccessNotification(message, duration = 5000) {
    return showNotification(message, 'success', duration);
}

function showErrorNotification(message, duration = 5000) {
    return showNotification(message, 'error', duration);
}

function showWarningNotification(message, duration = 5000) {
    return showNotification(message, 'warning', duration);
}

function showInfoNotification(message, duration = 5000) {
    return showNotification(message, 'info', duration);
}

// Initialize the notification system when the DOM is ready
document.addEventListener('DOMContentLoaded', initializeNotificationSystem);

// Export the notification functions to make them globally available
window.showNotification = showNotification;
window.showSuccessNotification = showSuccessNotification;
window.showErrorNotification = showErrorNotification;
window.showWarningNotification = showWarningNotification;
window.showInfoNotification = showInfoNotification;