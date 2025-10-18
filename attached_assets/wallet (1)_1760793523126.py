# routes/wallet.py
from flask import Blueprint, jsonify, session, request
from supabase import create_client, Client
import os
from dotenv import load_dotenv
#import re

load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)


wallet_bp = Blueprint('wallet_bp', __name__)


''''
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # Use Service Role Key
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# -------------------- CHECK WALLET --------------------
@wallet_bp.route('/api/check-wallet', methods=['GET'])
def check_wallet():
    """Check the user's wallet balance + status."""
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"wallet_balance": 0.0, "wallet_status": "unauthorized"}), 401

    try:
        res = supabase.table("user").select("wallet_balance, wallet_status").eq("id", user_id).execute()

        if not res.data:
            return jsonify({"wallet_balance": 0.0, "wallet_status": "not_found"}), 404

        user = res.data[0]
        balance = float(user.get("wallet_balance", 0.0))
        status = user.get("wallet_status", "pending")

        return jsonify({"wallet_balance": balance, "wallet_status": status}), 200

    except Exception as e:
        return jsonify({"wallet_balance": 0.0, "wallet_status": "error", "message": str(e)}), 500
        print("CHECK WALLET USER:", user_id, balance, status)


# -------------------- CONFIRM PAYMENT (ADMIN) --------------------
@wallet_bp.route('/api/confirm-payment', methods=['POST'])
def confirm_payment():
    """
    Admin confirms a payment — credits 100 KSh and marks status as 'approved'.
    Expects JSON: {"username": "john_doe"} or {"user_id": "uuid"}
    """
    data = request.get_json() or {}
    username = data.get("username")
    user_id = data.get("user_id")

    try:
        if username:
            query = supabase.table("user").select("id").eq("username", username).execute()
            if not query.data:
                return jsonify({"message": "User not found"}), 404
            user_id = query.data[0]["id"]

        if not user_id:
            return jsonify({"message": "Missing user identifier"}), 400

        supabase.table("user").update({
            "wallet_balance": 100.0,
            "wallet_status": "approved"
        }).eq("id", user_id).execute()

        return jsonify({"message": "Wallet credited successfully"}), 200

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500


# -------------------- REJECT PAYMENT (ADMIN) --------------------
@wallet_bp.route('/api/reject-payment', methods=['POST'])
def reject_payment():
    """Admin rejects wallet payment and sets status to 'rejected'."""
    data = request.get_json() or {}
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"message": "Missing user_id"}), 400

    try:
        supabase.table("user").update({
            "wallet_status": "rejected",
            "wallet_balance": 0.0
        }).eq("id", user_id).execute()

        return jsonify({"message": "Wallet payment rejected"}), 200

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500
'''


# routes/wallet.py
@wallet_bp.route('/api/mark-payment-sent', methods=['POST'])
def mark_payment_sent():
    """User clicked 'I've Sent Payment' - update status to pending"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({"message": "Not logged in"}), 401
    
    try:
        supabase.table("user").update({
            "wallet_status": "pending"
        }).eq("id", user_id).execute()
        
        return jsonify({"message": "Payment marked as sent"}), 200
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500


@wallet_bp.route('/api/check-wallet', methods=['GET'])
def check_wallet():
    """Check the user's wallet balance + status"""
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"wallet_balance": 0.0, "wallet_status": "unauthorized"}), 401

    try:
        res = supabase.table("user").select("wallet_balance, wallet_status").eq("id", user_id).execute()

        if not res.data:
            return jsonify({"wallet_balance": 0.0, "wallet_status": "not_found"}), 404

        user = res.data[0]
        balance = float(user.get("wallet_balance", 0.0))
        status = user.get("wallet_status", "not_paid")

        return jsonify({
            "wallet_balance": balance, 
            "wallet_status": status
        }), 200

    except Exception as e:
        return jsonify({
            "wallet_balance": 0.0, 
            "wallet_status": "error", 
            "message": str(e)
        }), 500