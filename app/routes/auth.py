"""
Authentication Routes for MyFi
Handles user signup, login, logout using Supabase REST API
"""

from flask import Blueprint, request, jsonify, session, redirect, render_template
from functools import wraps
from app.backend.supabase_client import supabase

# Create Blueprint
auth_bp = Blueprint('auth', __name__)

# ==================== DECORATORS ====================

def login_required(f):
    """Decorator to protect routes that require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_token' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Verify token is still valid
        user = supabase.get_user(session['access_token'])
        if not user:
            session.clear()
            return jsonify({'error': 'Invalid session'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current authenticated user from session"""
    if 'access_token' not in session:
        return None
    
    return supabase.get_user(session['access_token'])

# ==================== AUTH API ROUTES ====================

@auth_bp.route('/api/auth/signup', methods=['POST'])
def signup():
    """
    Create a new user account
    Request body: { email, password, username, full_name }
    """
    data = request.get_json()
    
    # Validate input
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    username = data.get('username', '').strip()
    full_name = data.get('full_name', '').strip()
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    if '@' not in email:
        return jsonify({'error': 'Invalid email address'}), 400
    
    # Sign up user using REST API
    result = supabase.sign_up(
        email=email,
        password=password,
        user_metadata={
            'username': username,
            'full_name': full_name
        }
    )
    
    if result['success']:
        user_data = result['data']
        
        # Store session
        session['access_token'] = user_data['access_token']
        session['refresh_token'] = user_data['refresh_token']
        session['user_id'] = user_data['user']['id']
        session['email'] = user_data['user']['email']
        session.permanent = True
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'user': {
                'id': user_data['user']['id'],
                'email': user_data['user']['email'],
                'username': username,
                'full_name': full_name
            }
        }), 201
    else:
        error = result['error']
        # Handle common errors
        if 'already registered' in error.lower():
            return jsonify({'error': 'Email already registered'}), 400
        else:
            return jsonify({'error': error}), 400

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """
    Authenticate user and create session
    Request body: { email, password }
    """
    data = request.get_json()
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    # Sign in user using REST API
    result = supabase.sign_in(email=email, password=password)
    
    if result['success']:
        user_data = result['data']
        
        # Store session
        session['access_token'] = user_data['access_token']
        session['refresh_token'] = user_data['refresh_token']
        session['user_id'] = user_data['user']['id']
        session['email'] = user_data['user']['email']
        session.permanent = True
        
        # Get profile data
        profiles = supabase.select(
            'profiles',
            filters={'id': user_data['user']['id']},
            access_token=user_data['access_token']
        )
        profile = profiles[0] if profiles else {}
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user_data['user']['id'],
                'email': user_data['user']['email'],
                'username': profile.get('username'),
                'full_name': profile.get('full_name')
            }
        }), 200
    else:
        error = result['error']
        # Handle common errors
        if 'invalid' in error.lower():
            return jsonify({'error': 'Invalid email or password'}), 401
        else:
            return jsonify({'error': error}), 401

@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    """Clear user session and sign out from Supabase"""
    try:
        if 'access_token' in session:
            supabase.sign_out(session['access_token'])
        
        session.clear()
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        }), 200
    except Exception as e:
        session.clear()
        return jsonify({
            'success': True,
            'message': 'Logged out'
        }), 200

@auth_bp.route('/api/auth/user', methods=['GET'])
@login_required
def get_user():
    """Get current authenticated user information"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get profile data
        profiles = supabase.select(
            'profiles',
            filters={'id': user['id']},
            access_token=session['access_token']
        )
        profile = profiles[0] if profiles else {}
        
        return jsonify({
            'id': user['id'],
            'email': user['email'],
            'username': profile.get('username'),
            'full_name': profile.get('full_name'),
            'phone': profile.get('phone'),
            'avatar_url': profile.get('avatar_url'),
            'bio': profile.get('bio'),
            'created_at': profile.get('created_at')
        }), 200
        
    except Exception as e:
        print(f"Get user error: {e}")
        return jsonify({'error': 'Failed to fetch user data'}), 500

@auth_bp.route('/api/auth/check', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    user = get_current_user()
    
    if user:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': user['id'],
                'email': user['email']
            }
        }), 200
    else:
        return jsonify({'authenticated': False}), 200

# ==================== HTML PAGE ROUTES ====================

@auth_bp.route('/login')
def login_page():
    """Render login page"""
    if 'user_id' in session:
        return redirect('/')
    
    return render_template('auth/login.html')

@auth_bp.route('/signup')
def signup_page():
    """Render signup page"""
    if 'user_id' in session:
        return redirect('/')
    
    return render_template('auth/signup.html')