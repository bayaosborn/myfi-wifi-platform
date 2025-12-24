"""
Contacts CRUD Routes - Phone Auth Compatible
All contact management operations
"""

from flask import Blueprint, request, jsonify, session, redirect
from functools import wraps
from app.backend.supabase_client import supabase

contacts_bp = Blueprint('contacts', __name__)

# ==================== HELPER FUNCTIONS ====================

def login_required(f):
    """Decorator to protect routes - Phone Auth Compatible"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def get_user_id():
    """Get current user ID from session"""
    return session.get('user_id')

# ==================== CRUD OPERATIONS ====================

@contacts_bp.route('/api/contacts', methods=['GET'])
@login_required
def get_contacts():
    """Get all contacts for logged-in user with pagination"""
    try:
        user_id = get_user_id()
        
        # Get query params
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 13, type=int)
        tag_filter = request.args.get('tag', None)
        
        # Build filters
        filters = {'user_id': user_id}
        if tag_filter:
            filters['tag'] = tag_filter
        
        # Get contacts from Supabase (no access_token needed)
        contacts = supabase.select('contacts', filters=filters)
        
        # Sort by name
        contacts_sorted = sorted(contacts, key=lambda x: x.get('name', '').lower())
        
        # Calculate pagination
        total = len(contacts_sorted)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_contacts = contacts_sorted[start:end]
        
        return jsonify({
            'success': True,
            'contacts': paginated_contacts,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }), 200
        
    except Exception as e:
        print(f"Get contacts error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_bp.route('/api/contacts/<contact_id>', methods=['GET'])
@login_required
def get_contact(contact_id):
    """Get a single contact by ID"""
    try:
        user_id = get_user_id()
        
        # Get contact (RLS ensures user can only see their own)
        contacts = supabase.select('contacts', filters={'id': contact_id, 'user_id': user_id})
        
        if contacts and len(contacts) > 0:
            return jsonify({'success': True, 'contact': contacts[0]}), 200
        else:
            return jsonify({'success': False, 'error': 'Contact not found'}), 404
            
    except Exception as e:
        print(f"Get contact error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_bp.route('/api/contacts', methods=['POST'])
@login_required
def create_contact():
    """Create a new contact"""
    try:
        user_id = get_user_id()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'success': False, 'error': 'Name is required'}), 400
        
        # Prepare contact data
        contact_data = {
            'user_id': user_id,
            'name': data.get('name', '').strip(),
            'phone': data.get('phone', '').strip(),
            'email': data.get('email', '').strip(),
            'tag': data.get('tag', 'General').strip(),
            'notes': data.get('notes', '').strip(),
            'is_favorite': data.get('is_favorite', False),
            'is_emergency_contact': data.get('is_emergency_contact', False)
        }
        
        # Insert into Supabase
        result = supabase.insert('contacts', contact_data)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Contact created successfully',
                'contact': result['data'][0] if result['data'] else None
            }), 201
        else:
            return jsonify({'success': False, 'error': result['error']}), 400
            
    except Exception as e:
        print(f"Create contact error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_bp.route('/api/contacts/<contact_id>', methods=['PUT'])
@login_required
def update_contact(contact_id):
    """Update an existing contact"""
    try:
        user_id = get_user_id()
        data = request.get_json()
        
        # Prepare update data
        allowed_fields = ['name', 'phone', 'email', 'tag', 'notes', 'is_favorite', 'is_emergency_contact']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not update_data:
            return jsonify({'success': False, 'error': 'No valid fields to update'}), 400
        
        # Update in Supabase
        success = supabase.update('contacts', {'id': contact_id, 'user_id': user_id}, update_data)
        
        if success:
            return jsonify({'success': True, 'message': 'Contact updated successfully'}), 200
        else:
            return jsonify({'success': False, 'error': 'Update failed'}), 400
            
    except Exception as e:
        print(f"Update contact error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_bp.route('/api/contacts/<contact_id>', methods=['DELETE'])
@login_required
def delete_contact(contact_id):
    """Delete a contact"""
    try:
        user_id = get_user_id()
        
        # Delete from Supabase
        success = supabase.delete('contacts', {'id': contact_id, 'user_id': user_id})
        
        if success:
            return jsonify({'success': True, 'message': 'Contact deleted successfully'}), 200
        else:
            return jsonify({'success': False, 'error': 'Delete failed'}), 404
            
    except Exception as e:
        print(f"Delete contact error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_bp.route('/api/contacts/search', methods=['GET'])
@login_required
def search_contacts():
    """Search contacts by name, phone, or email"""
    try:
        user_id = get_user_id()
        query = request.args.get('q', '').strip().lower()
        
        if not query:
            return jsonify({'success': False, 'error': 'Search query required'}), 400
        
        # Get all user's contacts
        contacts = supabase.select('contacts', filters={'user_id': user_id})
        
        # Filter by search query
        results = []
        for contact in contacts:
            name = contact.get('name', '').lower()
            phone = contact.get('phone', '').lower()
            email = contact.get('email', '').lower()
            
            if query in name or query in phone or query in email:
                results.append(contact)
        
        return jsonify({'success': True, 'contacts': results, 'count': len(results)}), 200
        
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_bp.route('/api/contacts/tag/<tag>', methods=['GET'])
@login_required
def get_contacts_by_tag(tag):
    """Get all contacts with a specific tag"""
    try:
        user_id = get_user_id()
        
        # Get contacts by tag
        contacts = supabase.select('contacts', filters={'user_id': user_id, 'tag': tag})
        
        # Sort by name
        contacts_sorted = sorted(contacts, key=lambda x: x.get('name', '').lower())
        
        return jsonify({
            'success': True,
            'contacts': contacts_sorted,
            'count': len(contacts_sorted),
            'tag': tag
        }), 200
        
    except Exception as e:
        print(f"Get by tag error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_bp.route('/api/contacts/delete-all', methods=['DELETE'])
@login_required
def delete_all_contacts():
    """Delete ALL contacts for the current user"""
    try:
        user_id = get_user_id()
        
        # Get count before deletion
        contacts = supabase.select('contacts', filters={'user_id': user_id})
        count = len(contacts)
        
        # Delete all user's contacts
        success = supabase.delete('contacts', {'user_id': user_id})
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Deleted {count} contacts',
                'deleted_count': count
            }), 200
        else:
            return jsonify({'success': False, 'error': 'Delete failed'}), 400
            
    except Exception as e:
        print(f"Delete all error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_bp.route('/api/contacts/count', methods=['GET'])
@login_required
def get_contacts_count():
    """Get total count of user's contacts"""
    try:
        user_id = get_user_id()
        
        # Get count
        total = supabase.count('contacts', filters={'user_id': user_id})
        
        return jsonify({'success': True, 'total': total}), 200
        
    except Exception as e:
        print(f"Count error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500