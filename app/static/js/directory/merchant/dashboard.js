/**
 * Merchant Dashboard JavaScript
 * Handles status updates and notifications
 */

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeStatusButtons();
    setupAutoRefresh();
});

/**
 * Initialize status button click handlers
 */
function initializeStatusButtons() {
    const statusButtons = document.querySelectorAll('.status-buttons .btn');
    
    statusButtons.forEach(button => {
        button.addEventListener('click', async (e) => {
            const field = e.target.getAttribute('data-field');
            const value = e.target.getAttribute('data-value');
            
            if (field && value) {
                await updateStatus(field, value, e.target);
            }
        });
    });
}

/**
 * Update merchant status (OPEN/CLOSED, IN_STOCK/OUT_OF_STOCK)
 */
async function updateStatus(field, value, buttonElement) {
    try {
        // Disable all buttons temporarily
        disableAllButtons(true);
        
        const response = await fetch('/directory/merchant/update-status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                [field]: value
            })
        });

        const data = await response.json();

        if (data.success) {
            showNotification('✅ Status updated successfully!', 'success');
            
            // Update button states
            updateButtonStates(buttonElement);
            
            // Reload page after 1 second to show updated status
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showNotification('❌ Update failed: ' + (data.error || 'Unknown error'), 'error');
            disableAllButtons(false);
        }
    } catch (error) {
        console.error('Update error:', error);
        showNotification('❌ Network error. Please check your connection.', 'error');
        disableAllButtons(false);
    }
}

/**
 * Update visual state of buttons
 */
function updateButtonStates(activeButton) {
    // Remove active class from all buttons in the same group
    const parentButtons = activeButton.closest('.status-buttons');
    if (parentButtons) {
        parentButtons.querySelectorAll('.btn').forEach(btn => {
            btn.classList.remove('active');
        });
    }
    
    // Add active class to clicked button
    activeButton.classList.add('active');
}

/**
 * Disable/enable all status buttons
 */
function disableAllButtons(disabled) {
    const allButtons = document.querySelectorAll('.status-buttons .btn');
    allButtons.forEach(btn => {
        btn.disabled = disabled;
        btn.style.cursor = disabled ? 'not-allowed' : 'pointer';
        btn.style.opacity = disabled ? '0.5' : '';
    });
}

/**
 * Show notification toast
 */
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    
    if (!notification) return;
    
    notification.textContent = message;
    notification.className = 'notification ' + (type === 'error' ? 'error' : '');
    notification.style.display = 'block';
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        notification.style.display = 'none';
    }, 3000);
}

/**
 * Setup auto-refresh for dashboard (optional)
 * Refreshes every 5 minutes to show latest orders
 */
function setupAutoRefresh() {
    // Disabled by default - uncomment if needed
    // setInterval(() => {
    //     window.location.reload();
    // }, 300000); // 5 minutes
}

/**
 * Utility: Format date for display
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    // Less than 1 hour
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
    }
    
    // Less than 24 hours
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
    }
    
    // More than 24 hours
    return date.toLocaleDateString();
}