// =============================================
// CONTACTS MANAGER (WITH TAG COLORS BUILT-IN)
// =============================================

let contactsArray = [];
let currentIndex = 0;
let totalContacts = 0;

// Tag colors
const TAG_COLORS = {
    'family': '#FFE5E5',
    'work': '#E8F4FD',
    'friends': '#FFF4E6',
    'relationship': '#FFE6F0',
    'riders': '#E8F5E9',
    'favorite': '#FFF9C4',
    'general': '#FFFFFF'
};

// Main display function
function displayContact(index) {
    if (contactsArray.length === 0) {
        showEmptyCard();
        return;
    }
    
    const contact = contactsArray[index];
    
    // Update name
    const nameElement = document.querySelector('.contact-name');
    if (nameElement) nameElement.textContent = contact.name || 'Unknown';
    
    // Update tag
    const tagElement = document.querySelector('.contact-tag');
    if (tagElement) tagElement.textContent = contact.tag || 'General';
    
    // Update phone
    const phoneDetail = document.querySelectorAll('.contact-detail')[0];
    if (phoneDetail) phoneDetail.innerHTML = `📞 ${contact.phone || 'No phone'}`;
    
    // Update email
    const emailDetail = document.querySelectorAll('.contact-detail')[1];
    if (emailDetail) emailDetail.innerHTML = `✉️ ${contact.email || 'No email'}`;
    
    // CHANGE CARD COLOR
    const mainCard = document.querySelector('.main-card');
    const tag = (contact.tag || 'general').toLowerCase().trim();
    const bgColor = TAG_COLORS[tag] || TAG_COLORS['general'];
    
    if (mainCard) {
        mainCard.style.backgroundColor = bgColor;
        console.log(`Changed card to ${tag} color: ${bgColor}`);
    } else {
        console.error('Main card not found!');
    }
    
    updatePositionCounter();
}

function showEmptyCard() {
    const nameElement = document.querySelector('.contact-name');
    const tagElement = document.querySelector('.contact-tag');
    
    if (nameElement) nameElement.textContent = 'No Contacts Yet';
    if (tagElement) tagElement.textContent = 'Upload contacts to start';
    
    const details = document.querySelectorAll('.contact-detail');
    details.forEach(detail => detail.textContent = '');
    
    // Reset to white
    const mainCard = document.querySelector('.main-card');
    if (mainCard) mainCard.style.backgroundColor = '#FFFFFF';
    
    updatePositionCounter();
}

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

function nextContact() {
    if (contactsArray.length === 0) return;
    currentIndex = (currentIndex + 1) % contactsArray.length;
    displayContact(currentIndex);
}

function previousContact() {
    if (contactsArray.length === 0) return;
    currentIndex = (currentIndex - 1 + contactsArray.length) % contactsArray.length;
    displayContact(currentIndex);
}

function updateContactsCount(count) {
    const countElement = document.getElementById('contactsCountNumber');
    if (countElement) {
        countElement.textContent = count;
    }
}










/*
// =============================================
// CONTACTS MANAGER
// Core functions for managing contact display
// =============================================

let contactsArray = [];      // All contacts from database
let currentIndex = 0;        // Currently displayed contact
let totalContacts = 0;

// Main function to update the card with contact details
function displayContact(index) {
    console.log('displayContact called with index:', index);
    
    if (contactsArray.length === 0) {
        console.log('No contacts in array, showing empty card');
        showEmptyCard();
        return;
    }
    
    const contact = contactsArray[index];
    console.log('Displaying contact:', contact);
    
    // Update name
    const nameElement = document.querySelector('.contact-name');
    if (nameElement) {
        nameElement.textContent = contact.name || 'Unknown';
    } else {
        console.error('❌ .contact-name element not found');
    }
    
    // Update tag
    const tagElement = document.querySelector('.contact-tag');
    if (tagElement) {
        tagElement.textContent = contact.tag || 'General';
    } else {
        console.error('❌ .contact-tag element not found');
    }
    
    // Update phone
    const phoneDetail = document.querySelectorAll('.contact-detail')[0];
    if (phoneDetail) {
        phoneDetail.innerHTML = `📞 ${contact.phone || 'No phone'}`;
    } else {
        console.error('❌ .contact-detail[0] element not found');
    }
    
    // Update email
    const emailDetail = document.querySelectorAll('.contact-detail')[1];
    if (emailDetail) {
        emailDetail.innerHTML = `✉️ ${contact.email || 'No email'}`;
    } else {
        console.error('❌ .contact-detail[1] element not found');
    }

    // Apply tag-based color scheme
    console.log('About to apply tag color for:', contact.tag);
    if (typeof applyTagColor === 'function') {
        applyTagColor(contact.tag);
    } else {
        console.error('❌ applyTagColor function not found!');
    }
    
    // Update position counter
    updatePositionCounter();
    
    console.log(`✓ Displayed contact ${index + 1}:`, contact.name);
}

// Show placeholder when no contacts
function showEmptyCard() {
    const nameElement = document.querySelector('.contact-name');
    const tagElement = document.querySelector('.contact-tag');
    
    if (nameElement) nameElement.textContent = 'No Contacts Yet';
    if (tagElement) tagElement.textContent = 'Upload contacts to start';
    
    const details = document.querySelectorAll('.contact-detail');
    details.forEach(detail => detail.textContent = '');
    
    // Reset to default color
    if (typeof resetCardColor === 'function') {
        resetCardColor();
    }
    
    updatePositionCounter();
}

// Update position counter
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

// Navigate to next contact
function nextContact() {
    if (contactsArray.length === 0) return;
    currentIndex = (currentIndex + 1) % contactsArray.length;
    displayContact(currentIndex);
}

// Navigate to previous contact
function previousContact() {
    if (contactsArray.length === 0) return;
    currentIndex = (currentIndex - 1 + contactsArray.length) % contactsArray.length;
    displayContact(currentIndex);
}

// Update contacts count card
function updateContactsCount(count) {
    const countElement = document.getElementById('contactsCountNumber');
    if (countElement) {
        countElement.textContent = count;
    }
}

console.log('✓ contactsManager.js loaded');














/*


// =============================================
// CONTACTS MANAGER
// Core functions for managing contact display
// =============================================

let contactsArray = [];      // All contacts from database
let currentIndex = 0;        // Currently displayed contact
let totalContacts = 0;

// Main function to update the card with contact details
function displayContact(index) {
    if (contactsArray.length === 0) {
        showEmptyCard();
        return;
    }
    
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
    
    // Update phone
    const phoneDetail = document.querySelectorAll('.contact-detail')[0];
    if (phoneDetail) {
        phoneDetail.innerHTML = `📞 ${contact.phone || 'No phone'}`;
    }
    
    // Update email
    const emailDetail = document.querySelectorAll('.contact-detail')[1];
    if (emailDetail) {
        emailDetail.innerHTML = `✉️ ${contact.email || 'No email'}`;
    }

        // Apply tag-based color scheme
    applyTagColor(contact.tag);
    
    // Update position counter
    updatePositionCounter();
    
    console.log(`Displaying contact ${index + 1}:`, contact.name);
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

// Update position counter
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

// Navigate to next contact
function nextContact() {
    if (contactsArray.length === 0) return;
    currentIndex = (currentIndex + 1) % contactsArray.length;
    displayContact(currentIndex);
}

// Navigate to previous contact
function previousContact() {
    if (contactsArray.length === 0) return;
    currentIndex = (currentIndex - 1 + contactsArray.length) % contactsArray.length;
    displayContact(currentIndex);
}

// Update contacts count card
function updateContactsCount(count) {
    const countElement = document.getElementById('contactsCountNumber');
    if (countElement) {
        countElement.textContent = count;
    }
}