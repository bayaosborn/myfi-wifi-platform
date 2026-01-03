/**
 * Notes App - Main Logic
 * Handles tabs, CRUD operations, infinite scroll, sharing
 */

class NotesApp {
    constructor() {
        this.currentTab = 'public';
        this.notes = [];
        this.contacts = [];
        this.editingNote = null;
        
        // DOM elements
        this.feed = document.getElementById('feed');
        this.modal = document.getElementById('noteModal');
        this.addBtn = document.getElementById('addBtn');
        this.closeModal = document.getElementById('closeModal');
        this.noteForm = document.getElementById('noteForm');
        this.loading = document.getElementById('loading');
        
        this.init();
    }
    
    init() {
        console.log('✅ Notes app initialized');
        
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });
        
        // Add button
        this.addBtn.addEventListener('click', () => {
            this.openModal();
        });
        
        // Close modal
        this.closeModal.addEventListener('click', () => {
            this.closeModalFn();
        });
        
        document.getElementById('cancelBtn').addEventListener('click', () => {
            this.closeModalFn();
        });
        
        // Form submit
        this.noteForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveNote();
        });
        
        // Note type radio buttons
        document.querySelectorAll('input[name="noteType"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.handleNoteTypeChange(e.target.value);
            });
        });
        
        // Listen for edit/delete/share events from NoteCard
        window.addEventListener('editNote', (e) => {
            this.openModal(e.detail);
        });
        
        window.addEventListener('deleteNote', (e) => {
            this.deleteNote(e.detail.id);
        });
        
        window.addEventListener('shareNote', (e) => {
            this.shareNote(e.detail);
        });
        
        // Load initial data
        this.loadContacts();
        this.loadNotes();
    }
    
    switchTab(tab) {
        this.currentTab = tab;
        
        // Update active button
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tab);
        });
        
        // Load notes for this tab
        this.loadNotes();
    }
    
    async loadNotes() {
        this.showLoading(true);
        
        let endpoint;
        if (this.currentTab === 'public') {
            endpoint = '/api/notes/public';
        } else if (this.currentTab === 'private') {
            endpoint = '/api/notes/private';
        } else {
            endpoint = '/api/notes/contacts';
        }
        
        try {
            const response = await fetch(endpoint);
            const data = await response.json();
            
            if (data.success) {
                this.notes = data.notes;
                this.renderNotes();
            } else {
                console.error('❌ Load notes error:', data.error);
            }
        } catch (error) {
            console.error('❌ API error:', error);
        } finally {
            this.showLoading(false);
        }
    }
    
    renderNotes() {
        // Clear feed
        this.feed.innerHTML = '';
        
        if (this.notes.length === 0) {
            this.showEmptyState();
            return;
        }
        
        // Render each note
        this.notes.forEach(note => {
            const canEdit = this.currentTab !== 'public'; // Can edit own notes
            const card = new NoteCard(note, canEdit);
            this.feed.appendChild(card.render());
        });
    }
    
    showEmptyState() {
        const empty = document.createElement('div');
        empty.className = 'empty-state';
        
        let message = '';
        if (this.currentTab === 'public') {
            message = 'No public notes yet. Be the first to share!';
        } else if (this.currentTab === 'private') {
            message = 'No private notes. Start writing your thoughts.';
        } else {
            message = 'No contact notes. Add notes about your contacts.';
        }
        
        empty.innerHTML = `
            <p>${message}</p>
            <button onclick="notesApp.openModal()" style="
                padding: 12px 24px;
                background: var(--accent);
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
            ">Create Note</button>
        `;
        
        this.feed.appendChild(empty);
    }
    
    openModal(note = null) {
        this.editingNote = note;
        
        // Set modal title
        document.getElementById('modalTitle').textContent = 
            note ? 'Edit Note' : 'New Note';
        
        if (note) {
            // Populate form
            document.getElementById('noteTitle').value = note.title || '';
            document.getElementById('noteContent').value = note.content || '';
            
            // Set note type
            if (note.is_public) {
                document.querySelector('input[value="public"]').checked = true;
            } else if (note.contact_id) {
                document.querySelector('input[value="contact"]').checked = true;
                document.getElementById('contactSelect').style.display = 'block';
                document.getElementById('contactDropdown').value = note.contact_id;
            } else {
                document.querySelector('input[value="private"]').checked = true;
            }
        } else {
            // Clear form
            this.noteForm.reset();
            document.getElementById('contactSelect').style.display = 'none';
        }
        
        this.modal.classList.add('active');
    }
    
    closeModalFn() {
        this.modal.classList.remove('active');
        this.editingNote = null;
        this.noteForm.reset();
    }
    
    handleNoteTypeChange(type) {
        const contactSelect = document.getElementById('contactSelect');
        
        if (type === 'contact') {
            contactSelect.style.display = 'block';
        } else {
            contactSelect.style.display = 'none';
        }
    }
    
    async loadContacts() {
        try {
            const response = await fetch('/api/contacts');
            const data = await response.json();
            
            if (data.success) {
                this.contacts = data.contacts;
                this.populateContactDropdown();
            }
        } catch (error) {
            console.error('❌ Load contacts error:', error);
        }
    }
    
    populateContactDropdown() {
        const dropdown = document.getElementById('contactDropdown');
        
        // Clear existing options (except first)
        dropdown.innerHTML = '<option value="">Select a contact...</option>';
        
        // Add contacts
        this.contacts.forEach(contact => {
            const option = document.createElement('option');
            option.value = contact.id;
            option.textContent = contact.name;
            dropdown.appendChild(option);
        });
    }
    
    async saveNote() {
        const title = document.getElementById('noteTitle').value.trim();
        const content = document.getElementById('noteContent').value.trim();
        const noteType = document.querySelector('input[name="noteType"]:checked').value;
        
        if (!content) {
            alert('Content is required');
            return;
        }
        
        // Prepare data
        const noteData = {
            title: title || null,
            content: content,
            is_public: noteType === 'public',
            contact_id: null
        };
        
        if (noteType === 'contact') {
            const contactId = document.getElementById('contactDropdown').value;
            if (!contactId) {
                alert('Please select a contact');
                return;
            }
            noteData.contact_id = contactId;
        }
        
        this.showLoading(true);
        
        try {
            let response;
            if (this.editingNote) {
                // Update
                response = await fetch(`/api/notes/${this.editingNote.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(noteData)
                });
            } else {
                // Create
                response = await fetch('/api/notes', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(noteData)
                });
            }
            
            const data = await response.json();
            
            if (data.success) {
                console.log('✅ Note saved');
                this.closeModalFn();
                this.loadNotes();
            } else {
                alert('Failed to save note: ' + data.message);
            }
        } catch (error) {
            console.error('❌ Save error:', error);
            alert('Connection error');
        } finally {
            this.showLoading(false);
        }
    }
    
    async deleteNote(noteId) {
        this.showLoading(true);
        
        try {
            const response = await fetch(`/api/notes/${noteId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log('✅ Note deleted');
                this.loadNotes();
            } else {
                alert('Failed to delete note');
            }
        } catch (error) {
            console.error('❌ Delete error:', error);
            alert('Connection error');
        } finally {
            this.showLoading(false);
        }
    }
    
    shareNote(note) {
        // If public note, generate shareable link
        if (note.is_public) {
            const shareUrl = `${window.location.origin}/notes/share/${note.id}`;
            
            // Copy to clipboard
            navigator.clipboard.writeText(shareUrl).then(() => {
                alert('📋 Link copied! Share on WhatsApp, Twitter, etc.');
            }).catch(() => {
                // Fallback: show prompt
                prompt('Copy this link:', shareUrl);
            });
        } else {
            // Private/Contact note: Generate text to share
            this.generateNoteText(note);
        }
    }
    
    generateNoteText(note) {
        // For private notes, create shareable text
        const shareText = `${note.title ? note.title + '\n\n' : ''}${note.content}\n\n— Shared from MyFi`;
        
        navigator.clipboard.writeText(shareText).then(() => {
            alert('📋 Note copied as text! Paste to share.');
        }).catch(() => {
            prompt('Copy this note:', shareText);
        });
    }
    
    showLoading(show) {
        if (show) {
            this.loading.classList.add('active');
        } else {
            this.loading.classList.remove('active');
        }
    }
}

// Initialize app
let notesApp;
document.addEventListener('DOMContentLoaded', () => {
    notesApp = new NotesApp();
});