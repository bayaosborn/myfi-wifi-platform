"""
Contacts Merge Routes - Phone Auth Compatible
Find and merge duplicate contacts based on phone number
"""

from flask import Blueprint, request, jsonify, session, redirect
from functools import wraps
from app.backend.supabase_client import supabase

cont_merge_bp = Blueprint('cont_merge', __name__)

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

# ==================== DUPLICATE DETECTION ====================

@cont_merge_bp.route('/api/contacts/find-duplicates', methods=['GET'])
@login_required
def find_duplicate_contacts():
    """Find contacts with duplicate phone numbers"""
    try:
        user_id = session.get('user_id')
        
        print(f"🔍 Finding duplicates for user {user_id}")
        
        # Get all user's contacts with phone numbers
        contacts = supabase.select('contacts', filters={'user_id': user_id})
        
        if not contacts:
            return jsonify({
                'success': True,
                'duplicate_groups': 0,
                'total_duplicate_contacts': 0
            }), 200
        
        # Group by phone number
        phone_count = {}
        for contact in contacts:
            phone = contact.get('phone', '').strip()
            if phone:
                phone_count[phone] = phone_count.get(phone, 0) + 1
        
        # Find phones that appear more than once
        duplicate_phones = {phone: count for phone, count in phone_count.items() if count > 1}
        
        # Calculate totals
        duplicate_groups = len(duplicate_phones)
        total_duplicate_contacts = sum(count - 1 for count in duplicate_phones.values())
        
        print(f"  ✓ Found {duplicate_groups} duplicate groups")
        print(f"  ✓ Total duplicate contacts: {total_duplicate_contacts}")
        
        return jsonify({
            'success': True,
            'duplicate_groups': duplicate_groups,
            'total_duplicate_contacts': total_duplicate_contacts
        }), 200
        
    except Exception as e:
        print(f"❌ Find duplicates error: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e),
            'duplicate_groups': 0,
            'total_duplicate_contacts': 0
        }), 500

# ==================== DUPLICATE MERGING ====================

@cont_merge_bp.route('/api/contacts/merge-duplicates', methods=['POST'])
@login_required
def merge_duplicate_contacts():
    """Merge contacts with same phone number"""
    try:
        user_id = session.get('user_id')
        
        print(f"🔀 Merging duplicates for user {user_id}")
        
        # Get all user's contacts
        contacts = supabase.select('contacts', filters={'user_id': user_id})
        
        if not contacts:
            return jsonify({
                'success': True,
                'merged_groups': 0,
                'deleted_contacts': 0,
                'message': 'No contacts found'
            }), 200
        
        # Group contacts by phone number
        phone_groups = {}
        for contact in contacts:
            phone = contact.get('phone', '').strip()
            if phone:
                if phone not in phone_groups:
                    phone_groups[phone] = []
                phone_groups[phone].append(contact)
        
        # Find phones with duplicates
        duplicate_phones = [phone for phone, group in phone_groups.items() if len(group) > 1]
        
        if not duplicate_phones:
            return jsonify({
                'success': True,
                'merged_groups': 0,
                'deleted_contacts': 0,
                'message': 'No duplicates found'
            }), 200
        
        merged_count = 0
        deleted_count = 0
        
        # Process each duplicate group
        for phone in duplicate_phones:
            contacts_list = phone_groups[phone]
            
            if len(contacts_list) < 2:
                continue
            
            print(f"  📞 Merging {len(contacts_list)} contacts with phone: {phone}")
            
            # Calculate completeness score
            def completeness_score(contact):
                score = 0
                if contact.get('name'): score += 1
                if contact.get('email'): score += 1
                if contact.get('notes'): score += 1
                if contact.get('tag'): score += 1
                return score
            
            # Sort by completeness and created_at
            sorted_contacts = sorted(
                contacts_list,
                key=lambda c: (completeness_score(c), c.get("created_at", "")),
                reverse=True
            )
            
            keeper = sorted_contacts[0]
            duplicates_to_delete = sorted_contacts[1:]
            
            print(f"    ✓ Keeper: {keeper.get('name')} (ID: {keeper.get('id')})")
            print(f"    ✗ Deleting {len(duplicates_to_delete)} duplicates")
            
            # Combine all notes
            all_notes = []
            for contact in contacts_list:
                if contact.get('notes'):
                    all_notes.append(contact['notes'])
            
            combined_notes = " | ".join(all_notes) if all_notes else keeper.get('notes', '')
            
            # Update keeper with combined notes
            if combined_notes != keeper.get('notes'):
                print(f"    📝 Updating notes for keeper")
                supabase.update('contacts', {'id': keeper['id'], 'user_id': user_id}, {'notes': combined_notes})
            
            # Delete duplicates
            for dup in duplicates_to_delete:
                success = supabase.delete('contacts', {'id': dup['id'], 'user_id': user_id})
                if success:
                    deleted_count += 1
                    print(f"      ✗ Deleted: {dup.get('name')} (ID: {dup.get('id')})")
            
            merged_count += 1
        
        print(f"✅ Merge complete: {merged_count} groups merged, {deleted_count} contacts deleted")
        
        return jsonify({
            'success': True,
            'merged_groups': merged_count,
            'deleted_contacts': deleted_count,
            'message': f'Merged {merged_count} groups, deleted {deleted_count} duplicate contacts'
        }), 200
        
    except Exception as e:
        print(f"❌ Merge duplicates error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500