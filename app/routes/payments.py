# routes/payments.py - MIGRATED TO SUPABASE

from flask import Blueprint, render_template, request, jsonify, session
from supabase import create_client
from app.utils.decorators import login_required
import os
from dotenv import load_dotenv

load_dotenv()

payments_bp = Blueprint('payments', __name__)

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

@payments_bp.route('/add-payment')
@login_required
def add_payment_page():
    """Payment submission page"""
    return render_template('payments/add_payment.html')


@payments_bp.route('/api/add-payment', methods=['POST'])
@login_required
def api_add_payment():
    """Submit a payment for verification"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"success": False, "message": "Not logged in"}), 401
        
        # Get user from Supabase
        user_result = supabase.table('user').select('*').eq('id', user_id).execute()
        if not user_result.data:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        user = user_result.data[0]
        
        if not user.get('member_id'):
            return jsonify({"success": False, "message": "You're not in a group"}), 400
        
        # Get member from Supabase
        member_result = supabase.table('member').select('*, group(*)').eq('id', user['member_id']).execute()
        if not member_result.data:
            return jsonify({"success": False, "message": "Member not found"}), 404
        
        member = member_result.data[0]
        group = member.get('group')
        
        if not group:
            return jsonify({"success": False, "message": "Group not found"}), 404
        
        # Validate amount
        try:
            amount = float(data.get('amount', 0))
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Invalid amount"}), 400
        
        if amount <= 0:
            return jsonify({"success": False, "message": "Amount must be greater than 0"}), 400
        
        if amount > 500:
            return jsonify({"success": False, "message": "Maximum payment is 500 KSH"}), 400
        
        # Create payment in Supabase
        payment_data = {
            'member_id': member['id'],
            'group_id': group['id'],
            'amount': amount,
            'mpesa_code': data.get('mpesa_code', '').strip() or None,
            'verified': False,
            'member_name': member['name'],
            'group_name': group['name']
        }
        
        result = supabase.table('payment').insert(payment_data).execute()
        
        if result.data:
            return jsonify({
                "success": True,
                "message": f"Payment of {amount} KSH submitted! Waiting for admin verification.",
                "payment_id": result.data[0]['id']
            }), 200
        else:
            return jsonify({"success": False, "message": "Failed to create payment"}), 500
            
    except Exception as e:
        print(f"Payment error: {e}")
        return jsonify({"success": False, "message": "Failed to submit payment. Please try again."}), 500