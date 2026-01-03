"""
Notes Routes
API endpoints for public/private/contact notes
"""

from flask import Blueprint, request, jsonify, session, render_template, redirect
from functools import wraps
from app.backend.supabase_client import supabase
from datetime import datetime

notes_bp = Blueprint('notes', __name__)


def login_required(f):
    """Decorator to protect routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


# ==================== PAGE ROUTES ====================

@notes_bp.route('/notes')
#@login_required
def notes_page():
    """Main notes page"""
    return render_template('notes/notes.html')


@notes_bp.route('/notes/share/<note_id>')
def share_note(note_id):
    """
    Public shareable note page
    Anyone with link can view
    """
    try:
        # Get note
        notes = supabase.select('notes', filters={'id': note_id})
        
        if not notes or not notes[0].get('is_public'):
            return "Note not found or is private", 404
        
        note = notes[0]
        
        # Get author username
        try:
            user = supabase.select('profiles', filters={'id': note['user_id']})
            username = 'Anonymous'
            if user and len(user) > 0:
                username = user[0].get('username') or user[0].get('full_name') or 'Anonymous'
            note['username'] = username
        except Exception as e:
            print(f"⚠️ Error fetching username: {e}")
            note['username'] = 'Anonymous'
        
        return render_template('notes/share.html', note=note)
        
    except Exception as e:
        print(f"❌ Share note error: {e}")
        return "Error loading note", 500


# ==================== API ROUTES ====================

@notes_bp.route('/api/notes/public', methods=['GET'])
#@login_required
def get_public_notes():
    """
    Get all public notes from all users
    
    Query params:
        limit: int (default: 20)
        offset: int (default: 0)
    """
    try:
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Get public notes (filter contact_id on client side)
        all_notes = supabase.select(
            'notes',
            filters={'is_public': True}
        )
        
        # Filter where contact_id is None/null
        notes = [note for note in all_notes if not note.get('contact_id')]
        
        # Fetch usernames for public notes
        for note in notes:
            try:
                user = supabase.select('profiles', filters={'id': note['user_id']})
                if user and len(user) > 0:
                    note['username'] = user[0].get('username') or user[0].get('full_name') or 'Anonymous'
                else:
                    note['username'] = 'Anonymous'
            except Exception as e:
                print(f"⚠️ Error fetching username: {e}")
                note['username'] = 'Anonymous'
        
        # Sort by created_at descending
        notes_sorted = sorted(
            notes, 
            key=lambda x: x.get('created_at', ''), 
            reverse=True
        )
        
        # Paginate
        paginated = notes_sorted[offset:offset + limit]
        
        return jsonify({
            'success': True,
            'notes': paginated,
            'count': len(paginated),
            'total': len(notes_sorted)
        }), 200
        
    except Exception as e:
        print(f"❌ Get public notes error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_bp.route('/api/notes/private', methods=['GET'])
@login_required
def get_private_notes():
    """
    Get user's private notes (not attached to contact)
    """
    try:
        user_id = session.get('user_id')
        
        # Get all user's notes, filter contact_id on client side
        all_notes = supabase.select(
            'notes',
            filters={
                'user_id': user_id,
                'is_public': False
            }
        )
        
        # Filter where contact_id is None/null
        notes = [note for note in all_notes if not note.get('contact_id')]
        
        # Sort by created_at descending
        notes_sorted = sorted(
            notes, 
            key=lambda x: x.get('created_at', ''), 
            reverse=True
        )
        
        return jsonify({
            'success': True,
            'notes': notes_sorted,
            'count': len(notes_sorted)
        }), 200
        
    except Exception as e:
        print(f"❌ Get private notes error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_bp.route('/api/notes/contacts', methods=['GET'])
@login_required
def get_contact_notes():
    """
    Get user's notes about contacts
    
    Query params:
        contact_id: uuid (optional - filter by specific contact)
    """
    try:
        user_id = session.get('user_id')
        contact_id = request.args.get('contact_id')
        
        # Get all contact notes (contact_id is NOT NULL)
        all_notes = supabase.select('notes', filters={'user_id': user_id})
        
        # Filter where contact_id is not None
        contact_notes = [
            note for note in all_notes 
            if note.get('contact_id') is not None
        ]
        
        # If specific contact requested, filter further
        if contact_id:
            contact_notes = [
                note for note in contact_notes 
                if note.get('contact_id') == contact_id
            ]
        
        # Sort by created_at descending
        notes_sorted = sorted(
            contact_notes, 
            key=lambda x: x.get('created_at', ''), 
            reverse=True
        )
        
        return jsonify({
            'success': True,
            'notes': notes_sorted,
            'count': len(notes_sorted)
        }), 200
        
    except Exception as e:
        print(f"❌ Get contact notes error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_bp.route('/api/notes', methods=['POST'])
@login_required
def create_note():
    """
    Create a new note
    
    Body:
    {
        "title": "Optional title",
        "content": "Note content (required)",
        "is_public": false,
        "contact_id": "uuid or null",
        "tags": ["tag1", "tag2"]
    }
    """
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        # Validate content
        content = data.get('content', '').strip()
        if not content:
            return jsonify({
                'success': False,
                'message': 'Content is required'
            }), 400
        
        # Prepare note data
        note_data = {
            'user_id': user_id,
            'title': data.get('title', '').strip() or None,
            'content': content,
            'is_public': data.get('is_public', False),
            'contact_id': data.get('contact_id'),
            'tags': data.get('tags', [])
        }
        
        # Insert
        result = supabase.insert('notes', note_data)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Note created',
                'note': result['data'][0]
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to create note'
            }), 400
        
    except Exception as e:
        print(f"❌ Create note error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_bp.route('/api/notes/<note_id>', methods=['PUT'])
@login_required
def update_note(note_id):
    """
    Update a note (user must own it)
    
    Body:
    {
        "title": "Updated title",
        "content": "Updated content",
        "is_public": true,
        "tags": ["updated"]
    }
    """
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        # Verify ownership
        note = supabase.select(
            'notes',
            filters={'id': note_id, 'user_id': user_id}
        )
        
        if not note:
            return jsonify({
                'success': False,
                'message': 'Note not found'
            }), 404
        
        # Prepare updates
        allowed_fields = ['title', 'content', 'is_public', 'tags']
        update_data = {
            k: v for k, v in data.items() 
            if k in allowed_fields
        }
        
        if not update_data:
            return jsonify({
                'success': False,
                'message': 'No fields to update'
            }), 400
        
        # Update
        success = supabase.update(
            'notes',
            {'id': note_id},
            update_data
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Note updated'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Update failed'
            }), 400
        
    except Exception as e:
        print(f"❌ Update note error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_bp.route('/api/notes/<note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    """Delete a note (user must own it)"""
    try:
        user_id = session.get('user_id')
        
        # Delete (RLS ensures user owns it)
        success = supabase.delete(
            'notes',
            {'id': note_id, 'user_id': user_id}
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Note deleted'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Delete failed'
            }), 404
        
    except Exception as e:
        print(f"❌ Delete note error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500