
// 1. Button triggers real file input
document.getElementById('uploadBtn').addEventListener('click', () => {
    document.getElementById('contactsFileInput').click();
});

// 2. File input handles upload
document.getElementById('contactsFileInput').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    const status = document.getElementById('status');
    status.textContent = 'Uploading...';

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            status.textContent = `✓ Loaded ${data.count} contacts`;

            // Update stats card
            updateContactsCount(data.count);

        } else {
            status.textContent = `✗ Upload failed: ${data.error}`;
        }
    } catch (error) {
        status.textContent = '✗ Upload failed';
        console.error(error);
    }
});

















/*
// Function to update the number in the card
function updateContactsCount(count) {
    const countElement = document.getElementById('contactsCountNumber');
    if (countElement) {
        countElement.textContent = count;
    }
}

// Clicking the button triggers the hidden file input
document.getElementById('uploadBtn').addEventListener('click', () => {
    document.getElementById('contactsFileInput').click();
});

let contactsLoaded = false;

// File upload handler
document.getElementById('contactsFileInput').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    const status = document.getElementById('status');
    status.textContent = 'Uploading...';

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            status.textContent = `✓ Loaded ${data.count} contacts`;
            contactsLoaded = true;
            
            // Reload contacts from database
            if (typeof loadContactsFromDatabase === 'function') {
                await loadContactsFromDatabase();
            }
            
            // Close the modal after successful upload
            setTimeout(() => {
                closeModals();
            }, 1500);
            
        } else {
            status.textContent = '✗ Upload failed: ' + data.error;
        }
    } catch (error) {
        status.textContent = '✗ Upload failed';
        console.error('Upload error:', error);
    }
});


*/


















/*
// Function to update the number in the card (DEFINE THIS FIRST)
function updateContactsCount(count) {
    const countElement = document.getElementById('contactsCountNumber');
    if (countElement) {
        countElement.textContent = count;
    }
}

// Clicking the button triggers the hidden file input
document.getElementById('uploadBtn').addEventListener('click', () => {
    document.getElementById('contactsFileInput').click();
});

let contactsLoaded = false;

// Now this works because it's an actual <input type="file">
document.getElementById('contactsFileInput').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    const status = document.getElementById('status');
    status.textContent = 'Uploading...';

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            status.textContent = `✓ Loaded ${data.count} contacts`;
            contactsLoaded = true;
            
            // Update the stats card number
            updateContactsCount(data.count);
            
            // Close the modal after successful upload
            setTimeout(() => {
                closeModals(); // This function is defined in your HTML
            }, 1500); // Give user 1.5 seconds to see the success message
            
        } else {
            status.textContent = '✗ Upload failed: ' + data.error;
        }
    } catch (error) {
        status.textContent = '✗ Upload failed';
        console.error('Upload error:', error);
    }
});