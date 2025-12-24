// =============================================
// ADD CUSTOM CONTACT FORM HANDLER
// =============================================

async function saveContact() {
    const name = document.getElementById('cName').value.trim();
    const phone = document.getElementById('cPhone').value.trim();
    const email = document.getElementById('cEmail').value.trim();
    const tag = document.getElementById('cTag').value;
    const notes = document.getElementById('cNotes').value.trim();
    
    // Validate name
    if (!name) {
        alert('❌ Name is required!');
        return;
    }
    
    // Prepare data
    const contactData = {
        name: name,
        phone: phone,
        email: email,
        tag: tag || 'General',
        notes: notes
    };
    
    console.log('Sending contact data:', contactData);
    
    try {
        const response = await fetch('/api/contacts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(contactData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`✓ ${result.message}`);
            
            // Clear form
            document.getElementById('cName').value = '';
            document.getElementById('cPhone').value = '';
            document.getElementById('cEmail').value = '';
            document.getElementById('cTag').value = '';
            document.getElementById('cNotes').value = '';
            
            // Reload contacts from database
            if (typeof loadContactsFromDatabase === 'function') {
                await loadContactsFromDatabase();
            }
            
            // Close modal
            closeModals();
        } else {
            alert('✗ Failed to add contact: ' + result.error);
        }
        
    } catch (error) {
        console.error('Error adding contact:', error);
        alert('✗ Failed to add contact. Check console for details.');
    }
}