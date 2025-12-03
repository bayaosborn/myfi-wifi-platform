from flask import Blueprint, request, jsonify
import sys
import os

# Add parent directory to path to import database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import (
    create_contact, 
    get_contact_by_id,
    get_all_contacts,  # Add this
    update_contact     # Add this
)

addCustomContact_bp = Blueprint('addCustomContact', __name__)


@addCustomContact_bp.route('/api/add-contact', methods=['POST'])
def add_custom_contact():
    """Add a single custom contact"""
    try:
        data = request.get_json()
        
        # Validate required field
        if not data or not data.get('name'):
            return jsonify({
                'success': False,
                'error': 'Name is required'
            }), 400
        
        # Extract and clean data
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        tag = data.get('tag', 'General').strip()
        notes = data.get('notes', '').strip()
        
        # Validate tag
        allowed_tags = ['Family', 'Work', 'Friends', 'Relationship', 'General']
        if tag not in allowed_tags:
            tag = 'General'
        
        # Insert into database
        contact_id = create_contact(
            name=name,
            phone=phone,
            email=email,
            tag=tag,
            notes=notes
        )
        
        # Fetch the created contact
        contact = get_contact_by_id(contact_id)
        
        return jsonify({
            'success': True,
            'message': f'Contact "{name}" added successfully',
            'contact_id': contact_id,
            'contact': contact
        }), 201
        
    except Exception as e:
        print(f"Error adding contact: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ADD THIS NEW ROUTE
@addCustomContact_bp.route('/api/contacts', methods=['GET'])
def api_get_contacts():
    """Get all contacts with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 1000, type=int)
    
    try:
        result = get_all_contacts(page, per_page)
        return jsonify(result)
    except Exception as e:
        print(f"Error fetching contacts: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'contacts': [],
            'total': 0
        }), 500


# ADD THIS ROUTE FOR UPDATING TAGS
@addCustomContact_bp.route('/api/contacts/<int:contact_id>/tag', methods=['PATCH'])
def update_contact_tag(contact_id):
    """Update contact tag"""
    try:
        data = request.get_json()
        new_tag = data.get('tag')
        
        if not new_tag:
            return jsonify({'success': False, 'error': 'Tag required'}), 400
        
        success = update_contact(contact_id, tag=new_tag)
        
        if success:
            return jsonify({'success': True, 'message': 'Tag updated'})
        else:
            return jsonify({'success': False, 'error': 'Update failed'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 50088




@addCustomContact_bp.route('/api/contacts/bulk', methods=['POST'])
def bulk_upload_contacts():
    """Bulk upload from VCF/CSV"""
    try:
        data = request.get_json()
        contacts_list = data.get('contacts', [])
        
        if not contacts_list:
            return jsonify({'success': False, 'error': 'No contacts provided'}), 400
        
        from backend.database import bulk_insert_contacts
        
        inserted = bulk_insert_contacts(contacts_list)
        
        return jsonify({
            'success': True,
            'count': inserted
        })
        
    except Exception as e:
        print(f"Bulk upload error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500













# PUT /api/contacts/<id> - Update contact
@addCustomContact_bp.route('/api/contacts/<int:contact_id>', methods=['PUT'])
def api_update_contact(contact_id):
    """Update a contact"""
    data = request.get_json()
    
    from backend.database import update_contact
    success = update_contact(contact_id, **data)
    
    if success:
        return jsonify({'success': True, 'message': 'Contact updated'})
    else:
        return jsonify({'success': False, 'error': 'Update failed'}), 400

# DELETE /api/contacts/<id> - Delete contact
@addCustomContact_bp.route('/api/contacts/<int:contact_id>', methods=['DELETE'])
def api_delete_contact(contact_id):
    """Delete a contact"""
    from backend.database import delete_contact
    success = delete_contact(contact_id)
    
    if success:
        return jsonify({'success': True, 'message': 'Contact deleted'})
    else:
        return jsonify({'success': False, 'error': 'Delete failed'}), 404




@addCustomContact_bp.route('/delete_all_contacts', methods=['POST'])
def delete_all_contacts_route():
    """Delete ALL contacts from database"""
    from backend.database import get_db_connection
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM contacts")
        conn.commit()

        deleted = cursor.rowcount  # Number of rows removed
        conn.close()

        return jsonify({
            "success": True,
            "deleted_count": deleted
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500