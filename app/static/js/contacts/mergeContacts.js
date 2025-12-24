
/*

// Check for duplicates on page load
async function checkDuplicates() {
    const response = await fetch('/api/contacts/find-duplicates');
    const data = await response.json();
    
    const button = document.getElementById('merge-btn');
    if (data.total_duplicate_contacts > 0) {
        button.textContent = `Merge Duplicates (${data.total_duplicate_contacts} found)`;
        button.disabled = false;
    } else {
        button.textContent = 'No Duplicates Found';
        button.disabled = true;
    }
}

*/



// Open modal and load duplicate count
async function openMergeModal() {
    try {
        const response = await fetch('/api/contacts/find-duplicates');
        const data = await response.json();
        
        if (data.success && data.total_duplicate_contacts > 0) {
            document.getElementById('modalDuplicateCount').textContent = data.total_duplicate_contacts;
            document.getElementById('confirmModal').classList.add('active');
        } else {
            alert('No duplicates found!');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to check duplicates');
    }
}

// Close modal
function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// Close success modal and refresh
function closeSuccessAndRefresh() {
    closeModal('successModal');
    setTimeout(() => location.reload(), 300);
}

// Close modal when clicking outside
document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.classList.remove('active');
        }
    });
});







async function checkDuplicates() {
    try {
        const response = await fetch('/api/contacts/find-duplicates');
        
        if (!response.ok) {
            console.error('Failed to check duplicates:', response.status);
            return;
        }
        
        const data = await response.json();
        
        const button = document.getElementById('merge-btn');
        
        if (!button) {
            console.error('Merge button not found');
            return;
        }
        
        if (data.success && data.total_duplicate_contacts > 0) {
            button.textContent = `Merge Duplicates (${data.total_duplicate_contacts} found)`;
            button.disabled = false;
        } else {
            button.textContent = 'No Duplicates Found';
            button.disabled = true;
        }
        
    } catch (error) {
        console.error('Error checking duplicates:', error);
    }
}




async function mergeDuplicates() {
    const btn = document.getElementById('modalMergeBtn');
    const btnText = document.getElementById('modalMergeBtnText');
    const spinner = document.getElementById('modalMergeSpinner');
    
    // Show loading
    btn.disabled = true;
    btnText.textContent = 'Merging...';
    spinner.classList.remove('hidden');
    
    try {
        const response = await fetch('/api/contacts/merge-duplicates', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            // Close confirmation modal
            closeModal('confirmModal');
            
            // Show success modal with stats
            document.getElementById('mergedGroups').textContent = data.merged_groups;
            document.getElementById('deletedContacts').textContent = data.deleted_contacts;
            document.getElementById('successMessage').textContent = data.message;
            
            setTimeout(() => {
                document.getElementById('successModal').classList.add('active');
            }, 300);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Merge error:', error);
        alert('Failed to merge. Please try again.');
    } finally {
        // Reset button
        btn.disabled = false;
        btnText.textContent = 'Merge Now';
        spinner.classList.add('hidden');
    }
}





/*

// Merge duplicates with confirmation
async function mergeDuplicates() {
    // Get count first
    const checkResponse = await fetch('/api/contacts/find-duplicates');
    const checkData = await checkResponse.json();
    
    if (!confirm(`Found ${checkData.total_duplicate_contacts} duplicate contacts. Merge now?`)) {
        return;
    }
    
    // Execute merge
    const response = await fetch('/api/contacts/merge-duplicates', {
        method: 'POST'
    });
    const data = await response.json();
    
    if (data.success) {
        alert(data.message);
        location.reload(); // Refresh to show updated list
    } else {
        alert('Error: ' + data.error);
    }
}


*/

// Call on page load
checkDuplicates();