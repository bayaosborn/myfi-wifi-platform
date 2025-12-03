// =============================================
// CONTACTS DISPLAY WITH SEARCH (FIXED VERSION)
// =============================================

let contactsArray = [];          // All contacts from database
let filteredContacts = [];       // Filtered results (for search)
//let currentIndex = 0;
//let totalContacts = 0;
let isSearching = false;

// Tag colors
const TAG_COLORS = {
    "family": "#FFE7ED",
    "friends": "#E9F7FF",
    "work": "#F3F0FF",
    "relationship": "#FFEFE3",
    "riders": "#E8FFE8",
    "favorite": "#FFFBDC",
    "general": "#FFFFFF"
};






async function loadContactsFromDatabase() {
    try {
        const response = await fetch("/api/contacts?page=1&per_page=10000");
        const data = await response.json();

        if (!data.contacts || data.contacts.length === 0) {
            showEmptyCard();
            return;
        }

        // Store previously viewed ID
        const previousId = currentEditingContactId;

        // Update arrays
        contactsArray = data.contacts;
        filteredContacts = isSearching ? contactsArray.filter(c => {
            const query = document.getElementById('contactSearchInput').value.trim().toLowerCase();
            return c.name.toLowerCase().includes(query) ||
                   (c.phone || '').toLowerCase().includes(query) ||
                   (c.email || '').toLowerCase().includes(query);
        }) : contactsArray;

        totalContacts = data.total;

        // Find contact in active array
        let idx = 0; // default to first
        if (previousId) {
            idx = filteredContacts.findIndex(c => c.id === previousId);
            if (idx === -1) idx = 0; // fallback if not found
        }

        currentIndex = idx;
        displayContact(currentIndex);

        if (typeof updateContactsCount === "function") {
            updateContactsCount(totalContacts);
        }

        console.log(`✓ Loaded ${totalContacts} contacts`);

    } catch (err) {
        console.error("Load error:", err);
        showEmptyCard();
    }
}





/*
// Load contacts from database
async function loadContactsFromDatabase() {
    try {
        const response = await fetch("/api/contacts?page=1&per_page=10000");
        const data = await response.json();

        if (!data.contacts || data.contacts.length === 0) {
            showEmptyCard();
            return;
        }




        
       // contactsArray = data.contacts;
       // filteredContacts = contactsArray; // Initially show all
       // totalContacts = data.total;
       // currentIndex = 0;
      //  displayContact(currentIndex);


        // store previously viewed ID if it exists
const previousId = currentEditingContactId;

// overwrite list
contactsArray = data.contacts;
filteredContacts = contactsArray;
totalContacts = data.total;

// if there was a previously viewed contact, restore it
if (previousId) {
    const idx = contactsArray.findIndex(c => c.id === previousId);
    if (idx !== -1) {
        currentIndex = idx;
        displayContact(idx);
        return;   // stop here
    }
}

// otherwise default behavior
currentIndex = 0;
displayContact(0);








        if (typeof updateContactsCount === "function") {
            updateContactsCount(totalContacts);
        }

        console.log(`✓ Loaded ${totalContacts} contacts`);

    } catch (err) {
        console.error("Load error:", err);
        showEmptyCard();
    }
}
*/






// Display contact on card
function displayContact(index) {
    const activeArray = isSearching ? filteredContacts : contactsArray;

    if (activeArray.length === 0) {
        showEmptyCard();
        return;
    }

    const contact = activeArray[index];

    //Adding this here so currentEditingContactId passes id directly from the card and prevent returning first contact in case of reload, search or adding other contacts 
    currentEditingContactId = contact.id;

    // Update name
    document.querySelector(".contact-name").textContent = contact.name || "Unknown";

    // Update tag
    const tagText = contact.tag || "General";
    document.querySelector(".contact-tag").textContent = tagText;

    // Update phone & email
    document.querySelectorAll(".contact-detail")[0].innerHTML = `📞 ${contact.phone || "No phone"}`;
    document.querySelectorAll(".contact-detail")[1].innerHTML = `✉️ ${contact.email || "No email"}`;

    // Change card color
    const tagKey = tagText.toLowerCase().trim();
    const bgColor = TAG_COLORS[tagKey] || TAG_COLORS["general"];
    document.querySelector(".main-card").style.backgroundColor = bgColor;

    // Update Logic card
    updateLogicCard(contact.name);

    // Update counter
    updatePositionCounter();
}













// Show empty state
function showEmptyCard() {
    document.querySelector(".contact-name").textContent = "No Contacts";
    document.querySelector(".contact-tag").textContent = isSearching ? "No matches found" : "Add contacts to start";
    document.querySelectorAll(".contact-detail").forEach(d => d.textContent = "");
    document.querySelector(".main-card").style.backgroundColor = "#FFFFFF";
    updatePositionCounter();
}

// Update Logic card
function updateLogicCard(name) {
    const logicText = document.querySelector(".logic-text");
    if (logicText) {
        logicText.innerHTML = `You haven't called <b>${name}</b> in 2 days.<br>Consider giving them a quick check-in.`;
    }
}

// Navigation
function nextContact() {
    const activeArray = isSearching ? filteredContacts : contactsArray;
    if (activeArray.length === 0) return;

    currentIndex = (currentIndex + 1) % activeArray.length;
    displayContact(currentIndex);
}

function previousContact() {
    const activeArray = isSearching ? filteredContacts : contactsArray;
    if (activeArray.length === 0) return;

    currentIndex = (currentIndex - 1 + activeArray.length) % activeArray.length;
    displayContact(currentIndex);
}

// Update position counter
function updatePositionCounter() {
    const activeArray = isSearching ? filteredContacts : contactsArray;
    const counter = document.getElementById("contactPosition");
    
    if (counter) {
        if (activeArray.length === 0) {
            counter.textContent = "0 of 0";
        } else {
            counter.textContent = `${currentIndex + 1} of ${activeArray.length}`;
        }
    }
}

// Update contacts count card
function updateContactsCount(count) {
    const countElement = document.getElementById('contactsCountNumber');
    if (countElement) {
        countElement.textContent = count;
    }
}

// SEARCH FUNCTIONALITY
function setupSearch() {
    const searchInput = document.getElementById('contactSearchInput');
    
    if (!searchInput) {
        console.warn('Search input not found');
        return;
    }

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim().toLowerCase();

        if (query === '') {
            // Reset to full list
            isSearching = false;
            filteredContacts = contactsArray;
            currentIndex = 0;
            displayContact(currentIndex);
            return;
        }

        // Filter contacts
        isSearching = true;
        filteredContacts = contactsArray.filter(contact => {
            const name = (contact.name || '').toLowerCase();
            const phone = (contact.phone || '').toLowerCase();
            const email = (contact.email || '').toLowerCase();
            
            return name.includes(query) || phone.includes(query) || email.includes(query);
        });

        // Show first result or empty
        currentIndex = 0;
        if (filteredContacts.length > 0) {
            displayContact(currentIndex);
        } else {
            showEmptyCard();
        }
    });

    console.log('✓ Search connected');
}

// Setup navigation buttons (ONCE)
let navigationSetup = false;

function setupNavigation() {
    if (navigationSetup) return;

    const prevBtn = document.getElementById('prevContactBtn');
    const nextBtn = document.getElementById('nextContactBtn');

    if (prevBtn && nextBtn) {
        prevBtn.onclick = previousContact;
        nextBtn.onclick = nextContact;
        navigationSetup = true;
        console.log('✓ Navigation connected');
    }
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
    console.log('Initializing contacts system...');
    setupNavigation();
    setupSearch();
    loadContactsFromDatabase();
});