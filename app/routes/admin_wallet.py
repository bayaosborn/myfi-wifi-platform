# routes/admin_wallet.py
from flask import Blueprint, render_template, jsonify, request, session
from supabase import create_client
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

admin_wallet_bp = Blueprint('admin_wallet_bp', __name__)


# ==================== MANUAL PAYMENT APPROVAL PAGE ====================

@admin_wallet_bp.route("/admin/dashboard/wallet-confirmation")
# @admin_required  # Uncomment when ready
def wallet_confirmation_page():
    """Show all pending manual payments for admin approval"""
    try:
        print("🔍 Starting wallet_confirmation_page...")
        
        # Get pending transactions - NO JOIN, just get transaction data
        result = supabase.table('transactions')\
            .select('*')\
            .eq('status', 'pending')\
            .order('created_at', desc=False)\
            .execute()
        
        print(f"📊 Raw query result: {result.data}")
        
        pending_payments = result.data or []
        print(f"📊 Pending payments count: {len(pending_payments)}")
        
        # Fetch user data for each transaction separately
        for payment in pending_payments:
            user_id = payment.get('user_id')
            print(f"👤 Fetching user for user_id: {user_id}")
            
            if user_id:
                try:
                    user_result = supabase.table('user')\
                        .select('id, username')\
                        .eq('id', user_id)\
                        .single()\
                        .execute()
                    
                    if user_result.data:
                        payment['user'] = user_result.data
                        print(f"✅ User found: {user_result.data.get('username')}")
                    else:
                        payment['user'] = {'username': 'Unknown User'}
                        print(f"⚠️ No user data returned for user_id: {user_id}")
                except Exception as e:
                    print(f"❌ Error fetching user {user_id}: {e}")
                    payment['user'] = {'username': 'Error loading user'}
            else:
                payment['user'] = {'username': 'No User ID'}
                print(f"⚠️ Payment has no user_id")
        
        # Calculate stats
        pending_count = len(pending_payments)
        total_pending = sum(float(p.get('amount', 0)) for p in pending_payments)
        
        print(f"📊 Final stats - Count: {pending_count}, Total: KSh {total_pending}")
        print(f"📊 Final pending_payments: {pending_payments}")
        
        return render_template(
            "admin/admin_wallet_confirmation.html",
            pending_payments=pending_payments,
            pending_count=pending_count,
            total_pending=total_pending
        )
    except Exception as e:
        print(f"❌ Error loading wallet confirmation: {e}")
        import traceback
        traceback.print_exc()
        return f"<h1>Error</h1><pre>{e}\n\n{traceback.format_exc()}</pre>", 500
''''
@admin_wallet_bp.route("/admin/dashboard/wallet-confirmation")
# @admin_required  # Uncomment when ready
def wallet_confirmation_page():
    """Show all pending manual payments for admin approval"""
    try:
        # Get pending transactions with user data
        # Using separate queries to avoid join issues
        result = supabase.table('transactions')\
            .select('*')\
            .eq('status', 'pending')\
            .order('created_at', desc=False)\
            .execute()
        
        pending_payments = result.data or []
        
        # Fetch user data for each transaction
        for payment in pending_payments:
            user_id = payment.get('user_id')
            if user_id:
                user_result = supabase.table('user')\
                    .select('id, username')\
                    .eq('id', user_id)\
                    .single()\
                    .execute()
                
                if user_result.data:
                    payment['user'] = user_result.data
                else:
                    payment['user'] = {'username': 'Unknown User'}
            else:
                payment['user'] = {'username': 'Unknown User'}
        
        # Calculate stats
        pending_count = len(pending_payments)
        total_pending = sum(float(p.get('amount', 0)) for p in pending_payments)
        
        print(f"📊 Loaded {pending_count} pending payments, Total: KSh {total_pending}")
        
        return render_template(
            "admin/admin_wallet_confirmation.html",
            pending_payments=pending_payments,
            pending_count=pending_count,
            total_pending=total_pending
        )
    except Exception as e:
        print(f"❌ Error loading wallet confirmation: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {e}", 500
'''

# ==================== APPROVE PAYMENT ====================

@admin_wallet_bp.route("/admin/dashboard/confirm-payment", methods=["POST"])
# @admin_required
def confirm_payment():
    """Admin confirms payment with verified amount and M-Pesa code"""
    data = request.get_json()
    user_id = data.get('user_id')
    verified_amount = data.get('verified_amount')
    mpesa_code = data.get('mpesa_code', '').upper().strip()
    admin_notes = data.get('notes', '')
    
    if not all([user_id, verified_amount, mpesa_code]):
        return jsonify({"message": "Missing required fields"}), 400
    
    if float(verified_amount) < 1:
        return jsonify({"message": "Amount must be at least 1 KSh"}), 400
    
    try:
        # Get pending transaction for this user
        tx_result = supabase.table('transactions')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('status', 'pending')\
            .order('created_at', desc=True)\
            .limit(1)\
            .execute()
        
        if not tx_result.data:
            return jsonify({"message": "No pending transaction found for this user"}), 404
        
        transaction = tx_result.data[0]
        
        # Verify M-Pesa code matches
        if mpesa_code != transaction.get('mpesa_receipt_number', '').upper().strip():
            return jsonify({"message": f"M-Pesa code doesn't match. Expected: {transaction.get('mpesa_receipt_number', 'N/A')}"}), 400
        
        # Get current wallet balance
        user_result = supabase.table('user').select('wallet_balance').eq('id', user_id).single().execute()
        
        if not user_result.data:
            return jsonify({"message": "User not found"}), 404
        
        current_balance = float(user_result.data.get('wallet_balance', 0))
        new_balance = current_balance + float(verified_amount)
        
        # Update wallet balance
        supabase.table('user').update({
            'wallet_balance': new_balance,
            'wallet_status': 'approved'
        }).eq('id', user_id).execute()
        
        # Update transaction status
        supabase.table('transactions').update({
            'status': 'success',
            'amount': float(verified_amount),
            'mpesa_receipt_number': mpesa_code,
            'result_desc': f"Approved by admin. {admin_notes}".strip(),
            'updated_at': datetime.now().isoformat()
        }).eq('id', transaction['id']).execute()
        
        print(f"✅ Payment approved: User {user_id}, Amount {verified_amount}, Code {mpesa_code}")
        
        return jsonify({
            "message": "Payment confirmed successfully",
            "new_balance": new_balance
        }), 200
        
    except Exception as e:
        print(f"❌ Confirm payment error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": str(e)}), 500


# ==================== REJECT PAYMENT ====================

@admin_wallet_bp.route("/admin/dashboard/reject-payment", methods=["POST"])
# @admin_required
def reject_payment():
    """Admin rejects payment with reason"""
    data = request.get_json()
    user_id = data.get('user_id')
    reason = data.get('reason', '').strip()
    
    if not user_id:
        return jsonify({"message": "User ID required"}), 400
    
    if not reason:
        return jsonify({"message": "Rejection reason required"}), 400
    
    try:
        # Get pending transaction
        tx_result = supabase.table('transactions')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('status', 'pending')\
            .order('created_at', desc=True)\
            .limit(1)\
            .execute()
        
        if not tx_result.data:
            return jsonify({"message": "No pending transaction found"}), 404
        
        transaction = tx_result.data[0]
        
        # Update transaction to failed
        supabase.table('transactions').update({
            'status': 'failed',
            'result_desc': f"Rejected by admin: {reason}",
            'updated_at': datetime.now().isoformat()
        }).eq('id', transaction['id']).execute()
        
        # Optionally update user wallet_status
        supabase.table('user').update({
            'wallet_status': 'rejected'
        }).eq('id', user_id).execute()
        
        print(f"❌ Payment rejected: User {user_id}, Reason: {reason}")
        
        return jsonify({"message": "Payment rejected successfully"}), 200
        
    except Exception as e:
        print(f"❌ Reject payment error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": str(e)}), 500


# ==================== DEBUG ENDPOINT ====================

@admin_wallet_bp.route("/admin/dashboard/debug-transactions")
def debug_transactions():
    """Debug endpoint to see all transactions"""
    try:
        # Get ALL transactions
        all_tx = supabase.table('transactions').select('*').execute()
        
        # Get pending specifically
        pending_tx = supabase.table('transactions').select('*').eq('status', 'pending').execute()
        
        return jsonify({
            "total_transactions": len(all_tx.data or []),
            "pending_transactions": len(pending_tx.data or []),
            "all_transactions": all_tx.data,
            "pending_details": pending_tx.data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_wallet_bp.route("/admin/dashboard/wallet-debug")
def wallet_debug_page():
    """Debug page to see what data is being passed to template"""
    try:
        # Get pending transactions
        result = supabase.table('transactions')\
            .select('*')\
            .eq('status', 'pending')\
            .order('created_at', desc=False)\
            .execute()
        
        pending_payments = result.data or []
        
        # Fetch user data for each transaction
        for payment in pending_payments:
            user_id = payment.get('user_id')
            if user_id:
                try:
                    user_result = supabase.table('user')\
                        .select('id, username')\
                        .eq('id', user_id)\
                        .single()\
                        .execute()
                    
                    if user_result.data:
                        payment['user'] = user_result.data
                    else:
                        payment['user'] = {'username': 'Unknown User'}
                except Exception as e:
                    print(f"Error fetching user {user_id}: {e}")
                    payment['user'] = {'username': f'Error loading user'}
            else:
                payment['user'] = {'username': 'No User ID'}
        
        # Calculate stats
        pending_count = len(pending_payments)
        total_pending = sum(float(p.get('amount', 0)) for p in pending_payments)
        
        print(f"📊 DEBUG: Loaded {pending_count} pending payments")
        print(f"📊 DEBUG: Payments data: {pending_payments}")
        
        return render_template(
            "admin/wallet_debug.html",  # Save the HTML above as this file
            pending_payments=pending_payments,
            pending_count=pending_count,
            total_pending=total_pending
        )
    except Exception as e:
        print(f"❌ Error in debug page: {e}")
        import traceback
        traceback.print_exc()
        return f"<pre>Error: {e}\n\n{traceback.format_exc()}</pre>", 500