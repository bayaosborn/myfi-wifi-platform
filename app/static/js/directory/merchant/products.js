/**
 * Merchant Products & Services JavaScript
 */

let currentProductId = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    updateFormFields();
});

/**
 * Show Add Modal
 */
function showAddModal() {
    currentProductId = null;
    document.getElementById('modalTitle').textContent = 'Add Product/Service';
    document.getElementById('productForm').reset();
    document.getElementById('productId').value = '';
    
    // Reset to PRODUCT type
    document.querySelector('input[name="type"][value="PRODUCT"]').checked = true;
    updateFormFields();
    
    document.getElementById('productModal').classList.add('active');
}

/**
 * Edit Product
 */
function editProduct(productId) {
    currentProductId = productId;
    
    // Find product data from card
    const card = document.querySelector(`.product-card[data-id="${productId}"]`);
    if (!card) return;
    
    const name = card.querySelector('.product-name').textContent;
    const description = card.querySelector('.product-description')?.textContent || '';
    const price = card.querySelector('.product-price').textContent.replace('KES ', '');
    const type = card.querySelector('.product-badge').textContent.trim();
    const isAvailable = card.querySelector('.product-status').classList.contains('available');
    
    // Populate form
    document.getElementById('modalTitle').textContent = 'Edit Product/Service';
    document.getElementById('productId').value = productId;
    document.getElementById('productName').value = name;
    document.getElementById('productDescription').value = description;
    document.getElementById('productPrice').value = price;
    document.getElementById('isAvailable').checked = isAvailable;
    
    // Set type
    document.querySelector(`input[name="type"][value="${type}"]`).checked = true;
    updateFormFields();
    
    document.getElementById('productModal').classList.add('active');
}

/**
 * Close Modal
 */
function closeModal() {
    document.getElementById('productModal').classList.remove('active');
    currentProductId = null;
}

/**
 * Update form fields based on type selection
 */
function updateFormFields() {
    const type = document.querySelector('input[name="type"]:checked').value;
    const serviceFields = document.getElementById('serviceFields');
    const productFields = document.getElementById('productFields');
    
    if (type === 'SERVICE') {
        serviceFields.style.display = 'block';
        productFields.style.display = 'none';
    } else {
        serviceFields.style.display = 'none';
        productFields.style.display = 'block';
    }
}

/**
 * Save Product
 */
async function saveProduct(event) {
    event.preventDefault();
    
    const type = document.querySelector('input[name="type"]:checked').value;
    const name = document.getElementById('productName').value.trim();
    const description = document.getElementById('productDescription').value.trim();
    const price = parseFloat(document.getElementById('productPrice').value);
    const imageUrl = document.getElementById('productImage').value.trim();
    const isAvailable = document.getElementById('isAvailable').checked;
    
    // Validation
    if (!name || !price) {
        showNotification('❌ Please fill in all required fields', 'error');
        return;
    }
    
    const productData = {
        name: name,
        description: description || null,
        type: type,
        price: price,
        is_available: isAvailable,
        image_url: imageUrl || null
    };
    
    // Add type-specific fields
    if (type === 'SERVICE') {
        productData.service_location = document.getElementById('serviceLocation').value;
        productData.delivery_required = false;
    } else {
        productData.delivery_required = document.getElementById('deliveryRequired').checked;
        productData.service_location = null;
    }
    
    try {
        let url, method;
        
        if (currentProductId) {
            // Update existing
            url = `/directory/merchant/products/${currentProductId}/update`;
            method = 'POST';
        } else {
            // Add new
            url = '/directory/merchant/products/add';
            method = 'POST';
        }
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(productData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification(`✅ ${currentProductId ? 'Updated' : 'Added'} successfully!`, 'success');
            closeModal();
            
            // Reload page after 1 second
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showNotification('❌ Failed: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Save error:', error);
        showNotification('❌ Network error. Please try again.', 'error');
    }
}

/**
 * Toggle Availability
 */
async function toggleAvailability(productId, newStatus) {
    if (!confirm(`Are you sure you want to mark this ${newStatus ? 'available' : 'unavailable'}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/directory/merchant/products/${productId}/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                is_available: newStatus
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('✅ Availability updated!', 'success');
            
            // Reload page
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showNotification('❌ Update failed', 'error');
        }
    } catch (error) {
        console.error('Toggle error:', error);
        showNotification('❌ Network error', 'error');
    }
}

/**
 * Delete Product
 */
async function deleteProduct(productId) {
    if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/directory/merchant/products/${productId}/delete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('✅ Deleted successfully!', 'success');
            
            // Remove card from DOM
            const card = document.querySelector(`.product-card[data-id="${productId}"]`);
            if (card) {
                card.style.opacity = '0';
                card.style.transform = 'scale(0.8)';
                setTimeout(() => {
                    card.remove();
                    
                    // Check if empty
                    const grid = document.querySelector('.products-grid');
                    if (grid.children.length === 0) {
                        window.location.reload();
                    }
                }, 300);
            }
        } else {
            showNotification('❌ Delete failed', 'error');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showNotification('❌ Network error', 'error');
    }
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
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, 3000);
}

// Close modal on outside click
document.addEventListener('click', (e) => {
    const modal = document.getElementById('productModal');
    if (e.target === modal) {
        closeModal();
    }
});