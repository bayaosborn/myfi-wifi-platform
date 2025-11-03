// Contacts management

let currentSearchedUser = null;

// Load saved contacts on page load
document.addEventListener('DOMContentLoaded', () => {
    loadSavedContacts();
    loadCallHistory();
});

// Save button handler
document.getElementById('saveBtn').addEventListener('click', () => {
    if (!currentSearchedUser) return;
    
    document.getElementById('saveUsername').textContent = currentSearchedUser.username;
    document.getElementById('customNameInput').value = currentSearchedUser.custom_name || '';
    document.getElementById('saveContactModal').style.display = 'flex';
});

// Confirm save
document.getElementById('confirmSaveBtn').addEventListener('click', async () => {
    const customName = document.getElementById('customNameInput').value.trim();
    
    try {
        const response = await fetch('/api/contacts/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                contact_user_id: currentSearchedUser.id,
                custom_name: customName
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message);
            document.getElementById('saveContactModal').style.display = 'none';
            document.getElementById('saveBtn').textContent = '✅ Saved';
            document.getElementById('saveBtn').disabled = true;
            
            // Reload contacts list
            loadSavedContacts();
        } else {
            alert('Failed to save contact');
        }
    } catch (error) {
        console.error('Save error:', error);
        alert('Error saving contact');
    }
});

// Cancel save
document.getElementById('cancelSaveBtn').addEventListener('click', () => {
    document.getElementById('saveContactModal').style.display = 'none';
});

// Load saved contacts
async function loadSavedContacts() {
    try {
        const response = await fetch('/api/contacts');
        const data = await response.json();
        
        const contactsList = document.getElementById('contactsList');
        
        if (data.success && data.contacts.length > 0) {
            contactsList.innerHTML = data.contacts.map(contact => `
                <div class="contact-card" data-user-id="${contact.user_id}">
                    <div class="contact-info">
                        <strong>${contact.custom_name || contact.username}</strong>
                        ${contact.custom_name ? `<span style="color:#666; font-size:12px;">(${contact.username})</span>` : ''}
                        <span class="status-indicator">${contact.online ? '🟢 Online' : '⚪ Offline'}</span>
                    </div>
                    <div class="contact-actions">
                        <button class="contact-call-btn" onclick="callContact(${contact.user_id}, '${contact.custom_name || contact.username}')">📞</button>
                        <button class="contact-delete-btn" onclick="deleteContact(${contact.id})">🗑️</button>
                    </div>
                </div>
            `).join('');
        } else {
            contactsList.innerHTML = '<p style="color:#666;">No saved contacts yet</p>';
        }
    } catch (error) {
        console.error('Load contacts error:', error);
    }
}

// Call a saved contact
window.callContact = function(userId, displayName) {
    initiateCall(userId, displayName);
};

// Delete contact
window.deleteContact = async function(contactId) {
    if (!confirm('Remove this contact?')) return;
    
    try {
        const response = await fetch(`/api/contacts/${contactId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadSavedContacts();
        }
    } catch (error) {
        console.error('Delete error:', error);
    }
};

// Load call history
async function loadCallHistory() {
    try {
        const response = await fetch('/api/call-history');
        const data = await response.json();
        
        const historyList = document.getElementById('callHistoryList');
        
        if (data.success && data.calls.length > 0) {
            historyList.innerHTML = data.calls.map(call => {
                const icon = call.direction === 'outgoing' ? '📞' : '📲';
                const duration = call.duration > 0 ? `${Math.floor(call.duration / 60)}:${(call.duration % 60).toString().padStart(2, '0')}` : '';
                const time = new Date(call.started_at).toLocaleString();
                
                return `
                    <div class="call-history-item">
                        <span>${icon} ${call.other_username}</span>
                        <span style="color:#666; font-size:12px;">${call.status} ${duration}</span>
                        <span style="color:#999; font-size:11px;">${time}</span>
                    </div>
                `;
            }).join('');
        } else {
            historyList.innerHTML = '<p style="color:#666;">No call history</p>';
        }
    } catch (error) {
        console.error('Load history error:', error);
    }
}

// Update current searched user (called from call-ui.js)
window.setCurrentSearchedUser = function(user) {
    currentSearchedUser = user;
    
    // Update save button state
    if (user.is_saved) {
        document.getElementById('saveBtn').textContent = '✅ Saved';
        document.getElementById('saveBtn').disabled = true;
        
        if (user.custom_name) {
            document.getElementById('customNameDisplay').textContent = `Saved as: ${user.custom_name}`;
            document.getElementById('customNameDisplay').style.display = 'block';
        }
    } else {
        document.getElementById('saveBtn').textContent = '💾 Save';
        document.getElementById('saveBtn').disabled = false;
        document.getElementById('customNameDisplay').style.display = 'none';
    }
};