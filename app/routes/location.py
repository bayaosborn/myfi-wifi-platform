from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from functools import wraps
from datetime import datetime
from supabase import create_client
import os

location_bp = Blueprint('location', __name__)

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)


''''

def location_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
        
        # Check if user has any device with location permission
        try:
            response = supabase.table('devices').select('location_permission_granted').eq('user_id', user_id).eq('is_active', True).execute()
            
            if not response.data or not any(d.get('location_permission_granted') for d in response.data):
                return redirect(url_for('location.location_identity'))
            
            session['location_permission_granted'] = True
        except Exception as e:
            print(f"Error checking location permission: {e}")
            return redirect(url_for('location.location_identity'))
        
        return f(*args, **kwargs)
    return decorated_function

'''



@location_bp.route('/location-identity')
def location_identity():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
    
    # Check if they've already granted permission
    try:
        response = supabase.table('devices').select('location_permission_granted').eq('user_id', user_id).eq('is_active', True).execute()
        
        if response.data and any(d.get('location_permission_granted') for d in response.data):
            return redirect(url_for('account.my_account'))
    except Exception as e:
        print(f"Error checking existing permission: {e}")
    
    return render_template('location/location-identity.html')

@location_bp.route('/api/location/capture', methods=['POST'])
def capture_location():
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
        
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        accuracy = data.get('accuracy')
        device_type = data.get('device_type', 'unknown')
        os_type = data.get('os_type', 'unknown')
        device_fingerprint = data.get('device_fingerprint')
        
        if not latitude or not longitude or not device_fingerprint:
            return jsonify({'error': 'Location data and device fingerprint required'}), 400
        
        # Check if device already exists
        device_response = supabase.table('devices').select('id').eq('device_fingerprint', device_fingerprint).execute()
        
        if device_response.data:
            # Update existing device
            device_id = device_response.data[0]['id']
            
            supabase.table('devices').update({
                'last_seen_at': datetime.utcnow().isoformat(),
                'location_permission_granted': True,
                'is_active': True
            }).eq('id', device_id).execute()
            
        else:
            # Create new device
            device_record = {
                'device_fingerprint': device_fingerprint,
                'user_id': user_id,
                'first_seen_at': datetime.utcnow().isoformat(),
                'last_seen_at': datetime.utcnow().isoformat(),
                'location_permission_granted': True,
                'device_type': device_type,
                'os_type': os_type,
                'is_active': True
            }
            
            device_response = supabase.table('devices').insert(device_record).execute()
            device_id = device_response.data[0]['id']
        
        # Insert location record
        location_record = {
            'device_id': device_id,
            'user_id': user_id,
            'latitude': float(latitude),
            'longitude': float(longitude),
            'accuracy_meters': float(accuracy) if accuracy else None,
            'captured_at': datetime.utcnow().isoformat(),
            'capture_trigger': 'signup',
            'location_type': 'signup',
            'device_type': device_type,
            'os_type': os_type,
            'is_primary_location': False
        }
        
        supabase.table('device_locations').insert(location_record).execute()
        
        # Update session
        session['location_permission_granted'] = True
        session['device_fingerprint'] = device_fingerprint
        session['device_id'] = device_id
        
        return jsonify({
            'success': True,
            'message': 'Location captured successfully',
            'redirect_to': '/notifications-setup' 
            
        }), 200
        
    except Exception as e:
        print(f"Error capturing location: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@location_bp.route('/api/location/update', methods=['POST'])
def update_location():
    """Capture location on app open"""
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        device_id = session.get('device_id')
        
        if not user_id or not device_id:
            return jsonify({'error': 'Unauthorized'}), 401
        
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        accuracy = data.get('accuracy')
        
        if not latitude or not longitude:
            return jsonify({'error': 'Location data required'}), 400
        
        # Insert location record
        location_record = {
            'device_id': device_id,
            'user_id': user_id,
            'latitude': float(latitude),
            'longitude': float(longitude),
            'accuracy_meters': float(accuracy) if accuracy else None,
            'captured_at': datetime.utcnow().isoformat(),
            'capture_trigger': 'app_open',
            'location_type': 'recurring',
            'is_primary_location': False
        }
        
        supabase.table('device_locations').insert(location_record).execute()
        
        # Update device last_seen
        supabase.table('devices').update({
            'last_seen_at': datetime.utcnow().isoformat()
        }).eq('id', device_id).execute()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"Error updating location: {e}")
        return jsonify({'error': 'Internal server error'}), 500