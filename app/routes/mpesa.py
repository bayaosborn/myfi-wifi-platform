# routes/mpesa.py
from flask import Blueprint, request, jsonify, session
import requests
from requests.auth import HTTPBasicAuth
import base64
import json
from datetime import datetime
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

mpesa_bp = Blueprint('mpesa_bp', __name__, url_prefix='/api/mpesa')

# Initialize Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# Sandbox credentials
CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
SHORTCODE = "174379"
PASSKEY = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
BASE_URL = os.getenv("BASE_URL", "https://d85b7960-1602-49de-82e6-d6a6a057c2c2-00-2f8oug5nd4017.spock.replit.dev")


def get_access_token():
    """Get M-Pesa access token"""
    endpoint = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    
    try:
        r = requests.get(endpoint, auth=HTTPBasicAuth(CONSUMER_KEY, CONSUMER_SECRET))
        data = r.json()
        return data.get('access_token')
    except Exception as e:
        print(f"Token error: {e}")
        return None


@mpesa_bp.route('/test')
def test():
    """Test if M-Pesa routes are working"""
    return jsonify({
        "status": "M-Pesa routes active",
        "endpoints": ["/stk-push", "/callback", "/check-payment"]
    })


@mpesa_bp.route('/stk-push', methods=['POST'])
def stk_push():
    """Initiate STK Push"""
    data = request.get_json()
    phone = data.get('phone')
    amount = data.get('amount', 10)
    
    if not phone:
        return jsonify({"error": "Phone number required"}), 400
    
    # Format phone number
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    elif not phone.startswith("254"):
        phone = "254" + phone
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        return jsonify({"error": "Failed to get access token. Check credentials."}), 500
    
    # Prepare request
    endpoint = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    headers = {"Authorization": f"Bearer {access_token}"}
    callback_url = BASE_URL + "/api/mpesa/callback"
    
    # Generate password
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password_string = SHORTCODE + PASSKEY + timestamp
    password = base64.b64encode(password_string.encode('utf-8')).decode('utf-8')
    
    payload = {
        "BusinessShortCode": SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": callback_url,
        "AccountReference": "MYFI WIFI",
        "TransactionDesc": "Wallet Top-up"
    }
    
    print("\n=== STK PUSH REQUEST ===")
    print(f"Phone: {phone}")
    print(f"Amount: {amount}")
    print(f"Callback: {callback_url}")
    print("========================\n")
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        response_data = response.json()
        
        print(f"Response: {response.status_code}")
        print(f"Body: {response.text}")
        
        # If successful, save transaction to database
        if response.ok and response_data.get('ResponseCode') == "0":
            user_id = session.get('user_id')
            checkout_request_id = response_data.get('CheckoutRequestID')
            
            if user_id and checkout_request_id:
                try:
                    supabase.table('transactions').insert({
                        'user_id': user_id,
                        'phone': phone,
                        'amount': float(amount),
                        'status': 'pending',
                        'checkout_request_id': checkout_request_id,
                        'merchant_request_id': response_data.get('MerchantRequestID'),
                        'created_at': datetime.now().isoformat()
                    }).execute()
                    print(f"✓ Transaction saved: {checkout_request_id}")
                except Exception as e:
                    print(f"Failed to save transaction: {e}")
        
        return jsonify(response_data), response.status_code
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@mpesa_bp.route('/callback', methods=['POST'])
def callback():
    """Handle M-Pesa callback and update transaction + wallet"""
    data = request.get_json()
    
    print("\n" + "="*60)
    print("M-PESA CALLBACK RECEIVED")
    print(json.dumps(data, indent=2))
    print("="*60 + "\n")
    
    try:
        body = data.get('Body', {}).get('stkCallback', {})
        result_code = body.get('ResultCode')
        checkout_request_id = body.get('CheckoutRequestID')
        
        if result_code == 0:  # Success
            # Get transaction details from callback
            callback_metadata = body.get('CallbackMetadata', {}).get('Item', [])
            amount = None
            mpesa_receipt = None
            phone = None
            
            for item in callback_metadata:
                if item.get('Name') == 'Amount':
                    amount = item.get('Value')
                elif item.get('Name') == 'MpesaReceiptNumber':
                    mpesa_receipt = item.get('Value')
                elif item.get('Name') == 'PhoneNumber':
                    phone = str(item.get('Value'))
            
            # Update transaction status
            supabase.table('transactions').update({
                'status': 'success',
                'mpesa_receipt_number': mpesa_receipt,
                'result_desc': body.get('ResultDesc'),
                'updated_at': datetime.now().isoformat()
            }).eq('checkout_request_id', checkout_request_id).execute()
            
            # Update user wallet
            tx_result = supabase.table('transactions').select('user_id').eq('checkout_request_id', checkout_request_id).execute()
            
            if tx_result.data:
                user_id = tx_result.data[0]['user_id']
                
                # Get current balance
                user_result = supabase.table('user').select('wallet_balance').eq('id', user_id).execute()
                current_balance = float(user_result.data[0].get('wallet_balance', 0))
                
                # Add amount to wallet
                new_balance = current_balance + float(amount)
                supabase.table('user').update({
                    'wallet_balance': new_balance,
                    'wallet_status': 'approved'
                }).eq('id', user_id).execute()
                
                print(f"✓ Wallet updated: User {user_id}, New balance: {new_balance}")
        
        else:  # Failed
            supabase.table('transactions').update({
                'status': 'failed',
                'result_desc': body.get('ResultDesc'),
                'updated_at': datetime.now().isoformat()
            }).eq('checkout_request_id', checkout_request_id).execute()
            
            print(f"✗ Payment failed: {body.get('ResultDesc')}")
        
        return jsonify({"ResultCode": 0, "ResultDesc": "Success"})
        
    except Exception as e:
        print(f"Callback error: {e}")
        return jsonify({"ResultCode": 1, "ResultDesc": str(e)})


@mpesa_bp.route('/check-payment', methods=['GET'])
def check_payment():
    """Check payment status (for polling)"""
    checkout_request_id = request.args.get('checkout_request_id')
    
    try:
        result = supabase.table('transactions').select('status').eq('checkout_request_id', checkout_request_id).execute()
        
        if result.data:
            status = result.data[0]['status']
            return jsonify({"status": status})
        
        return jsonify({"status": "pending"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500