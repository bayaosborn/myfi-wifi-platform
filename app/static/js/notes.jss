// notes.js - Handle notes for individual contacts

// Get contact ID from URL
function getContactIdFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('contact_id');
}

// Fetch and display notes for a contact
async function loadNotes() {
    const contactId = getContactIdFromURL();
    
    if (!contactId) {
        console.error('No contact ID provided');
        return;
    }

    try {
        const response = await fetch(`/api/notes/${contactId}`);
        const data = await response.json();

        if (data.success) {
            displayNotes(data.notes);
            updateContactName(data.contact_name);
        }
    } catch (error) {
        console.error('Error loading notes:', error);
    }
}

// Display notes in the UI
function displayNotes(notes) {
    const container = document.getElementById('notesContainer');
    
    if (!notes || notes.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #999; padding: 20px;">No notes yet. Add your first note!</p>';
        return;
    }

    container.innerHTML = notes.map(note => `
        <div class="note-card" data-note-id="${note.id}">
            <div class="note-title">${escapeHtml(note.title)}</div>
            <div class="note-preview">${escapeHtml(note.content)}</div>
            <div class="note-date">
                Added: ${formatDate(note.created_at)}
                <button class="note-delete-btn" onclick="deleteNote(${note.id})">🗑️</button>
            </div>
        </div>
    `).join('');

    // Add click handlers to edit notes
    document.querySelectorAll('.note-card').forEach(card => {
        card.addEventListener('click', (e) => {
            if (!e.target.classList.contains('note-delete-btn')) {
                const noteId = card.dataset.noteId;
                editNote(noteId);
            }
        });
    });
}

// Update contact name in header
function updateContactName(name) {
    const header = document.querySelector('.notes-header');
    if (header && name) {
        header.innerHTML = `
            <span onclick="history.back()">←</span>
            Notes for ${escapeHtml(name)}
        `;
    }
}

// Open add note modal
function openAddNoteModal() {
    const modal = document.getElementById('addNoteModal');
    document.getElementById('noteTitle').value = '';
    document.getElementById('noteContent').value = '';
    modal.style.display = 'flex';
}

// Close add note modal
function closeAddNoteModal() {
    document.getElementById('addNoteModal').style.display = 'none';
}

// Save new note
async function saveNewNote() {
    const contactId = getContactIdFromURL();
    const title = document.getElementById('noteTitle').value.trim();
    const content = document.getElementById('noteContent').value.trim();

    if (!title || !content) {
        alert('Please fill in both title and content');
        return;
    }

    try {
        const response = await fetch('/api/notes/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                contact_id: contactId,
                title: title,
                content: content
            })
        });

        const data = await response.json();

        if (data.success) {
            closeAddNoteModal();
            loadNotes(); // Refresh notes list
        } else {
            alert('Error saving note: ' + data.error);
        }
    } catch (error) {
        console.error('Error saving note:', error);
        alert('Failed to save note');
    }
}

// Edit existing note
async function editNote(noteId) {
    // Get note details
    try {
        const contactId = getContactIdFromURL();
        const response = await fetch(`/api/notes/${contactId}`);
        const data = await response.json();

        if (data.success) {
            const note = data.notes.find(n => n.id == noteId);
            if (note) {
                openEditNoteModal(note);
            }
        }
    } catch (error) {
        console.error('Error loading note:', error);
    }
}

// Open edit note modal
function openEditNoteModal(note) {
    const modal = document.getElementById('editNoteModal');
    document.getElementById('editNoteId').value = note.id;
    document.getElementById('editNoteTitle').value = note.title;
    document.getElementById('editNoteContent').value = note.content;
    modal.style.display = 'flex';
}

// Close edit note modal
function closeEditNoteModal() {
    document.getElementById('editNoteModal').style.display = 'none';
}

// Save edited note
async function saveEditedNote() {
    const noteId = document.getElementById('editNoteId').value;
    const title = document.getElementById('editNoteTitle').value.trim();
    const content = document.getElementById('editNoteContent').value.trim();

    if (!title || !content) {
        alert('Please fill in both title and content');
        return;
    }

    try {
        const response = await fetch(`/api/notes/${noteId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: title,
                content: content
            })
        });

        const data = await response.json();

        if (data.success) {
            closeEditNoteModal();
            loadNotes(); // Refresh notes list
        } else {
            alert('Error updating note: ' + data.error);
        }
    } catch (error) {
        console.error('Error updating note:', error);
        alert('Failed to update note');
    }
}

// Delete note
async function deleteNote(noteId) {
    if (!confirm('Are you sure you want to delete this note?')) {
        return;
    }

    try {
        const response = await fetch(`/api/notes/${noteId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            loadNotes(); // Refresh notes list
        } else {
            alert('Error deleting note: ' + data.error);
        }
    } catch (error) {
        console.error('Error deleting note:', error);
        alert('Failed to delete note');
    }
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return date.toLocaleDateString('en-US', options);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadNotes();

    // Add event listener for add note button
    const addBtn = document.querySelector('.add-note-btn');
    if (addBtn) {
        addBtn.addEventListener('click', openAddNoteModal);
    }
});