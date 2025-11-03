# routes/wallet.py
from flask import Blueprint, jsonify, session
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import requests
import base64
from requests.auth import HTTPBasicAuth
#import re

load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)


wallet_bp = Blueprint('wallet_bp', __name__)

#mpesa_bp = Blueprint('mpesa', __name__)


#authorization route from mpesa for access token


def get_daraja_access_token():
    """Fetch Daraja access token from Safaricom API"""
    consumer_key = os.getenv("MPESA_CONSUMER_KEY")
    consumer_secret = os.getenv("MPESA_CONSUMER_SECRET")
    daraja_env = os.getenv("DARAJA_ENV", "sandbox")

    if not consumer_key or not consumer_secret:
        raise Exception("Missing Daraja API credentials in .env")

    if daraja_env == "sandbox":
        url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    else:
        url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    try:
        response = requests.get(url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
        response.raise_for_status()
        access_token = response.json().get("access_token")
        return access_token
    except Exception as e:
        print("Error fetching Daraja access token:", e)
        return None

#temporary route

@wallet_bp.route('/api/test-daraja-token', methods=['GET'])
def test_daraja_token():
    token = get_daraja_access_token()
    if token:
        return jsonify({"access_token": token}), 200
    else:
        return jsonify({"error": "Failed to fetch token"}), 500

#stk push route

''''
@mpesa_bp.route('/api/stk_push', methods=['POST'])
def stk_push():
    try:
        # --- Static details ---
        short_code = "174379"
        passkey = "bfb279f9aa9bdbcf15e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c9192"  # Public sandbox passkey
        callback_url = "https://sandbox.safaricom.co.ke/mpesa/callback"  # Replace later with your route

        # --- Dynamic details ---
        amount = request.json.get("amount", 1)  # default to 1
        phone_number = request.json.get("default_mpesa_phone")  # use your DB field name

        # --- Timestamp and password ---
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode((short_code + passkey + timestamp).encode()).decode()

        # --- Headers and body ---
        headers = {
            "Authorization": f"Bearer {os.getenv('MPESA_ACCESS_TOKEN')}",  # or paste token directly for test
            "Content-Type": "application/json"
        }

        payload = {
            "BusinessShortCode": short_code,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": short_code,
            "PhoneNumber": phone_number,
            "CallBackURL": callback_url,
            "AccountReference": "1350CAPITAL",
            "TransactionDesc": "Deposit to 1350 Capital account"
        }

        # --- Send request ---
        response = requests.post(
            "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers=headers
        )

        return jsonify(response.json()), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500



    
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

'''''
@wallet_bp.route('/api/my-account', methods=['GET'])
def my_account():
    """Get user's account info including group and members"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({"message": "Not logged in"}), 401
    
    try:
        # Get user with member info
        user_result = supabase.table('user')\
            .select('*, member(*)')\
            .eq('id', user_id)\
            .single()\
            .execute()
        
        if not user_result.data:
            return jsonify({"message": "User not found"}), 404
        
        user = user_result.data
        member = user.get('member')
        
        # If user is not in a group
        if not member:
            return jsonify({
                "username": user.get('username'),
                "wallet_balance": user.get('wallet_balance', 0),
                "group": None,
                "members": []
            }), 200
        
        # User is in a group - fetch group details
        group_id = member.get('group_id')
        
        group_result = supabase.table('group')\
            .select('*')\
            .eq('id', group_id)\
            .single()\
            .execute()
        
        group = group_result.data if group_result.data else None
        
        # Fetch all members of the group
        members_result = supabase.table('member')\
            .select('*')\
            .eq('group_id', group_id)\
            .execute()
        
        members = members_result.data or []
        
        return jsonify({
            "username": user.get('username'),
            "wallet_balance": user.get('wallet_balance', 0),
            "group": group,
            "members": members
        }), 200
        
    except Exception as e:
        print(f"❌ My account error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"Error: {str(e)}"}), 500

'''

@wallet_bp.route('/api/my-account', methods=['GET'])
def my_account():
    """Get user's account info including group and members"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({"message": "Not logged in"}), 401
    
    try:
        # Get user data
        user_result = supabase.table('user')\
            .select('id, username, wallet_balance, member_id')\
            .eq('id', user_id)\
            .single()\
            .execute()
        
        if not user_result.data:
            return jsonify({"message": "User not found"}), 404
        
        user = user_result.data
        member_id = user.get('member_id')
        
        print(f"🔍 User {user.get('username')} has member_id: {member_id}")
        
        # If user is not in a group
        if not member_id:
            print(f"⚠️ User has no member_id - not in a group")
            return jsonify({
                "username": user.get('username'),
                "wallet_balance": user.get('wallet_balance', 0),
                "group": None,
                "members": []
            }), 200
        
        # Fetch member details
        member_result = supabase.table('member')\
            .select('*')\
            .eq('id', member_id)\
            .single()\
            .execute()
        
        if not member_result.data:
            print(f"⚠️ Member with id {member_id} not found")
            return jsonify({
                "username": user.get('username'),
                "wallet_balance": user.get('wallet_balance', 0),
                "group": None,
                "members": []
            }), 200
        
        member = member_result.data
        group_id = member.get('group_id')
        
        print(f"✅ Member found, group_id: {group_id}")
        
        # Fetch group details
        group_result = supabase.table('group')\
            .select('*')\
            .eq('id', group_id)\
            .single()\
            .execute()
        
        group = group_result.data if group_result.data else None
        
        print(f"✅ Group found: {group.get('name') if group else 'None'}")
        
        # Fetch all members of the group
        members_result = supabase.table('member')\
            .select('*')\
            .eq('group_id', group_id)\
            .execute()
        
        members = members_result.data or []
        
        print(f"✅ Found {len(members)} members in group")
        
        return jsonify({
            "username": user.get('username'),
            "wallet_balance": user.get('wallet_balance', 0),
            "group": group,
            "members": members
        }), 200
        
    except Exception as e:
        print(f"❌ My account error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"Error: {str(e)}", "group": None, "members": []}), 500

