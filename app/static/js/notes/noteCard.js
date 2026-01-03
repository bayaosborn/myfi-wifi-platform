/**
 * Note Card Component
 * Renders a single note in the feed
 */

class NoteCard {
    constructor(note, canEdit = false) {
        this.note = note;
        this.canEdit = canEdit;
    }

    render() {
        const wrapper = document.createElement('div');
        wrapper.className = 'note';
        wrapper.dataset.noteId = this.note.id;

        const card = document.createElement('div');
        card.className = 'note-card';

        /* ---------- Title ---------- */
        if (this.note.title) {
            const title = document.createElement('div');
            title.className = 'note-title';
            title.textContent = this.note.title;

            title.addEventListener('click', () => {
                title.classList.toggle('expanded');
            });

            card.appendChild(title);
        }

        /* ---------- Body ---------- */
        const body = document.createElement('div');
        body.className = 'note-body';
        body.textContent = this.note.content;
        card.appendChild(body);

        /* ---------- Footer ---------- */
        const footer = document.createElement('div');
        footer.className = 'note-footer';

        const author = document.createElement('span');
        author.className = 'note-author';
        author.textContent = this.note.is_public
            ? (this.note.username || 'Anonymous')
            : 'Private';

        const date = document.createElement('span');
        date.className = 'note-date';
        date.textContent = this.formatDate(this.note.created_at);

        footer.appendChild(author);
        footer.appendChild(date);
        card.appendChild(footer);

        /* ---------- Actions (Share / Edit / Delete) ---------- */
        const actions = document.createElement('div');
        actions.className = 'note-actions';

       
        
        
        // Share (always visible)
        const shareBtn = document.createElement('button');
shareBtn.className = 'note-share';
shareBtn.title = 'Share';

shareBtn.innerHTML = `
<svg
  width="18"
  height="18"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="1.8"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  <path d="M4 12 L20 4 L16 20 Z" />
  <line x1="10" y1="12" x2="14" y2="10" />
</svg>
`;

shareBtn.onclick = () => this.onShare();
        actions.appendChild(shareBtn);

        // Edit / Delete (only if user owns note)
        if (this.canEdit) {
            const editBtn = document.createElement('button');
            editBtn.textContent = 'Edit';
            editBtn.onclick = () => this.onEdit();

            const deleteBtn = document.createElement('button');
            deleteBtn.textContent = 'Delete';
            deleteBtn.onclick = () => this.onDelete();

            actions.appendChild(editBtn);
            actions.appendChild(deleteBtn);
        }

        card.appendChild(actions);

        wrapper.appendChild(card);
        return wrapper;
    }

    /* ---------- Helpers ---------- */

    formatDate(dateString) {
        if (!dateString) return '';

        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;

        if (diff < 86400000) {
            const hours = Math.floor(diff / 3600000);
            return hours < 1 ? 'Just now' : `${hours}h ago`;
        }

        if (diff < 604800000) {
            const days = Math.floor(diff / 86400000);
            return `${days}d ago`;
        }

        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric'
        });
    }

    /* ---------- Actions ---------- */

    onEdit() {
        window.dispatchEvent(new CustomEvent('editNote', {
            detail: this.note
        }));
    }

    onDelete() {
        if (confirm('Delete this note?')) {
            window.dispatchEvent(new CustomEvent('deleteNote', {
                detail: this.note
            }));
        }
    }

    onShare() {
        window.dispatchEvent(new CustomEvent('shareNote', {
            detail: this.note
        }));
    }
}