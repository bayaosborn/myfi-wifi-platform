// =============================================
// EDIT CONTACT FUNCTIONALITY
// Handles editing and deleting contacts
// =============================================

let currentEditingContactId = null;

// Open edit modal
document.getElementById('editContactBtn').addEventListener('click', () => {
    if (contactsArray.length === 0) return;
    
    const contact = contactsArray[currentIndex];
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
                // Stay on the same contact (find by ID)
                const newIndex = contactsArray.findIndex(c => c.id === currentEditingContactId);
                if (newIndex !== -1) {
                    currentIndex = newIndex;
                    displayContact(currentIndex);
                }
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
    
    const contact = contactsArray[currentIndex];
    const confirmDelete = confirm(`Delete "${contact.name}"?\n\nThis cannot be undone.`);
    
    if (!confirmDelete) return;
    
    try {
        const response = await fetch(`/api/contacts/${currentEditingContactId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('✓ Contact deleted');
            closeEditModal();
            
            // Reload contacts
            if (typeof loadContactsFromDatabase === 'function') {
                await loadContactsFromDatabase();
                
                // Show previous contact or first if deleted was first
                if (currentIndex >= contactsArray.length) {
                    currentIndex = Math.max(0, contactsArray.length - 1);
                }
                
                if (contactsArray.length > 0) {
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