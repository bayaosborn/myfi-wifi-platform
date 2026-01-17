/**
 * MyFi Contacts Management
 * Handles contact search, save, display, and call history
 */

let currentSearchedUser = null;

// ==================== SEARCH ====================

async function searchUser() {
    const phoneInput = document.getElementById('searchInput');
    const phone = phoneInput.value.trim();
    
    if (!phone) {
        alert('Please enter a phone number');
        return;
    }
    
    // Validate phone format (basic)
    if (!/^07\d{8}$/.test(phone) && !/^254\d{9}$/.test(phone)) {
        alert('Please enter a valid phone number (e.g., 0712345678)');
        return;
    }
    
    try {
        const response = await fetch('/call/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone_number: phone })
        });
        
        const data = await response.json();
        
        if (data.found) {
            currentSearchedUser = data.user;
            displaySearchResult(data.user);
        } else {
            alert(data.message || 'User not found on MyFi');
            hideSearchResult();
        }
    } catch (error) {
        console.error('Search error:', error);
        alert('Failed to search user');
    }
}

function displaySearchResult(user) {
    const resultsDiv = document.getElementById('searchResults');
    const foundPhone = document.getElementById('foundPhone');
    const foundName = document.getElementById('foundName');
    const onlineStatus = document.getElementById('onlineStatus');
    const callBtn = document.getElementById('callBtn');
    const saveBtn = document.getElementById('saveBtn');
    
    foundPhone.textContent = user.phone_number;
    foundName.textContent = user.full_name || 'MyFi User';
    
    onlineStatus.textContent = user.online ? '🟢 Online' : '⚪ Offline';
    onlineStatus.className = `status-badge ${user.online ? 'online' : 'offline'}`;
    
    callBtn.dataset.userId = user.id;
    callBtn.dataset.phone = user.phone_number;
    callBtn.dataset.name = user.full_name || user.phone_number;
    
    // Update save button based on saved status
    if (user.is_saved) {
        saveBtn.textContent = '✓ Saved';
        saveBtn.disabled = true;
        saveBtn.style.opacity = '0.6';
    } else {
        saveBtn.textContent = '💾 Save';
        saveBtn.disabled = false;
        saveBtn.style.opacity = '1';
    }
    
    resultsDiv.style.display = 'block';
}

function hideSearchResult() {
    const resultsDiv = document.getElementById('searchResults');
    resultsDiv.style.display = 'none';
    currentSearchedUser = null;
}

// ==================== SAVE CONTACT ====================

function showSaveContactModal() {
    if (!currentSearchedUser) return;
    
    const modal = document.getElementById('saveContactModal');
    const savePhone = document.getElementById('savePhone');
    const nameInput = document.getElementById('contactNameInput');
    
    savePhone.textContent = currentSearchedUser.phone_number;
    nameInput.value = currentSearchedUser.full_name || '';
    
    modal.style.display = 'flex';
}

function hideSaveContactModal() {
    const modal = document.getElementById('saveContactModal');
    modal.style.display = 'none';
}

async function saveContact() {
    if (!currentSearchedUser) return;
    
    const nameInput = document.getElementById('contactNameInput');
    const tagInput = document.getElementById('contactTagInput');
    
    const name = nameInput.value.trim();
    const tag = tagInput.value;
    
    if (!name) {
        alert('Please enter a name');
        return;
    }
    
    try {
        const response = await fetch('/call/api/contacts/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                phone_number: currentSearchedUser.phone_number,
                name: name,
                tag: tag
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Contact saved successfully!');
            hideSaveContactModal();
            loadContacts(); // Reload contacts list
            
            // Update save button
            const saveBtn = document.getElementById('saveBtn');
            saveBtn.textContent = '✓ Saved';
            saveBtn.disabled = true;
            saveBtn.style.opacity = '0.6';
        } else {
            alert(data.message || 'Failed to save contact');
        }
    } catch (error) {
        console.error('Save contact error:', error);
        alert('Failed to save contact');
    }
}

// ==================== LOAD CONTACTS ====================

async function loadContacts() {
    try {
        const response = await fetch('/call/api/contacts');
        const data = await response.json();
        
        if (data.success) {
            displayContacts(data.contacts);
        }
    } catch (error) {
        console.error('Load contacts error:', error);
    }
}

function displayContacts(contacts) {
    const listDiv = document.getElementById('contactsList');
    const countBadge = document.getElementById('contactCount');
    
    countBadge.textContent = contacts.length;
    
    if (contacts.length === 0) {
        listDiv.innerHTML = `
            <div class="empty-state">
                <p>No contacts yet</p>
                <small>Search for users to add them</small>
            </div>
        `;
        return;
    }
    
    listDiv.innerHTML = contacts.map(contact => `
        <div class="list-item" data-contact-id="${contact.id}">
            <div class="list-item-info">
                <div class="list-item-avatar">👤</div>
                <div class="list-item-details">
                    <h4>${contact.name}</h4>
                    <p>${contact.phone} ${contact.is_myfi ? '• 🟢 MyFi' : ''}</p>
                    ${contact.tag ? `<span class="status-badge">${contact.tag}</span>` : ''}
                </div>
            </div>
            <button 
                class="list-item-action" 
                onclick="callContact('${contact.myfi_user_id || ''}', '${contact.phone}', '${contact.name}')"
                ${contact.is_myfi ? '' : 'disabled title="Not on MyFi"'}
            >
                📞
            </button>
        </div>
    `).join('');
}

// ==================== CALL HISTORY ====================

async function loadCallHistory() {
    try {
        const response = await fetch('/call/api/history');
        const data = await response.json();
        
        if (data.success) {
            displayCallHistory(data.calls);
        }
    } catch (error) {
        console.error('Load call history error:', error);
    }
}

function displayCallHistory(calls) {
    const listDiv = document.getElementById('historyList');
    const countBadge = document.getElementById('historyCount');
    
    countBadge.textContent = calls.length;
    
    if (calls.length === 0) {
        listDiv.innerHTML = `
            <div class="empty-state">
                <p>No call history</p>
                <small>Your calls will appear here</small>
            </div>
        `;
        return;
    }
    
    listDiv.innerHTML = calls.map(call => {
        const isOutgoing = call.direction === 'outgoing';
        const otherPerson = isOutgoing ? call.callee_name : call.caller_name;
        const otherPhone = isOutgoing ? call.callee_phone : call.caller_phone;
        const icon = isOutgoing ? '📞' : '📱';
        const statusIcon = {
            'completed': '✓',
            'missed': '✕',
            'rejected': '✕',
            'failed': '✕'
        }[call.status] || '';
        
        return `
            <div class="list-item">
                <div class="list-item-info">
                    <div class="list-item-avatar">${icon}</div>
                    <div class="list-item-details">
                        <h4>${otherPerson || otherPhone}</h4>
                        <p>
                            ${call.direction === 'outgoing' ? 'Outgoing' : 'Incoming'} • 
                            ${formatCallDuration(call.duration)} • 
                            ${formatCallDate(call.started_at)}
                            ${statusIcon}
                        </p>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// ==================== HELPER FUNCTIONS ====================

function callContact(userId, phone, name) {
    if (!userId) {
        alert('This contact is not on MyFi');
        return;
    }
    
    if (typeof window.MyFiCall !== 'undefined') {
        window.MyFiCall.initiateCall(userId, phone, name);
    } else {
        console.error('MyFiCall not available');
    }
}

function formatCallDuration(seconds) {
    if (!seconds || seconds === 0) return '0:00';
    
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function formatCallDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
}

// ==================== EVENT LISTENERS ====================

document.addEventListener('DOMContentLoaded', () => {
    // Search
    const searchBtn = document.getElementById('searchBtn');
    const searchInput = document.getElementById('searchInput');
    
    if (searchBtn) {
        searchBtn.addEventListener('click', searchUser);
    }
    
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') searchUser();
        });
    }
    
    // Call button
    const callBtn = document.getElementById('callBtn');
    if (callBtn) {
        callBtn.addEventListener('click', () => {
            const userId = callBtn.dataset.userId;
            const phone = callBtn.dataset.phone;
            const name = callBtn.dataset.name;
            
            if (typeof initiateCall === 'function') {
                initiateCall(userId, phone, name);
            }
        });
    }
    
    // Save contact
    const saveBtn = document.getElementById('saveBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', showSaveContactModal);
    }
    
    const confirmSaveBtn = document.getElementById('confirmSaveBtn');
    if (confirmSaveBtn) {
        confirmSaveBtn.addEventListener('click', saveContact);
    }
    
    const cancelSaveBtn = document.getElementById('cancelSaveBtn');
    if (cancelSaveBtn) {
        cancelSaveBtn.addEventListener('click', hideSaveContactModal);
    }
    
    console.log('✅ Contacts UI initialized');
});

// Export for use in other scripts
window.setCurrentSearchedUser = (user) => {
    currentSearchedUser = user;
};

window.loadContacts = loadContacts;
window.loadCallHistory = loadCallHistory;