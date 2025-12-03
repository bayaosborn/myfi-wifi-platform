// =============================================
// LOGIC INTEGRATION
// Handles Logic AI recommendations and analysis
// =============================================

// Update logic card with current contact's analysis
function updateLogicCard(contactName) {
    const logicText = document.querySelector('.logic-text');
    if (logicText) {
        logicText.innerHTML = `
            You haven't called <b>${contactName}</b> in 2 days.<br>
            Consider giving them a quick check-in.
        `;
    }
}

// Function for Logic to recommend a specific contact
function showRecommendedContact(contactId) {
    const index = contactsArray.findIndex(c => c.id === contactId);
    if (index !== -1) {
        currentIndex = index;
        displayContact(currentIndex);
        updateLogicCard(contactsArray[index].name);
    }
}

// Function for Logic to get contact analytics
function getContactAnalytics() {
    // Return data for Logic to analyze
    return {
        totalContacts: contactsArray.length,
        contactsByTag: groupContactsByTag(),
        lastDisplayedContact: contactsArray[currentIndex]
    };
}

function groupContactsByTag() {
    const groups = {};
    contactsArray.forEach(contact => {
        const tag = contact.tag || 'General';
        groups[tag] = (groups[tag] || 0) + 1;
    });
    return groups;
}