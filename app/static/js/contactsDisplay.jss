/*

// =============================================
// CONTACTS DISPLAY MANAGER (DATABASE VERSION)
// Fetches contacts from API and handles navigation
// =============================================

let contactsArray = [];      // Caches contacts from database
let currentIndex = 0;        // Tracks which contact is being displayed
let currentPage = 1;         // For pagination
let totalContacts = 0;

// Tag color mapping
const TAG_COLORS = {
    'family': '#FFE5E5',
    'work': '#E8F4FD',
    'friends': '#FFF4E6',
    'relationship': '#FFE6F0',
    'riders': '#E8F5E9',
    'favorite': '#FFF9C4',
    'general': '#FFFFFF'
};

// Fetch contacts from database when page loads
async function loadContactsFromDatabase(page = 1) {
    try {
        const response = await fetch(`/api/contacts?page=${page}&per_page=1000`);
        const data = await response.json();
        
        if (data.contacts && data.contacts.length > 0) {
            contactsArray = data.contacts;
            totalContacts = data.total;
            currentIndex = 0;
            
            // Display first contact
            displayContact(currentIndex);
            
            // Update count card
            if (typeof updateContactsCount === 'function') {
                updateContactsCount(totalContacts);
            }
            
            console.log(`✓ Loaded ${totalContacts} contacts from database`);
        } else {
            showEmptyCard();
        }
    } catch (error) {
        console.error('Error loading contacts:', error);
        showEmptyCard();
    }
}

// Main function to update the card with contact details
function displayContact(index) {
    // Safety check
    if (contactsArray.length === 0) {
        showEmptyCard();
        return;
    }
    
    // Get contact at index
    const contact = contactsArray[index];
    
    // Update name
    const nameElement = document.querySelector('.contact-name');
    if (nameElement) {
        nameElement.textContent = contact.name || 'Unknown';
    }
    
    // Update tag
    const tagElement = document.querySelector('.contact-tag');
    if (tagElement) {
        tagElement.textContent = contact.tag || 'General';
    }
    
    // Update phone (with emoji)
    const phoneDetail = document.querySelectorAll('.contact-detail')[0];
    if (phoneDetail) {
        phoneDetail.innerHTML = `📞 ${contact.phone || 'No phone'}`;
    }
    
    // Update email (with emoji)
    const emailDetail = document.querySelectorAll('.contact-detail')[1];
    if (emailDetail) {
        emailDetail.innerHTML = `✉️ ${contact.email || 'No email'}`;
    }
    
    // CHANGE CARD BACKGROUND COLOR BASED ON TAG
    const mainCard = document.querySelector('.main-card');
    if (mainCard) {
        const tag = (contact.tag || 'general').toLowerCase().trim();
        const bgColor = TAG_COLORS[tag] || TAG_COLORS['general'];
        mainCard.style.backgroundColor = bgColor;
        console.log(`Card color changed to ${tag}: ${bgColor}`);
    }
    
    // Update Logic card with contact name
    updateLogicCard(contact.name);
    
    // Update position counter
    updatePositionCounter();
}

// Show placeholder when no contacts
function showEmptyCard() {
    const nameElement = document.querySelector('.contact-name');
    const tagElement = document.querySelector('.contact-tag');
    
    if (nameElement) nameElement.textContent = 'No Contacts Yet';
    if (tagElement) tagElement.textContent = 'Upload contacts to start';
    
    const details = document.querySelectorAll('.contact-detail');
    details.forEach(detail => detail.textContent = '');
    
    // Reset card to white
    const mainCard = document.querySelector('.main-card');
    if (mainCard) {
        mainCard.style.backgroundColor = '#FFFFFF';
    }
    
    updatePositionCounter();
}

// Update logic card with current contact's name
function updateLogicCard(contactName) {
    const logicText = document.querySelector('.logic-text');
    if (logicText) {
        logicText.innerHTML = `
            You haven't called <b>${contactName}</b> in 2 days.<br>
            Consider giving them a quick check-in.
        `;
    }
}

// Navigate to next contact (with looping)
function nextContact() {
    if (contactsArray.length === 0) return;
    
    currentIndex = (currentIndex + 1) % contactsArray.length; // Loop to start
    displayContact(currentIndex);
}

// Navigate to previous contact (with looping)
function previousContact() {
    if (contactsArray.length === 0) return;
    
    currentIndex = (currentIndex - 1 + contactsArray.length) % contactsArray.length; // Loop to end
    displayContact(currentIndex);
}

// Update position counter (e.g., "3 of 15")
function updatePositionCounter() {
    const counterElement = document.getElementById('contactPosition');
    if (counterElement) {
        if (contactsArray.length > 0) {
            counterElement.textContent = `${currentIndex + 1} of ${contactsArray.length}`;
        } else {
            counterElement.textContent = '0 of 0';
        }
    }
}

// Initialize navigation and load contacts when page loads
function setupNavigation() {
    const prevBtn = document.getElementById('prevContactBtn');
    const nextBtn = document.getElementById('nextContactBtn');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', previousContact);
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', nextContact);
    }
    
    // Load contacts from database
    loadContactsFromDatabase();
}

// Call setup when page loads
document.addEventListener('DOMContentLoaded', setupNavigation);







*/






// =============================================
// CONTACTS DISPLAY MANAGER (DATABASE VERSION)
// Fetches contacts from API and handles navigation
// =============================================

let contactsArray = [];      // Caches contacts from database
let currentIndex = 0;        // Tracks which contact is being displayed
let currentPage = 1;         // For pagination
let totalContacts = 0;

// Fetch contacts from database when page loads
async function loadContactsFromDatabase(page = 1) {
    try {
        const response = await fetch(`/api/contacts?page=${page}&per_page=1000`);
        const data = await response.json();
        
        if (data.contacts && data.contacts.length > 0) {
            contactsArray = data.contacts;
            totalContacts = data.total;
            currentIndex = 0;
            
            // Display first contact
            displayContact(currentIndex);
            
            // Update count card
            if (typeof updateContactsCount === 'function') {
                updateContactsCount(totalContacts);
            }
            
            console.log(`✓ Loaded ${totalContacts} contacts from database`);
        } else {
            showEmptyCard();
        }
    } catch (error) {
        console.error('Error loading contacts:', error);
        showEmptyCard();
    }
}

// Main function to update the card with contact details
function displayContact(index) {
    // Safety check
    if (contactsArray.length === 0) {
        showEmptyCard();
        return;
    }
    
    // Get contact at index
    const contact = contactsArray[index];
    
    // Update name
    const nameElement = document.querySelector('.contact-name');
    if (nameElement) {
        nameElement.textContent = contact.name || 'Unknown';
    }
    
    // Update tag
    const tagElement = document.querySelector('.contact-tag');
    if (tagElement) {
        tagElement.textContent = contact.tag || 'General';
    }
    
    // Update phone (with emoji)
    const phoneDetail = document.querySelectorAll('.contact-detail')[0];
    if (phoneDetail) {
        phoneDetail.innerHTML = `📞 ${contact.phone || 'No phone'}`;
    }
    
    // Update email (with emoji)
    const emailDetail = document.querySelectorAll('.contact-detail')[1];
    if (emailDetail) {
        emailDetail.innerHTML = `✉️ ${contact.email || 'No email'}`;
    }
    
    // Update Logic card with contact name
    updateLogicCard(contact.name);
    
    // Update position counter
    updatePositionCounter();
}

// Show placeholder when no contacts
function showEmptyCard() {
    const nameElement = document.querySelector('.contact-name');
    const tagElement = document.querySelector('.contact-tag');
    
    if (nameElement) nameElement.textContent = 'No Contacts Yet';
    if (tagElement) tagElement.textContent = 'Upload contacts to start';
    
    const details = document.querySelectorAll('.contact-detail');
    details.forEach(detail => detail.textContent = '');
    
    updatePositionCounter();
}

// Update logic card with current contact's name
function updateLogicCard(contactName) {
    const logicText = document.querySelector('.logic-text');
    if (logicText) {
        logicText.innerHTML = `
            You haven't called <b>${contactName}</b> in 2 days.<br>
            Consider giving them a quick check-in.
        `;
    }
}

// Navigate to next contact (with looping)
function nextContact() {
    if (contactsArray.length === 0) return;
    
    currentIndex = (currentIndex + 1) % contactsArray.length; // Loop to start
    displayContact(currentIndex);
}

// Navigate to previous contact (with looping)
function previousContact() {
    if (contactsArray.length === 0) return;
    
    currentIndex = (currentIndex - 1 + contactsArray.length) % contactsArray.length; // Loop to end
    displayContact(currentIndex);
}

// Update position counter (e.g., "3 of 15")
function updatePositionCounter() {
    const counterElement = document.getElementById('contactPosition');
    if (counterElement) {
        if (contactsArray.length > 0) {
            counterElement.textContent = `${currentIndex + 1} of ${contactsArray.length}`;
        } else {
            counterElement.textContent = '0 of 0';
        }
    }
}

// Initialize navigation and load contacts when page loads
function setupNavigation() {
    const prevBtn = document.getElementById('prevContactBtn');
    const nextBtn = document.getElementById('nextContactBtn');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', previousContact);
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', nextContact);
    }
    
    // Load contacts from database
    loadContactsFromDatabase();
}

// Call setup when page loads
document.addEventListener('DOMContentLoaded', setupNavigation);