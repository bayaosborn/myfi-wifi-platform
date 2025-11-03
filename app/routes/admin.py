# routes/admin.py (Complete version with wallet confirmation)

from flask import Blueprint, render_template, request, jsonify, session
from supabase import create_client
from werkzeug.security import check_password_hash
from datetime import datetime
from app.utils.decorators import admin_required
import os
from dotenv import load_dotenv

load_dotenv()

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# ===========================================
# ADMIN LOGIN & SESSION
# ===========================================

@admin_bp.route('/')
def admin_login_page():
    """Render admin login page"""
    return render_template('admin/admin_login.html')


@admin_bp.route('/api/login', methods=['POST'])
def admin_login():
    """Login route for admin users"""
    try:
        data = request.get_json()
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({"message": "Username and password required"}), 400

        username = data['username'].lower().strip()

        # Fetch user by username
        result = supabase.table('user').select('*').eq('username', username).execute()
        if not result.data:
            return jsonify({"message": "User not found"}), 404

        user = result.data[0]

        # Check password
        if not check_password_hash(user['password'], data['password']):
            return jsonify({"message": "Invalid password"}), 401

        # Check if user is an admin
        if user.get('role') != 'admin':
            return jsonify({"message": "Access denied - not an admin"}), 403

        # Require email for admins
        if not user.get('email'):
            return jsonify({"message": "Admin must have a registered email"}), 400

        # Update last login
        supabase.table('user').update({
            'last_login': datetime.utcnow().isoformat()
        }).eq('id', user['id']).execute()

        # Create session
        session['is_admin'] = True
        session['admin_username'] = user['username']
        session['admin_email'] = user['email']
        session['user_id'] = user['id']
        session.permanent = True

        print(f"✅ Admin login successful: {user['username']} ({user['email']})")

        return jsonify({
            "message": "Login successful",
            "admin": user['username'],
            "email": user['email']
        }), 200

    except Exception as e:
        print(f"❌ Admin login error: {e}")
        return jsonify({"message": "Login failed"}), 500


@admin_bp.route('/api/logout', methods=['POST'])
def admin_logout():
    """Logout admin"""
    session.clear()
    return jsonify({"message": "Logged out"}), 200


# ===========================================
# DASHBOARD DATA
# ===========================================

@admin_bp.route('/dashboard')
@admin_required
def admin_dashboard_page():
    """Render the admin dashboard"""
    return render_template('admin/admin_dashboard.html')


@admin_bp.route('/api/dashboard', methods=['GET'])
@admin_required
def admin_dashboard_api():
    """Fetch summary data for admin dashboard"""
    try:
        # Fetch all data
        groups_result = supabase.table('group').select('*').execute()
        users_result = supabase.table('user').select('*').execute()
        payments_result = supabase.table('payment').select('*').execute()

        groups = groups_result.data or []
        users = users_result.data or []
        payments = payments_result.data or []

        # Calculate statistics
        pending_payments = [p for p in payments if not p.get('verified') and not p.get('rejected')]
        verified_payments = [p for p in payments if p.get('verified')]
        total_revenue = sum(float(p.get('amount', 0)) for p in verified_payments)

        # Format groups with member details
        formatted_groups = []
        for group in groups:
            members = group.get('members', [])
            member_count = len(members)
            
            formatted_group = {
                'id': group.get('id'),
                'name': group.get('name'),
                'group_code': group.get('group_code'),
                'status': group.get('status', 'pending'),
                'member_count': member_count,
                'target_amount': group.get('target_amount', 0),
                'current_balance': group.get('current_balance', 0),
                'members': members,
                'created_at': group.get('created_at')
            }
            formatted_groups.append(formatted_group)

        # Format payments with details
        formatted_payments = []
        for payment in pending_payments:
            formatted_payment = {
                'id': payment.get('id'),
                'member_name': payment.get('member_name', 'Unknown'),
                'amount': payment.get('amount', 0),
                'group_name': payment.get('group_name', 'Unknown'),
                'mpesa_code': payment.get('mpesa_code', 'N/A'),
                'created_at': payment.get('created_at')
            }
            formatted_payments.append(formatted_payment)

        return jsonify({
            "total_groups": len(groups),
            "pending_payments": len(pending_payments),
            "total_revenue": total_revenue,
            "groups": formatted_groups,
            "payments": formatted_payments
        }), 200

    except Exception as e:
        print(f"❌ Dashboard load error: {e}")
        return jsonify({"error": str(e)}), 500


# ===========================================
# WALLET CONFIRMATION ROUTES
# ===========================================

@admin_bp.route('/dashboard/wallet_confirmation')
@admin_required
def wallet_confirmation_page():
    """Render wallet confirmation page"""
    try:
        # Get users with pending wallet payments
        result = supabase.table('user').select('*').eq('wallet_status', 'pending').execute()
        pending_users = result.data or []
        
        return render_template('admin/admin_wallet_confirmation.html', users=pending_users)
    except Exception as e:
        print(f"❌ Wallet confirmation page error: {e}")
        return render_template('admin/admin_wallet_confirmation.html', users=[])


@admin_bp.route('/api/wallet/confirm', methods=['POST'])
@admin_required
def confirm_wallet_payment():
    """Approve wallet payment"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"message": "User ID required"}), 400
        
        # Get user
        user_result = supabase.table('user').select('*').eq('id', user_id).execute()
        if not user_result.data:
            return jsonify({"message": "User not found"}), 404
        
        user = user_result.data[0]
        
        # Update wallet balance (assuming 100 KSH payment)
        current_balance = float(user.get('wallet_balance', 0))
        new_balance = current_balance + 100.0
        
        supabase.table('user').update({
            'wallet_balance': new_balance,
            'wallet_status': 'paid'
        }).eq('id', user_id).execute()
        
        return jsonify({"message": f"✅ Payment confirmed for {user['username']}. Balance: {new_balance} KSH"}), 200
        
    except Exception as e:
        print(f"❌ Wallet confirmation error: {e}")
        return jsonify({"message": f"Failed: {str(e)}"}), 500


@admin_bp.route('/api/wallet/reject', methods=['POST'])
@admin_required
def reject_wallet_payment():
    """Reject wallet payment"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"message": "User ID required"}), 400
        
        # Update status to rejected
        supabase.table('user').update({
            'wallet_status': 'rejected'
        }).eq('id', user_id).execute()
        
        return jsonify({"message": "❌ Payment rejected"}), 200
        
    except Exception as e:
        print(f"❌ Wallet rejection error: {e}")
        return jsonify({"message": f"Failed: {str(e)}"}), 500


# ===========================================
# GROUP EXPIRY CHECK
# ===========================================

@admin_bp.route('/api/expire-groups', methods=['POST'])
@admin_required
def expire_groups():
    """Manually check and expire groups that have passed their deadline"""
    try:
        groups_result = supabase.table('group').select('*').execute()
        groups = groups_result.data or []
        
        expired_count = 0
        current_time = datetime.utcnow()
        
        for group in groups:
            if group.get('status') == 'active':
                # Check if group has expired (e.g., 30 days from creation)
                created_at = datetime.fromisoformat(group['created_at'].replace('Z', '+00:00'))
                days_active = (current_time - created_at).days
                
                # If group is older than 30 days and not fully funded, expire it
                if days_active > 30 and group.get('current_balance', 0) < group.get('target_amount', 0):
                    supabase.table('group').update({
                        'status': 'expired'
                    }).eq('id', group['id']).execute()
                    expired_count += 1
        
        return jsonify({
            "message": f"Expired {expired_count} group(s)",
            "expired_count": expired_count
        }), 200
        
    except Exception as e:
        print(f"❌ Expire groups error: {e}")
        return jsonify({"message": f"Error: {str(e)}"}), 500


# ===========================================
# PAYMENT VERIFICATION
# ===========================================

@admin_bp.route('/api/verify-payment', methods=['POST'])
@admin_required
def verify_payment():
    """Approve or reject payment"""
    try:
        data = request.get_json()
        payment_id = data.get('payment_id')
        approve = data.get('approve', False)

        if not payment_id:
            return jsonify({"message": "Payment ID required"}), 400

        # Get payment
        payment_result = supabase.table('payment').select('*').eq('id', payment_id).execute()
        if not payment_result.data:
            return jsonify({"message": "Payment not found"}), 404

        payment = payment_result.data[0]

        if approve:
            # Approve payment
            supabase.table('payment').update({
                'verified': True,
                'rejected': False
            }).eq('id', payment_id).execute()

            # Update wallet balance
            if payment.get('user_id') and payment.get('amount'):
                user_result = supabase.table('user').select('wallet_balance').eq('id', payment['user_id']).execute()
                if user_result.data:
                    current_balance = float(user_result.data[0].get('wallet_balance', 0))
                    new_balance = current_balance + float(payment['amount'])
                    supabase.table('user').update({
                        'wallet_balance': new_balance
                    }).eq('id', payment['user_id']).execute()

            return jsonify({"message": "✅ Payment approved and wallet updated"}), 200
        else:
            # Reject payment
            supabase.table('payment').update({
                'verified': False,
                'rejected': True
            }).eq('id', payment_id).execute()
            return jsonify({"message": "❌ Payment rejected"}), 200

    except Exception as e:
        print(f"❌ Payment verification error: {e}")
        return jsonify({"message": f"Failed: {str(e)}"}), 500


# ===========================================
# USER MANAGEMENT
# ===========================================

@admin_bp.route('/api/users', methods=['GET'])
@admin_required
def get_all_users():
    """Get all users"""
    try:
        result = supabase.table('user').select('*').execute()
        return jsonify({"users": result.data or []}), 200
    except Exception as e:
        print(f"❌ Get users error: {e}")
        return jsonify({"error": str(e)}), 500


@admin_bp.route('/api/promote', methods=['POST'])
@admin_required
def promote_user():
    """Promote a normal user to admin"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')

        if not username or not email:
            return jsonify({"message": "Username and email required"}), 400

        supabase.table('user').update({
            'role': 'admin',
            'email': email
        }).eq('username', username).execute()

        return jsonify({"message": f"✅ User '{username}' promoted to admin"}), 200
    except Exception as e:
        print(f"❌ Promote user error: {e}")
        return jsonify({"message": f"Failed: {str(e)}"}), 500


@admin_bp.route('/api/delete-user/<user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete user"""
    try:
        supabase.table('user').delete().eq('id', user_id).execute()
        return jsonify({"message": "✅ User deleted successfully"}), 200
    except Exception as e:
        print(f"❌ Delete user error: {e}")
        return jsonify({"message": f"Failed: {str(e)}"}), 500





# ===========================================
# NOTIFICATION MANAGEMENT
# ===========================================

@admin_bp.route('/dashboard/notifications')
@admin_required
def notifications_management_page():
    """Render notifications management page"""
    return render_template('admin/admin_notifications.html')

@admin_bp.route('/api/notifications/send', methods=['POST'])
@admin_required
def send_notification():
    """Send notification to user(s)"""
    try:
        data = request.get_json()
        
        title = data.get('title')
        message = data.get('message')
        category = data.get('category', 'system')
        priority = data.get('priority', 'medium')
        target = data.get('target', 'all')
        user_id = data.get('user_id')
        
        if not title or not message:
            return jsonify({"message": "Title and message required"}), 400
        
        # Import the function from notifications
        from routes.notifications import send_notification_to_user
        
        if target == 'all':
            # Send to all users
            users = supabase.table('user').select('id').execute()
            sent_count = 0
            
            for user in users.data:
                success = send_notification_to_user(
                    user_id=user['id'],
                    title=title,
                    message=message,
                    category=category,
                    priority=priority
                )
                if success:
                    sent_count += 1
            
            return jsonify({
                "message": f"✅ Sent to {sent_count} users"
            }), 200
            
        elif target == 'single' and user_id:
            # Send to specific user
            success = send_notification_to_user(
                user_id=user_id,
                title=title,
                message=message,
                category=category,
                priority=priority
            )
            
            if success:
                return jsonify({
                    "message": "✅ Notification sent successfully"
                }), 200
            else:
                return jsonify({"message": "Failed to send notification"}), 500
        else:
            return jsonify({"message": "Invalid target"}), 400
            
    except Exception as e:
        print(f"❌ Send notification error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"Error: {str(e)}"}), 500

@admin_bp.route('/api/notifications/all', methods=['GET'])
@admin_required
def get_all_notifications():
    """Get all notifications sent (admin view)"""
    try:
        # Get all notifications, grouped by user
        notifications = supabase.table('notifications')\
            .select('*')\
            .order('created_at', desc=True)\
            .limit(100)\
            .execute()
        
        return jsonify({
            "success": True,
            "notifications": notifications.data or []
        }), 200
    except Exception as e:
        print(f"❌ Get notifications error: {e}")
        return jsonify({"error": str(e)}), 500