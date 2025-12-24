"""
Authentication Routes for MyFi - Phone + PIN (SIMPLIFIED)
"""

from flask import Blueprint, request, jsonify, session, redirect, render_template
from functools import wraps
from datetime import datetime, timedelta
import secrets
import uuid

# Import your supabase client and phone utils
from app.backend.supabase_client import supabase
from app.backend.phone_utils import normalize_phone, hash_pin, verify_pin

# Create Blueprint
auth_bp = Blueprint('auth', __name__)

# Constants
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

# ==================== DECORATORS ====================

def login_required(f):
    """Decorator to protect routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# ==================== HELPER FUNCTIONS ====================

def check_account_locked(user):
    """Check if account is locked"""
    if not user.get('locked_until'):
        return False, 0
    
    locked_time = datetime.fromisoformat(user['locked_until'].replace('Z', '+00:00'))
    if datetime.now(locked_time.tzinfo) < locked_time:
        remaining = (locked_time - datetime.now(locked_time.tzinfo)).seconds // 60
        return True, remaining
    
    # Lock expired
    supabase.update('profiles', {'id': user['id']}, {
        'locked_until': None,
        'failed_login_attempts': 0
    })
    return False, 0

def record_failed_attempt(user_id):
    """Record failed login attempt"""
    users = supabase.select('profiles', filters={'id': user_id})
    if not users:
        return
    
    attempts = users[0].get('failed_login_attempts', 0) + 1
    update_data = {'failed_login_attempts': attempts}
    
    if attempts >= MAX_LOGIN_ATTEMPTS:
        lockout_time = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        update_data['locked_until'] = lockout_time.isoformat()
    
    supabase.update('profiles', {'id': user_id}, update_data)

# ==================== API ROUTES ====================

@auth_bp.route('/api/auth/signup', methods=['POST'])
def signup():
    """Create new account with phone + PIN"""
    try:
        data = request.get_json()
        
        phone_input = data.get('phone_number', '').strip()
        pin = data.get('pin', '').strip()
        confirm_pin = data.get('confirm_pin', '').strip()
        full_name = data.get('full_name', '').strip()
        
        print(f"\n{'='*60}")
        print(f"🔍 SIGNUP ATTEMPT")
        print(f"{'='*60}")
        print(f"📱 Raw phone input: '{phone_input}'")
        print(f"👤 Full name: '{full_name}'")
        
        # Validate
        if not phone_input or not pin:
            print("❌ Missing required fields")
            return jsonify({'error': 'Phone number and PIN are required'}), 400
        
        if pin != confirm_pin:
            print("❌ PINs don't match")
            return jsonify({'error': 'PINs do not match'}), 400
        
        if not pin.isdigit() or len(pin) not in [4, 6]:
            print(f"❌ Invalid PIN format: {len(pin)} digits")
            return jsonify({'error': 'PIN must be 4 or 6 digits'}), 400
        
        # Normalize phone
        normalized_phone = normalize_phone(phone_input)
        print(f"✅ Normalized phone: '{normalized_phone}'")
        
        if not normalized_phone:
            print("❌ Phone normalization failed")
            return jsonify({'error': 'Invalid phone number format'}), 400
        
        # Check if exists
        print(f"🔍 Checking if phone exists...")
        existing = supabase.select('profiles', filters={'phone_number': normalized_phone})
        if existing:
            print(f"❌ Phone already registered: {len(existing)} users found")
            return jsonify({'error': 'Phone number already registered'}), 400
        print("✅ Phone number is available")
        
        # Hash PIN
        print("🔐 Hashing PIN...")
        pin_hash_value = hash_pin(pin)
        print(f"✅ PIN hashed: {pin_hash_value[:20]}...")
        
        # Create user
        user_id = str(uuid.uuid4())
        print(f"🆔 Generated user ID: {user_id}")
        
        user_data = {
            'id': user_id,
            'phone_number': normalized_phone,  # Stored as: 254759335278 (NO plus)
            'country_code': '254',  # Just the code, no plus
            'pin_hash': pin_hash_value,
            'full_name': full_name if full_name else None,
            'phone_verified': False,
            'failed_login_attempts': 0,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        print("📤 Inserting user into database...")
        result = supabase.insert('profiles', user_data)
        
        if result['success'] and result['data']:
            user = result['data'][0]
            print(f"✅ User created successfully!")
            print(f"📱 Stored phone: '{user['phone_number']}'")
            
            # Create session
            session['user_id'] = user['id']
            session['phone_number'] = normalized_phone
            session.permanent = True
            
            print(f"✅ Session created")
            print(f"{'='*60}\n")
            
            return jsonify({
                'success': True,
                'message': 'Account created successfully',
                'user': {
                    'id': user['id'],
                    'phone_number': normalized_phone,
                    'full_name': full_name
                }
            }), 201
        else:
            error_msg = result.get('error', 'Failed to create account')
            print(f"❌ Database insert failed: {error_msg}")
            print(f"{'='*60}\n")
            return jsonify({'error': error_msg}), 500
            
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ CRITICAL SIGNUP ERROR")
        print(f"{'='*60}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        return jsonify({'error': 'An error occurred during signup'}), 500

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """Login with phone + PIN"""
    try:
        data = request.get_json()
        
        phone_input = data.get('phone_number', '').strip()
        pin = data.get('pin', '').strip()
        
        print(f"\n{'='*60}")
        print(f"🔍 LOGIN ATTEMPT")
        print(f"{'='*60}")
        print(f"📱 Raw phone input: '{phone_input}'")
        print(f"🔢 PIN length: {len(pin)}")
        
        if not phone_input or not pin:
            print("❌ Missing phone or PIN")
            return jsonify({'error': 'Phone number and PIN are required'}), 400
        
        # Normalize phone
        normalized_phone = normalize_phone(phone_input)
        print(f"✅ Normalized phone: '{normalized_phone}'")
        
        if not normalized_phone:
            print("❌ Phone normalization failed")
            return jsonify({'error': 'Invalid phone number format'}), 400
        
        # Find user
        print(f"🔍 Searching database for: '{normalized_phone}'")
        users = supabase.select('profiles', filters={'phone_number': normalized_phone})
        print(f"📊 Found {len(users)} matching users")
        
        if not users:
            # Debug: Show what's in database
            all_users = supabase.select('profiles')
            print(f"📊 Total users in database: {len(all_users)}")
            if all_users:
                sample_phones = [u.get('phone_number', 'NO_PHONE') for u in all_users[:5]]
                print(f"📱 Sample phone numbers in DB: {sample_phones}")
            print("❌ No matching user found")
            return jsonify({'success': False, 'error': 'Account not found'}), 401
        
        user = users[0]
        print(f"✅ Found user ID: {user['id']}")
        print(f"📱 User phone in DB: '{user['phone_number']}'")
        
        # Check if locked
        is_locked, remaining_mins = check_account_locked(user)
        if is_locked:
            print(f"🔒 Account is locked for {remaining_mins} minutes")
            return jsonify({
                'success': False,
                'error': f'Account locked. Try again in {remaining_mins} minutes'
            }), 403
        
        # Verify PIN
        print(f"🔐 Verifying PIN...")
        pin_hash = user.get('pin_hash')
        if not pin_hash:
            print("❌ No PIN hash found for user")
            return jsonify({'success': False, 'error': 'Account setup incomplete'}), 500
        
        if not verify_pin(pin, pin_hash):
            print("❌ PIN verification FAILED")
            record_failed_attempt(user['id'])
            return jsonify({'success': False, 'error': 'Invalid PIN'}), 401
        
        print("✅ PIN verification SUCCESS")
        
        # Success - reset attempts
        supabase.update('profiles', {'id': user['id']}, {
            'failed_login_attempts': 0,
            'locked_until': None,
            'last_login_at': datetime.utcnow().isoformat()
        })
        
        # Create session
        session['user_id'] = user['id']
        session['phone_number'] = normalized_phone
        session.permanent = True
        
        print(f"✅ Session created for user: {user['id']}")
        print(f"{'='*60}\n")
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'phone_number': normalized_phone,
                'full_name': user.get('full_name')
            }
        }), 200
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ CRITICAL LOGIN ERROR")
        print(f"{'='*60}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        return jsonify({'success': False, 'error': 'Server error occurred'}), 500

@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    """Clear session"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200

@auth_bp.route('/api/auth/user', methods=['GET'])
@login_required
def get_user():
    """Get current user"""
    try:
        users = supabase.select('profiles', filters={'id': session['user_id']})
        if not users:
            return jsonify({'error': 'User not found'}), 404
        
        user = users[0]
        return jsonify({
            'id': user['id'],
            'phone_number': user['phone_number'],
            'full_name': user.get('full_name'),
            'phone_verified': user.get('phone_verified', False),
            'created_at': user.get('created_at')
        }), 200
        
    except Exception as e:
        print(f"Get user error: {e}")
        return jsonify({'error': 'Failed to fetch user data'}), 500

@auth_bp.route('/api/auth/forgot-pin', methods=['POST'])
def forgot_pin():
    """Request PIN reset"""
    try:
        data = request.get_json()
        phone_input = data.get('phone_number', '').strip()
        
        if not phone_input:
            return jsonify({'error': 'Phone number is required'}), 400
        
        normalized_phone = normalize_phone(phone_input)
        if not normalized_phone:
            return jsonify({'error': 'Invalid phone number format'}), 400
        
        # Find user
        users = supabase.select('profiles', filters={'phone_number': normalized_phone})
        if not users:
            # Don't reveal if account exists
            return jsonify({
                'success': True,
                'message': 'If this phone is registered, you will receive a reset code'
            }), 200
        
        user = users[0]
        
        # Generate token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Save token
        supabase.insert('pin_reset_tokens', {
            'id': str(uuid.uuid4()),
            'user_id': user['id'],
            'token': token,
            'expires_at': expires_at.isoformat(),
            'used': False,
            'created_at': datetime.utcnow().isoformat()
        })
        
        # DEV ONLY - return token
        return jsonify({
            'success': True,
            'message': 'Reset code sent',
            'token': token  # REMOVE IN PRODUCTION
        }), 200
        
    except Exception as e:
        print(f"Forgot PIN error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'An error occurred'}), 500

@auth_bp.route('/api/auth/reset-pin', methods=['POST'])
def reset_pin():
    """Reset PIN with token"""
    try:
        data = request.get_json()
        
        token = data.get('token', '').strip()
        new_pin = data.get('new_pin', '').strip()
        confirm_pin = data.get('confirm_pin', '').strip()
        
        if not token or not new_pin:
            return jsonify({'error': 'Token and new PIN are required'}), 400
        
        if new_pin != confirm_pin:
            return jsonify({'error': 'PINs do not match'}), 400
        
        if not new_pin.isdigit() or len(new_pin) not in [4, 6]:
            return jsonify({'error': 'PIN must be 4 or 6 digits'}), 400
        
        # Find token
        tokens = supabase.select('pin_reset_tokens', filters={'token': token})
        if not tokens:
            return jsonify({'error': 'Invalid or expired reset code'}), 400
        
        reset_token = tokens[0]
        
        # Check if used
        if reset_token['used']:
            return jsonify({'error': 'Reset code already used'}), 400
        
        # Check expiry
        expires_at = datetime.fromisoformat(reset_token['expires_at'].replace('Z', '+00:00'))
        if datetime.now(expires_at.tzinfo) > expires_at:
            return jsonify({'error': 'Reset code expired'}), 400
        
        # Hash new PIN
        pin_hash_value = hash_pin(new_pin)
        
        # Update user
        supabase.update('profiles', {'id': reset_token['user_id']}, {
            'pin_hash': pin_hash_value,
            'failed_login_attempts': 0,
            'locked_until': None
        })
        
        # Mark token as used
        supabase.update('pin_reset_tokens', {'id': reset_token['id']}, {'used': True})
        
        return jsonify({
            'success': True,
            'message': 'PIN reset successfully'
        }), 200
        
    except Exception as e:
        print(f"Reset PIN error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'An error occurred'}), 500

# ==================== HTML ROUTES ====================

@auth_bp.route('/login')
def login_page():
    """Render login page"""
    if 'user_id' in session:
        return redirect('/')
    return render_template('auth/login_phone.html')

@auth_bp.route('/signup')
def signup_page():
    """Render signup page"""
    if 'user_id' in session:
        return redirect('/')
    return render_template('auth/signup_phone.html')

@auth_bp.route('/forgot-pin')
def forgot_pin_page():
    """Render forgot PIN page"""
    return render_template('auth/forgot_pin.html')

# ==================== TEST ROUTE ====================

@auth_bp.route('/test')
def test():
    """Test if blueprint is working"""
    return jsonify({
        'message': 'Blueprint is working!',
        'routes': [
            'GET /signup',
            'POST /api/auth/signup',
            'GET /login',
            'POST /api/auth/login',
            'POST /api/auth/logout',
            'GET /api/auth/user',
            'POST /api/auth/forgot-pin',
            'POST /api/auth/reset-pin',
            'GET /forgot-pin'
        ]
    })