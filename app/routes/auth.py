# routes/auth.py

from flask import Blueprint, render_template, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.helpers import sanitize_input
from supabase import create_client
import os
from dotenv import load_dotenv
import re
from app.utils.decorators import location_required


load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

auth_bp = Blueprint('auth', __name__)

def is_valid_username(username):
    """Validate username: 3-20 chars, alphanumeric + underscore, no spaces"""
    if not username or len(username) < 3 or len(username) > 20:
        return False
    return bool(re.match(r'^[a-zA-Z0-9_]+$', username))

@auth_bp.route('/login')
def login_page():
    return render_template('auth/login.html')




# routes/auth.py
@auth_bp.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"message": "Username and password required"}), 400
    
    username = data['username'].lower().replace(' ', '')
    
    if not is_valid_username(username):
        return jsonify({"message": "Username must be 3-20 characters, letters, numbers and underscore only"}), 400
    
    if len(data['password']) < 6:
        return jsonify({"message": "Password must be at least 6 characters"}), 400
    
    mpesa_phone = data.get('mpesa_phone', '').strip()
    if not mpesa_phone:
        return jsonify({"message": "M-PESA phone number required"}), 400
    
    try:
        existing = supabase.table('user').select('id').eq('username', username).execute()
        if existing.data:
            return jsonify({"message": "Username already exists"}), 400
        
        hashed_pw = generate_password_hash(data['password'])
        result = supabase.table('user').insert({
            'username': username,
            'password': hashed_pw,
            'default_mpesa_phone': mpesa_phone,
            'wallet_balance': 0.0,
            'wallet_status': 'not_paid'  # User hasn't sent payment yet
        }).execute()
        
        new_user = result.data[0]
        session['user_id'] = new_user['id']
        session.permanent = True
        
        return jsonify({
            "message": "Account created!",
            "user_id": new_user['id'],
            "username": username
        }), 201
        
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500


#login

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    #print("=== LOGIN ATTEMPT ===")
    #print(f"Received data: {data}")
    
    if not data or not data.get('username') or not data.get('password'):
     #   print("ERROR: Missing username or password")
        return jsonify({"message": "Username and password required"}), 400
    
    username = data['username'].lower().strip()  # Also lowercase here!
    
   # print(f"Looking for username: {username}")
    
    try:
        # Get user
        result = supabase.table('user').select('*').eq('username', username).execute()
        
        #print(f"Supabase query result: {result.data}")
        
        if not result.data:
           # print("ERROR: User not found")
            return jsonify({"message": "Invalid username or password"}), 401
        
        user = result.data[0]
     #   print(f"Found user: {user['username']}, ID: {user['id']}")
        
        # Check password
        if not check_password_hash(user['password'], data['password']):
        #    print("ERROR: Invalid password")
            return jsonify({"message": "Invalid username or password"}), 401
        
        session['user_id'] = user['id']
        session.permanent = True
        
     #   print(f"SUCCESS: Login successful for user {user['username']}")
        
        return jsonify({
            "message": "Login successful", 
            "user_id": user['id'],
            "username": user['username']
        }), 200
        
    except Exception as e:
    #    print(f"EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"Error: {str(e)}"}), 500


    
        



#2/11/2025
# I'll route user back to home page instead of login page so user if they logout hey don't see login page but index. form there they can access profile again

@auth_bp.route('/logout')
def logout():
    session.clear()
    return render_template('/index.html')




@auth_bp.route('/api/whoami')
def whoami():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"username": None})
    
    try:
        result = supabase.table('user').select('username, id, member_id, default_mpesa_phone').eq('id', user_id).execute()
        if result.data:
            return jsonify(result.data[0])
        return jsonify({"username": None})
    except Exception as e:
        return jsonify({"username": None, "error": str(e)})



# routes/auth.py (add this route)
@auth_bp.route('/my-account')
#@location_required
def my_account():
    user_id = session.get('user_id')
    if not user_id:
        return render_template('auth/login.html')
    return render_template('user/my_account.html')
    

            
