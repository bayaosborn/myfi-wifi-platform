"""
Contacts Import Routes - Phone Auth Compatible
Handles bulk contact insertion
"""

from flask import Blueprint, request, jsonify, session, redirect
from functools import wraps
from app.backend.supabase_client import supabase

cont_import_bp = Blueprint('cont_import', __name__)

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

# ==================== BULK IMPORT ROUTE ====================

@cont_import_bp.route('/api/contacts/bulk', methods=['POST'])
@login_required
def bulk_insert_contacts():
    """Bulk insert contacts from JSON array"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        # Validate input
        if not data or 'contacts' not in data:
            return jsonify({'success': False, 'error': 'No contacts provided'}), 400
        
        contacts_list = data.get('contacts', [])
        
        if not isinstance(contacts_list, list):
            return jsonify({'success': False, 'error': 'Contacts must be an array'}), 400
        
        if len(contacts_list) == 0:
            return jsonify({'success': False, 'error': 'Empty contacts array'}), 400
        
        print(f"📥 Bulk import started: {len(contacts_list)} contacts for user {user_id}")
        
        # Insert contacts one by one
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
                
                # Insert to Supabase (no access_token needed)
                result = supabase.insert('contacts', contact_data)
                
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
                'errors': errors[:10] if errors else []
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
        
        return jsonify({'success': False, 'error': str(e), 'inserted': 0}), 500