// =============================================
// EDIT CONTACT FUNCTIONALITY
// Handles editing and deleting contacts
// =============================================

// Open edit modal
document.getElementById('editContactBtn').addEventListener('click', () => {
    // Use the active array (filtered or full)
    const activeArray = isSearching ? filteredContacts : contactsArray;
    
    if (activeArray.length === 0) return;
    
    const contact = activeArray[currentIndex];
    currentEditingContactId = contact.id;
    
    // Populate form
    document.getElementById('editName').value = contact.name || '';
    document.getElementById('editPhone').value = contact.phone || '';
    document.getElementById('editEmail').value = contact.email || '';
    document.getElementById('editTag').value = contact.tag || 'General';
    document.getElementById('editNotes').value = contact.notes || '';
    
    // Show modal
    document.getElementById('modalEdit').style.display = 'flex';
});

// Close edit modal
function closeEditModal() {
    document.getElementById('modalEdit').style.display = 'none';
    currentEditingContactId = null;
}

// Save contact edits
async function saveContactEdits() {
    if (!currentEditingContactId) return;
    
    const updatedContact = {
        name: document.getElementById('editName').value.trim(),
        phone: document.getElementById('editPhone').value.trim(),
        email: document.getElementById('editEmail').value.trim(),
        tag: document.getElementById('editTag').value,
        notes: document.getElementById('editNotes').value.trim()
    };
    
    // Validate
    if (!updatedContact.name) {
        alert('❌ Name is required');
        return;
    }
    
    try {
        const response = await fetch(`/api/contacts/${currentEditingContactId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedContact)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('✓ Contact updated');
            closeEditModal();
            
            // Reload contacts
            if (typeof loadContactsFromDatabase === 'function') {
                await loadContactsFromDatabase();
            }
        } else {
            alert('✗ Update failed: ' + result.error);
        }
        
    } catch (error) {
        console.error('Update error:', error);
        alert('✗ Update failed');
    }
}

// Delete contact
async function deleteContact() {
    if (!currentEditingContactId) return;
    
    const activeArray = isSearching ? filteredContacts : contactsArray;
    const contact = activeArray[currentIndex];
    const confirmDelete = confirm(`Delete "${contact.name}"?\n\nThis cannot be undone.`);
    
    if (!confirmDelete) return;
    
    try {
        const response = await fetch(`/api/contacts/${currentEditingContactId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('✓ Contact deleted');
            
            // Clear the ID since we're deleting
            currentEditingContactId = null;
            closeEditModal();
            
            // Reload contacts
            if (typeof loadContactsFromDatabase === 'function') {
                await loadContactsFromDatabase();
                
                // Show previous contact or first if deleted was first
                const activeArray = isSearching ? filteredContacts : contactsArray;
                if (currentIndex >= activeArray.length) {
                    currentIndex = Math.max(0, activeArray.length - 1);
                }
                
                if (activeArray.length > 0) {
                    displayContact(currentIndex);
                } else {
                    showEmptyCard();
                }
            }
        } else {
            alert('✗ Delete failed: ' + result.error);
        }
        
    } catch (error) {
        console.error('Delete error:', error);
        alert('✗ Delete failed');
    }
}

// Open notes page for current contact
function openNotes() {
    if (!currentEditingContactId) {
        console.error('No contact ID available');
        alert('Please open a contact first');
        return;
    }

    // Navigate to notes page with contact ID
    window.location.href = `/notes?contact_id=${currentEditingContactId}`;
}