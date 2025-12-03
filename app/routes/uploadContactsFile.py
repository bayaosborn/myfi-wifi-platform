from flask import Blueprint, request, jsonify, session
#from supabase import create_client
import os
import io
import csv

# Direct imports - logic is now a proper package under app/
#from app.logic.engine import LogicEngine
#from app.logic.security import SecurityFilter
#from app.logic.q_engine import QueryQuotient

uploadContactsFile_bp = Blueprint('uploadContactsFile', __name__)





@uploadContactsFile_bp.route('/upload', methods=['POST'])
def upload_contacts():
    """Handle CSV/VCF file upload and save to database"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    try:
        # Read file content
        file_content = file.read().decode('utf-8')
        file_type = 'csv' if file.filename.endswith('.csv') else 'vcf'
        
        contacts_list = []
        
        if file_type == 'csv':
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(file_content))
            
            for row in csv_reader:
                contact = {
                    'name': row.get('name', row.get('Name', '')).strip(),
                    'phone': row.get('phone', row.get('Phone', row.get('phone number', ''))).strip(),
                    'email': row.get('email', row.get('Email', '')).strip(),
                    'tag': row.get('tag', row.get('Tag', row.get('category', 'General'))).strip(),
                    'notes': row.get('notes', row.get('Notes', '')).strip()
                }
                
                # Only add if has a name
                if contact['name']:
                    contacts_list.append(contact)
        
        # TODO: Add VCF parsing later if needed
        
        # Insert contacts into database
        inserted_count = bulk_insert_contacts(contacts_list)
        
        return jsonify({
            'success': True,
            'count': inserted_count,
            'message': f'Successfully uploaded {inserted_count} contacts'
        })
        
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@uploadContactsFile_bp.route('/api/contacts', methods=['GET'])
def api_get_contacts():
    """Get all contacts with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 13, type=int)
    
    result = get_all_contacts(page, per_page)
    return jsonify(result)


@uploadContactsFile_bp.route('/api/contacts/<int:contact_id>', methods=['GET'])
def api_get_contact(contact_id):
    """Get a single contact"""
    contact = get_contact_by_id(contact_id)
    
    if contact:
        return jsonify({'success': True, 'contact': contact})
    else:
        return jsonify({'success': False, 'error': 'Contact not found'}), 404


@uploadContactsFile_bp.route('/api/contacts', methods=['POST'])
def api_create_contact():
    """Create a new contact"""
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'success': False, 'error': 'Name is required'}), 400
    
    contact_id = create_contact(
        name=data.get('name'),
        phone=data.get('phone', ''),
        email=data.get('email', ''),
        tag=data.get('tag', 'General'),
        notes=data.get('notes', '')
    )
    
    return jsonify({'success': True, 'contact_id': contact_id})


@uploadContactsFile_bp.route('/api/contacts/<int:contact_id>', methods=['PUT'])
def api_update_contact(contact_id):
    """Update a contact"""
    data = request.get_json()
    
    success = update_contact(contact_id, **data)
    
    if success:
        return jsonify({'success': True, 'message': 'Contact updated'})
    else:
        return jsonify({'success': False, 'error': 'Update failed'}), 400


@uploadContactsFile_bp.route('/api/contacts/<int:contact_id>', methods=['DELETE'])
def api_delete_contact(contact_id):
    """Delete a contact"""
    success = delete_contact(contact_id)
    
    if success:
        return jsonify({'success': True, 'message': 'Contact deleted'})
    else:
        return jsonify({'success': False, 'error': 'Delete failed'}), 404


@uploadContactsFile_bp.route('/api/contacts/search', methods=['GET'])
def api_search_contacts():
    """Search contacts"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'success': False, 'error': 'Search query required'}), 400
    
    contacts = search_contacts(query)
    return jsonify({'success': True, 'contacts': contacts, 'count': len(contacts)})


@uploadContactsFile_bp.route('/api/contacts/tag/<tag>', methods=['GET'])
def api_contacts_by_tag(tag):
    """Get contacts by tag"""
    contacts = get_contacts_by_tag(tag)
    return jsonify({'success': True, 'contacts': contacts, 'count': len(contacts)})