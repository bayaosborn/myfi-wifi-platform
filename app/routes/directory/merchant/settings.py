"""
Merchant Settings Routes
app/routes/merchant_settings.py

Settings page and update functionality
"""

from flask import Blueprint, request, jsonify, render_template, session, redirect
from app.backend.supabase_client import supabase

merchant_settings_bp = Blueprint('merchant_settings', __name__, url_prefix='/directory/merchant')


@merchant_settings_bp.route('/settings')
def settings_page():
    """Merchant settings page"""
    user_id = session.get('user_id')

    if not user_id:
        return redirect('/auth/login')

    try:
        merchant = supabase.select(
            'merchants',
            filters={'profile_user_id': user_id}
        )

        if not merchant:
            return redirect('/directory/merchant/onboard')

        return render_template(
            'directory/merchant/settings.html',
            merchant=merchant[0]
        )

    except Exception as e:
        print(f"❌ Settings page error: {e}")
        return "Error loading settings", 500


@merchant_settings_bp.route('/update-settings', methods=['POST'])
def update_settings():
    """Update merchant settings"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        # Get merchant
        merchant = supabase.select('merchants', filters={'profile_user_id': user_id})
        
        if not merchant:
            return jsonify({'success': False, 'error': 'Merchant not found'}), 404
        
        merchant_id = merchant[0]['id']
        data = request.get_json()
        
        updates = {}
        
        # Business details
        if 'business_name' in data:
            updates['business_name'] = data['business_name']
        if 'owner_name' in data:
            updates['owner_name'] = data['owner_name']
        if 'description' in data:
            updates['description'] = data['description']
        if 'tags' in data:
            updates['tags'] = data['tags']  # Array of tags
        
        # Contact info
        if 'phone' in data:
            updates['contact_phone'] = data['phone']
        if 'email' in data:
            updates['contact_email'] = data['email']
        if 'location' in data:
            updates['location'] = data['location']
        
        # Operating hours
        if 'opening_time' in data:
            updates['opening_time'] = data['opening_time']
        if 'closing_time' in data:
            updates['closing_time'] = data['closing_time']
        
        # Payment methods
        if 'mpesa_till' in data:
            updates['mpesa_till'] = data['mpesa_till']
        if 'mpesa_paybill' in data:
            updates['mpesa_paybill'] = data['mpesa_paybill']
        if 'mpesa_account' in data:
            updates['mpesa_account'] = data['mpesa_account']
        
        if not updates:
            return jsonify({'success': False, 'error': 'No valid updates'}), 400
        
        # Update merchant
        success = supabase.update('merchants', {'id': merchant_id}, updates)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Settings updated successfully'
            }), 200
        else:
            return jsonify({'success': False, 'error': 'Update failed'}), 400
        
    except Exception as e:
        print(f"❌ Update settings error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500