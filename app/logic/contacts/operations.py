"""
Contact Operations for Logic AI
Business logic for adding/editing contacts

Location: app/logic/contacts/operations.py
"""

from app.backend.supabase_client import supabase
from typing import Optional, Dict, Any
import re


def add_contact(
    user_id: str,
    name: str,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    tag: str = "General"
) -> Dict[str, Any]:
    """
    Add a new contact via Logic AI
    
    Args:
        user_id: User's UUID
        name: Contact name (required)
        phone: Phone number (optional)
        email: Email address (optional)
        tag: Contact category (default: General)
    
    Returns:
        {
            'success': bool,
            'contact_id': str,
            'message': str
        }
    """
    try:
        # Need at least phone OR email
        if not phone and not email:
            return {
                'success': False,
                'message': f'Need phone or email for {name}'
            }
        
        # Clean phone (remove spaces, commas, etc.)
        if phone:
            phone = clean_phone_number(phone)
        
        # Check if contact already exists
        existing = supabase.select(
            'contacts',
            filters={
                'user_id': user_id,
                'name': name
            }
        )
        
        if existing:
            return {
                'success': False,
                'message': f'{name} already exists'
            }
        
        # Insert contact
        contact_data = {
            'user_id': user_id,
            'name': name.strip(),
            'phone': phone,
            'email': email.strip() if email else None,
            'tag': tag.strip(),
            'is_favorite': False,
            'is_emergency_contact': False
        }
        
        result = supabase.insert('contacts', contact_data)
        
        if result['success']:
            contact_id = result['data'][0]['id']
            return {
                'success': True,
                'contact_id': contact_id,
                'message': f'Added {name}'
            }
        else:
            return {
                'success': False,
                'message': 'Failed to add contact'
            }
        
    except Exception as e:
        print(f"❌ Add contact error: {e}")
        return {
            'success': False,
            'message': 'Something went wrong'
        }


def edit_contact(
    user_id: str,
    contact_id: str,
    **updates
) -> Dict[str, Any]:
    """
    Edit existing contact via Logic AI
    
    Args:
        user_id: User's UUID
        contact_id: Contact's UUID
        **updates: Fields to update (name, phone, email, tag)
    
    Returns:
        {
            'success': bool,
            'message': str
        }
    """
    try:
        # Verify contact exists and belongs to user
        contact = supabase.select(
            'contacts',
            filters={
                'id': contact_id,
                'user_id': user_id
            }
        )
        
        if not contact:
            return {
                'success': False,
                'message': 'Contact not found'
            }
        
        contact_name = contact[0]['name']
        
        # Prepare allowed updates
        allowed_fields = ['name', 'phone', 'email', 'tag']
        update_data = {}
        
        for key, value in updates.items():
            if key in allowed_fields and value:
                # Clean phone if updating
                if key == 'phone':
                    update_data[key] = clean_phone_number(value)
                else:
                    update_data[key] = value.strip()
        
        if not update_data:
            return {
                'success': False,
                'message': 'No fields to update'
            }
        
        # Update in database
        # FIXED: Correct argument order for supabase.update(table, filters, data)
        success = supabase.update(
            'contacts',                           # table
            {'id': contact_id},                   # filters
            update_data                           # data
        )
        
        if success:
            # Build message based on what was updated
            updated_fields = list(update_data.keys())
            if len(updated_fields) == 1:
                field = updated_fields[0]
                return {
                    'success': True,
                    'message': f"Updated {contact_name}'s {field}"
                }
            else:
                return {
                    'success': True,
                    'message': f"Updated {contact_name}"
                }
        else:
            return {
                'success': False,
                'message': 'Update failed'
            }
        
    except Exception as e:
        print(f"❌ Edit contact error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'message': 'Something went wrong'
        }


def clean_phone_number(phone: str) -> str:
    """
    Clean phone number - remove unwanted characters
    Does NOT force country code
    
    Examples:
        "07,12-345,678" -> "0712345678"
        "+1 (555) 123-4567" -> "+15551234567"
        "0712 345 678" -> "0712345678"
    """
    # Remove spaces, commas, parentheses, hyphens
    cleaned = re.sub(r'[\s,\(\)\-]', '', phone)
    
    # Keep only digits and leading +
    cleaned = re.sub(r'[^\d+]', '', cleaned)
    
    # Ensure + only at start
    if '+' in cleaned:
        parts = cleaned.split('+')
        cleaned = '+' + ''.join(parts)
    
    return cleaned