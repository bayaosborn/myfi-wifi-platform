/**
 * Merchant Settings JavaScript
 * Handles updating merchant information
 */

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeFormValues();
});

/**
 * Initialize form values from merchant data
 */
function initializeFormValues() {
    // Set operating hours if they exist
    const openingTime = "{{ merchant.opening_time or '' }}";
    const closingTime = "{{ merchant.closing_time or '' }}";
    
    if (openingTime) {
        document.getElementById('opening_time').value = openingTime;
    }
    if (closingTime) {
        document.getElementById('closing_time').value = closingTime;
    }
}

/**
 * Save Business Details
 */
async function saveBusinessDetails() {
    const businessName = document.getElementById('business_name').value.trim();
    const ownerName = document.getElementById('owner_name').value.trim();
    const description = document.getElementById('description').value.trim();
    const tagsInput = document.getElementById('tags').value.trim();
    
    // Validation
    if (!businessName) {
        showNotification('❌ Business name is required', 'error');
        return;
    }
    
    if (!ownerName) {
        showNotification('❌ Owner name is required', 'error');
        return;
    }
    
    // Convert comma-separated tags to array
    const tags = tagsInput ? tagsInput.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
    
    const data = {
        business_name: businessName,
        owner_name: ownerName,
        description: description || null,
        tags: tags
    };
    
    await saveSettings(data, 'Business details updated successfully!');
}

/**
 * Save Contact Information
 */
async function saveContactInfo() {
    const phone = document.getElementById('phone').value.trim();
    const email = document.getElementById('email').value.trim();
    const location = document.getElementById('location').value.trim();
    
    // Validation
    if (!phone) {
        showNotification('❌ Phone number is required', 'error');
        return;
    }
    
    if (!location) {
        showNotification('❌ Location is required', 'error');
        return;
    }
    
    const data = {
        phone: phone,
        email: email || null,
        location: location
    };
    
    await saveSettings(data, 'Contact information updated successfully!');
}

/**
 * Save Operating Hours
 */
async function saveOperatingHours() {
    const openingTime = document.getElementById('opening_time').value;
    const closingTime = document.getElementById('closing_time').value;
    
    // Validation
    if (!openingTime || !closingTime) {
        showNotification('❌ Please select both opening and closing times', 'error');
        return;
    }
    
    const data = {
        opening_time: openingTime,
        closing_time: closingTime
    };
    
    await saveSettings(data, 'Operating hours updated successfully!');
}

/**
 * Save Payment Methods
 */
async function savePaymentMethods() {
    const mpesaTill = document.getElementById('mpesa_till').value.trim();
    const mpesaPaybill = document.getElementById('mpesa_paybill').value.trim();
    const mpesaAccount = document.getElementById('mpesa_account').value.trim();
    
    // At least one payment method should be provided
    if (!mpesaTill && !mpesaPaybill) {
        showNotification('❌ Please provide at least one payment method', 'error');
        return;
    }
    
    const data = {
        mpesa_till: mpesaTill || null,
        mpesa_paybill: mpesaPaybill || null,
        mpesa_account: mpesaAccount || null
    };
    
    await saveSettings(data, 'Payment methods updated successfully!');
}

/**
 * Generic function to save settings
 */
async function saveSettings(data, successMessage) {
    try {
        // Disable all save buttons
        disableSaveButtons(true);
        
        const response = await fetch('/directory/merchant/update-settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showNotification('✅ ' + successMessage, 'success');
        } else {
            showNotification('❌ Update failed: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Update error:', error);
        showNotification('❌ Network error. Please check your connection.', 'error');
    } finally {
        disableSaveButtons(false);
    }
}

/**
 * Disable/enable all save buttons
 */
function disableSaveButtons(disabled) {
    const buttons = document.querySelectorAll('.btn-save');
    buttons.forEach(btn => {
        btn.disabled = disabled;
        btn.textContent = disabled ? 'Saving...' : btn.textContent.replace('Saving...', 'Save');
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