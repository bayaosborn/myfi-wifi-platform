# routes/admin_wallet.py
from flask import Blueprint, render_template, jsonify, request, session
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

admin_wallet_bp = Blueprint('admin_wallet_bp', __name__)

# -------------------- HTML PAGE --------------------
@admin_wallet_bp.route("/admin/dashboard/wallet")
def wallet_confirmation_page():
    """Renders admin wallet confirmation page - ONLY shows pending users"""
    try:
        # ✅ Only fetch users with status = 'pending'
        res = supabase.table("user").select(
            "id, username, default_mpesa_phone, wallet_balance, wallet_status"
        ).eq("wallet_status", "pending").execute()
        
        users = res.data
        return render_template("admin/admin_wallet_confirmation.html", users=users)
    except Exception as e:
        return f"Error: {e}", 500


# -------------------- CONFIRM WALLET (AJAX) --------------------
@admin_wallet_bp.route("/admin/api/wallet/confirm", methods=["POST"])
def admin_confirm_wallet():
    """Admin confirms wallet payment."""
    data = request.get_json() or {}
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"message": "Missing user_id"}), 400

    try:
        # ✅ FIX: Update BOTH balance AND status
        supabase.table("user").update({
            "wallet_balance": 100.0,
            "wallet_status": "approved"  # ← THIS WAS MISSING!
        }).eq("id", user_id).execute()
        
        print(f"✅ Approved user {user_id}: balance=100, status=approved")
        return jsonify({"message": "Wallet credited successfully"}), 200
    except Exception as e:
        print(f"❌ Error approving user {user_id}: {e}")
        return jsonify({"message": f"Error: {str(e)}"}), 500


# -------------------- REJECT WALLET (AJAX) --------------------
@admin_wallet_bp.route("/admin/api/wallet/reject", methods=["POST"])
def admin_reject_wallet():
    """Admin rejects payment attempt."""
    data = request.get_json() or {}
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"message": "Missing user_id"}), 400

    try:
        # ✅ Set status to rejected
        supabase.table("user").update({
            "wallet_balance": 0.0,
            "wallet_status": "rejected"
        }).eq("id", user_id).execute()
        
        print(f"❌ Rejected user {user_id}")
        return jsonify({"message": "Wallet payment rejected"}), 200
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500