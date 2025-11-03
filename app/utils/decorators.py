# utils/decorators.py

from functools import wraps
from flask import session, redirect, url_for, render_template, jsonify, request
import os
from supabase import create_client
#from functools import wraps
#from flask import session, redirect, url_for, jsonify, request


# Initialize Supabase (if not already done in this file)
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

def login_required(f):
    """
    Decorator to require login for routes
    
    Usage:
        @app.route('/my-account')
        @login_required
        def my_account():
            return render_template('user/my_account.html')
    
    What it does:
    - Checks if 'user_id' exists in session
    - If not logged in, redirects to login page
    - If logged in, allows the function to execute
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # For HTML pages: render login page
            if request.path.startswith('/api/'):
                return jsonify({"error": "Not logged in"}), 401
            return render_template('auth/login.html')
        return f(*args, **kwargs)
    return decorated_function

'''
def admin_required(f):
    """
    Decorator to require admin login
    
    Usage:
        @app.route('/admin/dashboard')
        @admin_required
        def admin_dashboard():
            return render_template('admin/admin_dashboard.html')
    
    What it does:
    - Checks if 'is_admin' flag exists in session
    - If not admin, redirects to admin login page
    - If admin, allows the function to execute
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            # For HTML pages: render admin login
            if request.path.startswith('/api/'):
                return jsonify({"error": "Admin access required"}), 403
            return render_template('admin/admin_login.html')
        return f(*args, **kwargs)
    return decorated_function
'''

def check_group_access(f):
    """
    Decorator to check if user has access to a group
    
    Usage:
        @app.route('/generate_qr')
        @check_group_access
        def generate_qr():
            return render_template('index.html')
    
    What it does:
    - Checks if user is in a group
    - Checks if group payment is complete
    - Checks if group is not expired
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from models.user import User
        from models.member import Member
        from datetime import datetime
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Please login first"}), 401
        
        user = User.query.get(user_id)
        if not user or not user.member_id:
            return jsonify({"error": "Join a group first"}), 400
        
        member = Member.query.get(user.member_id)
        if not member or not member.group:
            return jsonify({"error": "Group not found"}), 404
        
        group = member.group
        now = datetime.utcnow()
        
        # Check expiration
        if group.status == 'expired' or now > group.week_end:
            return jsonify({"error": "Group access expired"}), 403
        
        # Check payment
        if group.current_balance < group.target_amount:
            return jsonify({"error": "Group payment incomplete"}), 402
        
        return f(*args, **kwargs)
    return decorated_function


def setup_session_config(app):
    """
    Configure Flask session settings
    
    What it does:
    - Sets session cookie security
    - Configures session lifetime
    - Enables permanent sessions
    
    Call this in app.py during initialization
    """
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600 * 24 * 7  # 7 days


# utils/decorators.py



def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in as admin
        if not session.get('is_admin'):
            # If it's an API request, return JSON error
            if request.path.startswith('/admin/api/'):
                return jsonify({"message": "Unauthorized - Admin access required"}), 401
            # Otherwise redirect to login
            return redirect(url_for('admin.admin_login_page'))
        
        return f(*args, **kwargs)
    return decorated_function







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