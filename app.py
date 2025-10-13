from flask import Flask, render_template, jsonify, request, session
import qrcode
import io
import base64
import secrets
import random
import string
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Group, Member, Payment, WiFiCredential, User
from accounts import init_accounts
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os


load_dotenv()

def check_expired_groups():
    """Check and expire groups that have passed their week_end date"""
    try:
        now = datetime.utcnow()
        expired_groups = Group.query.filter(
            Group.week_end <= now,
            Group.status != 'expired'
        ).all()
        
        for group in expired_groups:
            group.status = 'expired'
            group.password_revealed = False
        
        if expired_groups:
            db.session.commit()
            print(f"✅ Expired {len(expired_groups)} groups")
        
        return len(expired_groups)
    except Exception as e:
        print(f"❌ Error checking expired groups: {e}")
        return 0

def login_required(f):
    """Decorator to require login for routes"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return render_template('login.html')
        return f(*args, **kwargs)
    return decorated_function

# Admin password (change this!)
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
print(ADMIN_PASSWORD)


def admin_required(f):
    """Decorator to require admin login"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return render_template('admin_login.html')
        return f(*args, **kwargs)
    return decorated_function

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///myfi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = secrets.token_hex(16)

db.init_app(app)
init_accounts(app, db)

# Create tables on startup
with app.app_context():
    db.create_all()
    print("✅ Database tables created")

# Network credentials
SSID = os.getenv('SSID')
PASSWORD = os.getenv('SSID_PASSWORD')
SECURITY = os.getenv('SSID_SECURITY')

# Global error handler
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({"error": "Something went wrong. Please try again."}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Page not found"}), 404

# ===== ALL ROUTES =====

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    try:
        wifi_string = f"WIFI:T:{SECURITY};S:{SSID};P:{PASSWORD};;"
        img = qrcode.make(wifi_string)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        return render_template('index.html', qr_image=qr_b64, ssid=SSID)
    except Exception as e:
        print(f"Error generating QR: {e}")
        return render_template('index.html', error="Failed to generate QR code")

@app.route('/groups')
def groups_page():
    try:
        all_groups = Group.query.all()
        return render_template('groups.html', groups=all_groups)
    except Exception as e:
        print(f"Error loading groups: {e}")
        return render_template('groups.html', groups=[])

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/api/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({"message": "Username and password required"}), 400
        
        if len(data['username']) < 3:
            return jsonify({"message": "Username must be at least 3 characters"}), 400
        
        if len(data['password']) < 6:
            return jsonify({"message": "Password must be at least 6 characters"}), 400
        
        existing = User.query.filter_by(username=data['username']).first()
        if existing:
            return jsonify({"message": "Username already exists"}), 400
        
        hashed_pw = generate_password_hash(data['password'])
        new_user = User(username=data['username'], password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        
        session['user_id'] = new_user.id
        return jsonify({"message": "Account created!"}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Signup error: {e}")
        return jsonify({"message": "Failed to create account. Please try again."}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({"message": "Username and password required"}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        if not user or not check_password_hash(user.password, data['password']):
            return jsonify({"message": "Invalid username or password"}), 401
        
        session['user_id'] = user.id
        return jsonify({"message": "Login successful", "user_id": user.id}), 200
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"message": "Login failed. Please try again."}), 500

@app.route('/api/my-account', methods=['GET'])
def my_account_api():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Not logged in"}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 401
        
        result = {
            "username": user.username,
            "group": None,
            "members": [],
            "my_contribution": 0
        }
        
        if user.member_id:
            member = Member.query.get(user.member_id)
            if member and member.group:
                group = member.group
                now = datetime.utcnow()
                is_expired = group.status == 'expired' or now > group.week_end
                
                if is_expired and group.status != 'expired':
                    group.status = 'expired'
                    group.password_revealed = False
                    db.session.commit()
                
                result["group"] = {
                    "name": group.name,
                    "group_code": group.group_code,
                    "current_balance": group.current_balance,
                    "target_amount": group.target_amount,
                    "can_scan": group.current_balance >= group.target_amount and not is_expired,
                    "status": group.status,
                    "week_end": group.week_end.strftime('%Y-%m-%d %H:%M'),
                    "is_expired": is_expired
                }
                result["members"] = [{
                    "name": m.name,
                    "amount_contributed": m.amount_contributed
                } for m in group.members]
                result["my_contribution"] = member.amount_contributed
        
        return jsonify(result)
    except Exception as e:
        print(f"My account error: {e}")
        return jsonify({"error": "Failed to load account data"}), 500

@app.before_request
def check_expirations():
    """Check for expired groups periodically"""
    try:
        if request.endpoint in ['static', 'login_page', 'admin_login_page']:
            return
        
        last_check = session.get('last_expiry_check')
        now = datetime.utcnow()
        
        if not last_check or (now - datetime.fromisoformat(last_check)).total_seconds() > 3600:
            check_expired_groups()
            session['last_expiry_check'] = now.isoformat()
    except Exception as e:
        print(f"Expiry check error: {e}")

@app.route('/my-account')
@login_required
def my_account():
    return render_template('my_account.html')

@app.route('/api/check-access', methods=['GET'])
def check_access():
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({"has_access": False, "message": "Please login first"})
        
        user = User.query.get(user_id)
        if not user or not user.member_id:
            return jsonify({"has_access": False, "message": "Join a group first"})
        
        member = Member.query.get(user.member_id)
        if not member or not member.group:
            return jsonify({"has_access": False, "message": "Group not found"})
        
        group = member.group
        now = datetime.utcnow()
        
        if group.status == 'expired' or now > group.week_end:
            return jsonify({"has_access": False, "message": "Your group access has expired. Please join a new group."})
        
        if group.current_balance < group.target_amount:
            return jsonify({"has_access": False, "message": f"Group payment incomplete ({group.current_balance}/{group.target_amount} KSH)"})
        
        return jsonify({"has_access": True})
    except Exception as e:
        print(f"Access check error: {e}")
        return jsonify({"has_access": False, "message": "Error checking access"}), 500

@app.route('/create-group')
@login_required
def create_group_page():
    return render_template('create_group.html')

@app.route('/test-expire')
def test_expire():
    try:
        group = Group.query.first()
        if group:
            group.week_end = datetime.utcnow() - timedelta(hours=1)
            group.status = 'active'
            group.current_balance = 350
            group.password_revealed = True
            db.session.commit()
            return f"Group {group.name} set to expire 1 hour ago (and marked active)"
        return "No groups found"
    except Exception as e:
        return f"Error: {e}"

@app.route('/api/create-group', methods=['POST'])
def api_create_group():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        if not data.get('group_name') or len(data['group_name']) < 3:
            return jsonify({"success": False, "message": "Group name must be at least 3 characters"}), 400
        
        if not data.get('member_name') or len(data['member_name']) < 2:
            return jsonify({"success": False, "message": "Your name is required"}), 400
        
        if not data.get('phone') or len(data['phone']) < 10:
            return jsonify({"success": False, "message": "Valid phone number required (10+ digits)"}), 400
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"success": False, "message": "Not logged in"}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        if user.member_id:
            return jsonify({"success": False, "message": "You're already in a group. Leave it first."}), 400
        
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        new_group = Group(
            name=data['group_name'],
            group_code=code,
            target_amount=350,
            current_balance=0
        )
        db.session.add(new_group)
        db.session.commit()
        
        member = Member(
            name=data['member_name'],
            phone=data['phone'],
            group_id=new_group.id,
            amount_contributed=0
        )
        db.session.add(member)
        db.session.commit()
        
        user.member_id = member.id
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Group created!",
            "group_code": code,
            "group_id": new_group.id
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Create group error: {e}")
        return jsonify({"success": False, "message": "Failed to create group. Please try again."}), 500

@app.route('/api/join-group', methods=['POST'])
def api_join_group():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        if not data.get('group_code'):
            return jsonify({"success": False, "message": "Group code required"}), 400
        
        if not data.get('member_name') or len(data['member_name']) < 2:
            return jsonify({"success": False, "message": "Your name is required"}), 400
        
        if not data.get('phone') or len(data['phone']) < 10:
            return jsonify({"success": False, "message": "Valid phone number required"}), 400
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"success": False, "message": "Not logged in"}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        if user.member_id:
            return jsonify({"success": False, "message": "You're already in a group. Leave it first."}), 400
        
        group = Group.query.filter_by(group_code=data['group_code'].upper()).first()
        
        if not group:
            return jsonify({"success": False, "message": "Group not found. Check the code."}), 404
        
        if len(group.members) >= 4:
            return jsonify({"success": False, "message": "Group is full (max 4 members)"}), 400
        
        member = Member(
            name=data['member_name'],
            phone=data['phone'],
            group_id=group.id,
            amount_contributed=0
        )
        db.session.add(member)
        db.session.commit()
        
        user.member_id = member.id
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Joined {group.name}!",
            "group_id": group.id
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Join group error: {e}")
        return jsonify({"success": False, "message": "Failed to join group. Please try again."}), 500

@app.route('/add-payment')
@login_required
def add_payment_page():
    return render_template('add_payment.html')

@app.route('/api/add-payment', methods=['POST'])
def api_add_payment():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"success": False, "message": "Not logged in"}), 401
        
        user = User.query.get(user_id)
        if not user or not user.member_id:
            return jsonify({"success": False, "message": "You're not in a group"}), 400
        
        member = Member.query.get(user.member_id)
        if not member or not member.group:
            return jsonify({"success": False, "message": "Group not found"}), 404
        
        group = member.group
        
        try:
            amount = float(data.get('amount', 0))
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Invalid amount"}), 400
        
        if amount <= 0:
            return jsonify({"success": False, "message": "Amount must be greater than 0"}), 400
        
        if amount > 500:
            return jsonify({"success": False, "message": "Maximum payment is 500 KSH"}), 400
        
        payment = Payment(
            member_id=member.id,
            group_id=group.id,
            amount=amount,
            mpesa_code=data.get('mpesa_code', '').strip() or None,
            verified=False
        )
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Payment of {amount} KSH submitted! Waiting for admin verification.",
            "payment_id": payment.id
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Payment error: {e}")
        return jsonify({"success": False, "message": "Failed to submit payment. Please try again."}), 500

@app.route('/logout')
def logout():
    session.clear()
    return render_template('login.html')

@app.route('/api/admin/expire-groups', methods=['POST'])
@admin_required
def admin_expire_groups():
    try:
        count = check_expired_groups()
        return jsonify({"message": f"Checked all groups. {count} expired and updated."})
    except Exception as e:
        print(f"Admin expire error: {e}")
        return jsonify({"message": "Error checking groups"}), 500

@app.route('/api/search-group', methods=['GET'])
def search_group():
    try:
        code = request.args.get('code', '').upper().strip()
        
        if not code:
            return jsonify({"found": False, "message": "No code provided"})
        
        group = Group.query.filter_by(group_code=code).first()
        
        if not group:
            return jsonify({"found": False})
        
        return jsonify({
            "found": True,
            "group": {
                "name": group.name,
                "group_code": group.group_code,
                "current_balance": group.current_balance,
                "target_amount": group.target_amount,
                "member_count": len(group.members)
            }
        })
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({"found": False, "message": "Search failed"}), 500

@app.route('/api/leave-group', methods=['POST'])
def leave_group():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"success": False, "message": "Not logged in"}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        if not user.member_id:
            return jsonify({"success": False, "message": "You're not in a group"}), 400
        
        user.member_id = None
        db.session.commit()
        
        return jsonify({"success": True, "message": "You've left the group successfully"})
    except Exception as e:
        db.session.rollback()
        print(f"Leave group error: {e}")
        return jsonify({"success": False, "message": "Failed to leave group"}), 500

@app.route('/api/whoami')
def whoami():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"username": None})
        
        user = User.query.get(user_id)
        return jsonify({"username": user.username if user else None})
    except Exception as e:
        print(f"Whoami error: {e}")
        return jsonify({"username": None})

# ADMIN ROUTES

@app.route('/admin')
def admin_login_page():
    return render_template('admin_login.html')

@app.route('/api/admin-login', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        
        if not data or not data.get('password'):
            return jsonify({"message": "Password required"}), 400
        
        if data['password'] == ADMIN_PASSWORD:
            session['is_admin'] = True
            return jsonify({"message": "Login successful"}), 200
        else:
            return jsonify({"message": "Invalid password"}), 401
    except Exception as e:
        print(f"Admin login error: {e}")
        return jsonify({"message": "Login failed"}), 500

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/api/admin/dashboard', methods=['GET'])
@admin_required
def admin_dashboard_api():
    try:
        all_groups = Group.query.all()
        pending_payments = Payment.query.filter_by(verified=False).all()
        verified_payments = Payment.query.filter_by(verified=True).all()
        
        total_revenue = sum(p.amount for p in verified_payments)
        
        payments_data = [{
            "id": p.id,
            "member_name": p.member.name if p.member else "Unknown",
            "group_name": p.group.name if p.group else "Unknown",
            "amount": p.amount,
            "mpesa_code": p.mpesa_code or "N/A"
        } for p in pending_payments]
        
        groups_data = [{
            "name": g.name,
            "group_code": g.group_code,
            "status": g.status,
            "current_balance": g.current_balance,
            "target_amount": g.target_amount,
            "member_count": len(g.members),
            "members": [{"name": m.name, "amount_contributed": m.amount_contributed} for m in g.members]
        } for g in all_groups]
        
        return jsonify({
            "total_groups": len(all_groups),
            "pending_payments": len(pending_payments),
            "total_revenue": total_revenue,
            "payments": payments_data,
            "groups": groups_data
        })
    except Exception as e:
        print(f"Admin dashboard error: {e}")
        return jsonify({"error": "Failed to load dashboard"}), 500

@app.route('/api/admin/verify-payment', methods=['POST'])
@admin_required
def verify_payment():
    try:
        data = request.get_json()
        
        if not data or 'payment_id' not in data:
            return jsonify({"message": "Payment ID required"}), 400
        
        payment = Payment.query.get(data['payment_id'])
        
        if not payment:
            return jsonify({"message": "Payment not found"}), 404
        
        if data.get('approve'):
            payment.verified = True
            
            member = payment.member
            member.amount_contributed += payment.amount
            
            group = payment.group
            group.current_balance += payment.amount
            
            if group.current_balance >= group.target_amount and not group.password_revealed:
                group.password_revealed = True
                group.status = 'active'
            
            db.session.commit()
            return jsonify({"message": f"Payment approved! {payment.amount} KSH added."})
        else:
            db.session.delete(payment)
            db.session.commit()
            return jsonify({"message": "Payment rejected and removed."})
    except Exception as e:
        db.session.rollback()
        print(f"Verify payment error: {e}")
        return jsonify({"message": "Failed to verify payment"}), 500

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('is_admin', None)
    return jsonify({"message": "Logged out"})

@app.route('/test-db')
def test_db():
    try:
        groups = Group.query.all()
        return jsonify({
            "status": "success",
            "groups_count": len(groups),
            "groups": [{"id": g.id, "name": g.name, "code": g.group_code} for g in groups]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/reset-db-confirm')
def reset_db_confirm():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Reset Database</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; background: #f5f5f5; }
            h1 { color: #dc3545; }
            button { background: #dc3545; color: white; padding: 20px 40px; font-size: 18px; border: none; border-radius: 8px; cursor: pointer; }
            button:hover { background: #c82333; }
            .warning { background: #fff3cd; padding: 20px; margin: 20px auto; max-width: 500px; border-radius: 8px; color: #856404; }
        </style>
    </head>
    <body>
        <h1>⚠️ Reset Database</h1>
        <div class="warning">
            <strong>WARNING:</strong> This will permanently delete:
            <ul style="text-align: left;">
                <li>All users</li>
                <li>All groups</li>
                <li>All payments</li>
                <li>All data</li>
            </ul>
            This action cannot be undone!
        </div>
        <form action="/reset-db" method="post">
            <button type="submit">YES, DELETE EVERYTHING</button>
        </form>
        <br><br>
        <a href="/">Cancel and go back</a>
    </body>
    </html>
    """

@app.route('/reset-db', methods=['POST'])
def reset_db():
    try:
        db.drop_all()
        db.create_all()
        session.clear()
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Database Reset</title>
            <style>
                body { font-family: Arial; text-align: center; padding: 50px; background: #d4edda; }
                h1 { color: #155724; }
                a { color: #0051ff; text-decoration: none; font-size: 18px; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1>✅ Database Reset Complete!</h1>
            <p>All data has been deleted.</p>
            <a href="/">Go to Home Page</a>
        </body>
        </html>
        """
    except Exception as e:
        return f"Error resetting database: {e}", 500

# ===== THIS MUST BE LAST =====
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)