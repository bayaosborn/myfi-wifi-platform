"""
Contacts Import Routes - SIMPLIFIED & WORKING
Handles bulk contact insertion
"""

from flask import Blueprint, request, jsonify, session
from functools import wraps
from app.backend.supabase_client import supabase

cont_import_bp = Blueprint('cont_import', __name__)

# ==================== HELPER FUNCTIONS ====================

def login_required(f):
    """Decorator to protect routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_token' not in session or 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# ==================== BULK IMPORT ROUTE ====================

@cont_import_bp.route('/api/contacts/bulk', methods=['POST'])
@login_required
def bulk_insert_contacts():
    """
    Bulk insert contacts from JSON array
    Request body: { contacts: [{name, phone, email, tag, notes}, ...] }
    """
    try:
        user_id = session.get('user_id')
        access_token = session.get('access_token')
        data = request.get_json()
        
        # Validate input
        if not data or 'contacts' not in data:
            return jsonify({
                'success': False,
                'error': 'No contacts provided'
            }), 400
        
        contacts_list = data.get('contacts', [])
        
        if not isinstance(contacts_list, list):
            return jsonify({
                'success': False,
                'error': 'Contacts must be an array'
            }), 400
        
        if len(contacts_list) == 0:
            return jsonify({
                'success': False,
                'error': 'Empty contacts array'
            }), 400
        
        print(f"📥 Bulk import started: {len(contacts_list)} contacts for user {user_id}")
        
        # Insert contacts one by one (simple & reliable)
        inserted_count = 0
        failed_count = 0
        errors = []
        
        for idx, contact in enumerate(contacts_list):
            try:
                # Validate contact has name
                name = contact.get('name', '').strip()
                if not name:
                    failed_count += 1
                    errors.append(f"Contact {idx}: No name")
                    continue
                
                # Prepare contact data
                contact_data = {
                    'user_id': user_id,
                    'name': name,
                    'phone': contact.get('phone', '').strip(),
                    'email': contact.get('email', '').strip(),
                    'tag': contact.get('tag', 'General').strip() or 'General',
                    'notes': contact.get('notes', '').strip()
                }
                
                # Insert to Supabase
                result = supabase.insert('contacts', contact_data, access_token=access_token)
                
                if result.get('success'):
                    inserted_count += 1
                    if inserted_count % 100 == 0:
                        print(f"  ✓ Inserted {inserted_count} contacts...")
                else:
                    failed_count += 1
                    error_msg = result.get('error', 'Unknown error')
                    errors.append(f"Contact {idx} ({name}): {error_msg}")
                    print(f"  ✗ Failed: {name} - {error_msg}")
                
            except Exception as e:
                failed_count += 1
                errors.append(f"Contact {idx}: {str(e)}")
                print(f"  ✗ Exception for contact {idx}: {str(e)}")
        
        print(f"📊 Bulk import complete: {inserted_count} success, {failed_count} failed")
        
        # Return response
        if inserted_count > 0:
            return jsonify({
                'success': True,
                'count': inserted_count,
                'inserted': inserted_count,
                'failed': failed_count,
                'message': f'Successfully uploaded {inserted_count} contacts' + 
                          (f' ({failed_count} failed)' if failed_count > 0 else ''),
                'errors': errors[:10] if errors else []  # First 10 errors only
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No contacts were inserted',
                'inserted': 0,
                'failed': failed_count,
                'errors': errors[:10] if errors else []
            }), 400
        
    except Exception as e:
        print(f"❌ Bulk import error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e),
            'inserted': 0
        }), 500

# ==================== FILE UPLOAD ROUTE (OPTIONAL) ====================

@cont_import_bp.route('/api/contacts/upload', methods=['POST'])
@login_required
def upload_contacts_file():
    """
    Handle CSV/VCF file upload via multipart form
    This is for direct file uploads (not used by your current JS)
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    try:
        user_id = session.get('user_id')
        access_token = session.get('access_token')
        
        # Read file
        file_content = file.read().decode('utf-8')
        file_type = 'csv' if file.filename.lower().endswith('.csv') else 'vcf'
        
        # Parse based on type
        contacts_list = []
        
        if file_type == 'csv':
            import csv
            import io
            
            csv_reader = csv.DictReader(io.StringIO(file_content))
            for row in csv_reader:
                name = (row.get('name') or row.get('Name') or '').strip()
                if name:
                    contacts_list.append({
                        'user_id': user_id,
                        'name': name,
                        'phone': (row.get('phone') or row.get('Phone') or '').strip(),
                        'email': (row.get('email') or row.get('Email') or '').strip(),
                        'tag': (row.get('tag') or row.get('Tag') or 'General').strip(),
                        'notes': (row.get('notes') or row.get('Notes') or '').strip()
                    })
        
        elif file_type == 'vcf':
            # Simple VCF parsing
            current_contact = {}
            
            for line in file_content.split('\n'):
                line = line.strip()
                
                if line.startswith('BEGIN:VCARD'):
                    current_contact = {'user_id': user_id, 'tag': 'General'}
                
                elif line.startswith('FN:'):
                    current_contact['name'] = line[3:].strip()
                
                elif line.startswith('TEL'):
                    current_contact['phone'] = line.split(':')[-1].strip()
                
                elif line.startswith('EMAIL'):
                    current_contact['email'] = line.split(':')[-1].strip()
                
                elif line.startswith('END:VCARD'):
                    if current_contact.get('name'):
                        current_contact.setdefault('phone', '')
                        current_contact.setdefault('email', '')
                        current_contact.setdefault('notes', '')
                        contacts_list.append(current_contact)
                    current_contact = {}
        
        # Insert contacts
        if not contacts_list:
            return jsonify({'success': False, 'error': 'No valid contacts found'}), 400
        
        inserted_count = 0
        for contact in contacts_list:
            result = supabase.insert('contacts', contact, access_token=access_token)
            if result.get('success'):
                inserted_count += 1
        
        return jsonify({
            'success': True,
            'count': inserted_count,
            'message': f'Uploaded {inserted_count} contacts'
        }), 200
        
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500