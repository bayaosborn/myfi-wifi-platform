"""
Logic Contact Routes
Separate API endpoints for Logic AI to manage contacts

Prefix: /api/logic/v1/contacts/*
Different from user endpoints in app/routes/contacts.py
"""

from flask import Blueprint, request, jsonify, session
from functools import wraps
from app.logic.contacts.operations import add_contact, edit_contact

logic_contacts_bp = Blueprint('logic_contacts', __name__)


def login_required(f):
    """Decorator to protect routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


@logic_contacts_bp.route('/api/logic/v1/contacts/add', methods=['POST'])
@login_required
def logic_add_contact():
    """
    Logic AI adds a contact
    
    Body:
    {
        "name": "Sarah Johnson",
        "phone": "0712345678",    # Optional
        "email": "sarah@email.com", # Optional
        "tag": "Work"              # Optional, default: General
    }
    
    Response:
    {
        "success": true,
        "contact_id": "uuid",
        "message": "Added Sarah Johnson"
    }
    """
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        # Validate name
        if not data.get('name'):
            return jsonify({
                'success': False,
                'message': 'Name is required'
            }), 400
        
        # Add contact
        result = add_contact(
            user_id=user_id,
            name=data.get('name'),
            phone=data.get('phone'),
            email=data.get('email'),
            tag=data.get('tag', 'General')
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"❌ Logic add contact error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to add contact'
        }), 500


@logic_contacts_bp.route('/api/logic/v1/contacts/edit/<contact_id>', methods=['PUT'])
@login_required
def logic_edit_contact(contact_id):
    """
    Logic AI edits a contact
    
    URL: api/logic/v1/contacts/edit/{contact_id}
    
    Body (send only what needs updating):
    {
        "name": "Sarah J. Smith",      # Optional
        "phone": "0798765432",          # Optional
        "email": "new@email.com",       # Optional
        "tag": "Family"                 # Optional
    }
    
    Response:
    {
        "success": true,
        "message": "Updated Sarah's phone"
    }
    """
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        # Validate contact_id
        if not contact_id:
            return jsonify({
                'success': False,
                'message': 'Contact ID is required'
            }), 400
        
        # Extract updates
        updates = {}
        if 'name' in data and data['name']:
            updates['name'] = data['name']
        if 'phone' in data and data['phone']:
            updates['phone'] = data['phone']
        if 'email' in data and data['email']:
            updates['email'] = data['email']
        if 'tag' in data and data['tag']:
            updates['tag'] = data['tag']
        
        if not updates:
            return jsonify({
                'success': False,
                'message': 'No fields to update'
            }), 400
        
        # Edit contact
        result = edit_contact(
            user_id=user_id,
            contact_id=contact_id,
            **updates
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"❌ Logic edit contact error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to update contact'
        }), 500