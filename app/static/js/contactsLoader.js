// =============================================
// CONTACTS LOADER
// Handles fetching contacts from database API
// =============================================

// Fetch contacts from database
async function loadContactsFromDatabase(page = 1) {
    console.log('Loading contacts from database...');
    
    try {
        const response = await fetch(`/api/contacts?page=${page}&per_page=1000`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        console.log('API Response:', data);
        
        if (data.contacts && data.contacts.length > 0) {
            contactsArray = data.contacts;
            totalContacts = data.total;
            currentIndex = 0;
            
            // Display first contact
            displayContact(currentIndex);
            
            // Update count card
            updateContactsCount(totalContacts);
            
            console.log(`✓ Loaded ${totalContacts} contacts from database`);
        } else {
            console.log('No contacts found in database');
            showEmptyCard();
        }
    } catch (error) {
        console.error('Error loading contacts:', error);
        showEmptyCard();
    }
}

// Initialize navigation and load contacts
function setupNavigation() {
    console.log('Setting up navigation...');
    
    const prevBtn = document.getElementById('prevContactBtn');
    const nextBtn = document.getElementById('nextContactBtn');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', previousContact);
        console.log('Previous button connected');
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', nextContact);
        console.log('Next button connected');
    }
    
    // Load contacts from database
    loadContactsFromDatabase();
}

// Auto-initialize when page loads
document.addEventListener('DOMContentLoaded', setupNavigation);