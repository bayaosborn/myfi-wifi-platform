# routes/wifi.py - MIGRATED TO SUPABASE

from flask import Blueprint, render_template, request, jsonify, session
from supabase import create_client
from datetime import datetime
import qrcode
import io
import base64
from PIL import Image, ImageDraw
import os
from dotenv import load_dotenv

load_dotenv()

wifi_bp = Blueprint('wifi', __name__)

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

@wifi_bp.route('/')
def index():
    """Home page with QR generator"""
    return render_template('index.html')


@wifi_bp.route('/generate_qr', methods=['POST'])
def generate_qr():
    """Generate WiFi QR code"""
    try:
        SSID = os.getenv('SSID_NAME')
        PASSWORD = os.getenv('SSID_PASSWORD')
        SECURITY = os.getenv('SSID_SECURITY', 'WPA2')
        
        # Generate Wi-Fi QR string
        wifi_string = f"WIFI:S:{SSID};T:{SECURITY};P:{PASSWORD};H:False;;"

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(wifi_string)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0051FF", back_color="white").convert("RGB")

        # Add logo at center (optional)
        logo_path = "myfi_logo.png"
        try:
            logo = Image.open(logo_path)
            qr_width, qr_height = img.size
            logo_size = int(qr_width * 0.2)
            logo = logo.resize((logo_size, logo_size))
            pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
            
            mask = Image.new("L", (logo_size, logo_size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, logo_size, logo_size), fill=255)
            
            white_bg = Image.new("RGB", (logo_size, logo_size), "white")
            img.paste(white_bg, pos, mask=mask)
            img.paste(logo, pos, mask=logo if logo.mode == "RGBA" else None)
        except Exception as logo_err:
            print(f"Logo load error: {logo_err}")

        # Add border
        border_thickness = 20
        corner_radius = 30
        bordered_size = (img.size[0] + border_thickness * 2, img.size[1] + border_thickness * 2)
        bordered_img = Image.new("RGB", bordered_size, "white")
        
        draw = ImageDraw.Draw(bordered_img)
        draw.rounded_rectangle(
            [(0, 0), bordered_size],
            radius=corner_radius,
            outline="black",
            width=4
        )
        
        bordered_img.paste(img, (border_thickness, border_thickness))

        # Encode to base64
        buf = io.BytesIO()
        bordered_img.save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        return render_template("index.html", qr_image=qr_b64, ssid=SSID)

    except Exception as e:
        print(f"Error generating QR: {e}")
        return render_template("index.html", error="Failed to generate QR code")


@wifi_bp.route('/api/check-access', methods=['GET'])
def check_access():
    """Check if user has WiFi access"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({"has_access": False, "message": "Please login first"})
        
        # Get user from Supabase
        user_result = supabase.table('user').select('*').eq('id', user_id).execute()
        if not user_result.data or not user_result.data[0].get('member_id'):
            return jsonify({"has_access": False, "message": "Join a group first"})
        
        user = user_result.data[0]
        
        # Get member and group from Supabase
        member_result = supabase.table('member').select('*, group(*)').eq('id', user['member_id']).execute()
        if not member_result.data:
            return jsonify({"has_access": False, "message": "Group not found"})
        
        member = member_result.data[0]
        group = member.get('group')
        
        if not group:
            return jsonify({"has_access": False, "message": "Group not found"})
        
        now = datetime.utcnow()
        week_end = datetime.fromisoformat(group['week_end'].replace('Z', '+00:00'))
        
        # Check expiration
        if group['status'] == 'expired' or now > week_end:
            return jsonify({"has_access": False, "message": "Your group access has expired. Please join a new group."})
        
        # Check payment completion
        current_balance = float(group.get('current_balance', 0))
        target_amount = float(group.get('target_amount', 0))
        
        if current_balance < target_amount:
            remaining = target_amount - current_balance
            return jsonify({
                "has_access": False, 
                "message": f"Group payment incomplete. {remaining} KSH remaining ({current_balance}/{target_amount})"
            })
        
        return jsonify({"has_access": True})
        
    except Exception as e:
        print(f"Access check error: {e}")
        return jsonify({"has_access": False, "message": "Error checking access"}), 500


@wifi_bp.route('/my-account')
def my_account():
    """User account page"""
    user_id = session.get('user_id')
    if not user_id:
        return render_template('auth/login.html')
    return render_template('user/my_account.html')


@wifi_bp.route('/api/my-account', methods=['GET'])
def my_account_api():
    """Get user account data"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Not logged in"}), 401
        
        # Get user from Supabase
        user_result = supabase.table('user').select('*').eq('id', user_id).execute()
        if not user_result.data:
            return jsonify({"error": "User not found"}), 401
        
        user = user_result.data[0]
        
        result = {
            "username": user['username'],
            "group": None,
            "members": [],
            "my_contribution": 0
        }
        
        if user.get('member_id'):
            # Get member and group
            member_result = supabase.table('member').select('*, group(*)').eq('id', user['member_id']).execute()
            
            if member_result.data:
                member = member_result.data[0]
                group = member.get('group')
                
                if group:
                    now = datetime.utcnow()
                    week_end = datetime.fromisoformat(group['week_end'].replace('Z', '+00:00'))
                    is_expired = group['status'] == 'expired' or now > week_end
                    
                    # Update group status if expired
                    if is_expired and group['status'] != 'expired':
                        supabase.table('group').update({
                            'status': 'expired',
                            'password_revealed': False
                        }).eq('id', group['id']).execute()
                    
                    current_balance = float(group.get('current_balance', 0))
                    target_amount = float(group.get('target_amount', 0))
                    
                    result["group"] = {
                        "name": group['name'],
                        "group_code": group.get('group_code'),
                        "current_balance": current_balance,
                        "target_amount": target_amount,
                        "remaining": target_amount - current_balance,
                        "can_scan": current_balance >= target_amount and not is_expired,
                        "status": group['status'],
                        "week_end": group['week_end'],
                        "is_expired": is_expired
                    }
                    
                    # Get all members in group
                    members_result = supabase.table('member').select('*').eq('group_id', group['id']).execute()
                    result["members"] = [{
                        "name": m['name'],
                        "amount_contributed": m.get('amount_contributed', 0)
                    } for m in members_result.data]
                    
                    result["my_contribution"] = member.get('amount_contributed', 0)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"My account error: {e}")
        return jsonify({"error": "Failed to load account data"}), 500