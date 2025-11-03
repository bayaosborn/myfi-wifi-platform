# routes/manual_payment.py
from flask import Blueprint, request, jsonify, session
from supabase import create_client
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

manual_payment_bp = Blueprint('manual_payment_bp', __name__, url_prefix='/api/manual-payment')

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)


@manual_payment_bp.route('/submit', methods=['POST'])
def submit_manual_payment():
    """Submit manual payment for admin approval"""
    data = request.get_json()
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"message": "Please login first"}), 401
    
    phone = data.get('phone')
    amount = data.get('amount')
    mpesa_code = data.get('mpesa_code', '').upper().strip()
    
    # Validation
    if not all([phone, amount, mpesa_code]):
        return jsonify({"message": "All fields are required"}), 400
    
    if amount < 50:
        return jsonify({"message": "Minimum payment is 50 KSh"}), 400
    
    if len(mpesa_code) < 8:
        return jsonify({"message": "Invalid M-Pesa code format"}), 400
    
    try:
        # Check for duplicate M-Pesa code
        existing = supabase.table('transactions').select('id').eq('mpesa_receipt_number', mpesa_code).execute()
        
        if existing.data:
            return jsonify({"message": "This M-Pesa code has already been submitted"}), 400
        
        # Save transaction as pending
        supabase.table('transactions').insert({
            'user_id': user_id,
            'default_mpesa_phone': phone,
            'amount': float(amount),
            'status': 'pending',
            'mpesa_receipt_number': mpesa_code,
            'created_at': datetime.now().isoformat()
        }).execute()
        
        print(f"✓ Manual payment submitted: User {user_id}, Amount {amount}, Code {mpesa_code}")
        
        return jsonify({"message": "Payment submitted successfully"}), 200
        
    except Exception as e:
        print(f"Manual payment error: {e}")
        return jsonify({"message": "Failed to submit payment. Please try again."}), 500