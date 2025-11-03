# routes/wifi.py - GATED VERSION WITH LOGIN & PAYMENT CHECKS

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
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

@wifi_bp.route('/generate_qr', methods=['POST'])
def generate_qr():
    """Generate WiFi QR code - Simple gated version"""
    try:
        # ============ GATE 1: CHECK LOGIN ============
        user_id = session.get('user_id')
        if not user_id:
            # Return index.html with a flag to open auth modal via JS
            return render_template('index.html', 
                open_auth_modal=True)
        
        # ============ GATE 2: GET USER DATA ============
        user_result = supabase.table('user').select('*').eq('id', user_id).execute()
        if not user_result.data:
            session.clear()
            return render_template('index.html', 
                open_auth_modal=True)
        
        user = user_result.data[0]
        
        # ============ GATE 3: CHECK WALLET BALANCE ============
        wallet_balance = float(user.get('wallet_balance', 0))
        if wallet_balance < 100:
            return render_template('index.html', 
                error_message=f"Wallet balance too low (KSh {wallet_balance:.0f}). Add at least KSh 100.",
                error_action="wallet")
        
        # ============ GATE 4: CHECK GROUP MEMBERSHIP ============
        if not user.get('member_id'):
            return render_template('index.html', 
                error_message="You're not in a group. Join a group first.",
                error_action="group")

        # ============ GATE 5: VERIFY GROUP & STATUS ============
        member_result = supabase.table('member').select('*, group(*)').eq('id', user['member_id']).execute()
        
        if not member_result.data or not member_result.data[0].get('group'):
            return render_template('index.html', 
                error_message="Group not found. Join a valid group.",
                error_action="group")
        
        member = member_result.data[0]
        group = member['group']
        
        # ============ GATE 6: CHECK GROUP STATUS ============
        group_status = group.get('status', 'pending')
        
        if group_status == 'pending':
            max_members = group.get('max_members', 3)
            # Count actual members in the group
            all_members = supabase.table('member').select('id').eq('group_id', group['id']).execute()
            current_members = len(all_members.data) if all_members.data else 0
            remaining = max_members - current_members
            return render_template('index.html', 
                error_message=f"Group not active yet. Waiting for {remaining} more member(s) to join.",
                error_action="group")
        
        # ============ GATE 7: CHECK GROUP EXPIRATION ============
        week_end = group.get('week_end')

        if not week_end:
            return render_template('index.html', 
                error_message="Group has not started yet. Wait for all members to join.",
                error_action="group")

        # Make both datetimes timezone-naive for comparison
        now = datetime.utcnow().replace(tzinfo=None)
        week_end_dt = datetime.fromisoformat(week_end.replace('Z', '+00:00')).replace(tzinfo=None)

        if group_status == 'expired' or now > week_end_dt:
            return render_template('index.html', 
                error_message="Your group access expired. Leave and join a new group.",
                error_action="group")
        # ============ GATE 8: VERIFY PAYMENT COMPLETE ============
        current_balance = float(group.get('current_balance', 0))
        target_amount = float(group.get('target_amount', 0))
        
        if current_balance < target_amount:
            remaining = target_amount - current_balance
            return render_template('index.html', 
                error_message=f"Group payment incomplete. KSh {remaining:.0f} remaining.",
                error_action="payment")
        
        # ============ GENERATE QR CODE ============
        SSID = os.getenv('SSID_NAME')
        PASSWORD = os.getenv('SSID_PASSWORD')
        SECURITY = os.getenv('SSID_SECURITY', 'WPA2')
        
        wifi_string = f"WIFI:S:{SSID};T:{SECURITY};P:{PASSWORD};H:False;;"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(wifi_string)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0051FF", back_color="white").convert("RGB")

        # Add logo (optional)
        try:
            logo = Image.open("myfi_logo.png")
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
        except:
            pass

        # Add border
        border_thickness = 20
        corner_radius = 30
        bordered_size = (img.size[0] + border_thickness * 2, img.size[1] + border_thickness * 2)
        bordered_img = Image.new("RGB", bordered_size, "white")
        
        draw = ImageDraw.Draw(bordered_img)
        draw.rounded_rectangle([(0, 0), bordered_size], radius=corner_radius, outline="black", width=4)
        bordered_img.paste(img, (border_thickness, border_thickness))

        buf = io.BytesIO()
        bordered_img.save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        print(f"✅ QR Code generated for user: {user['username']} | Group: {group['name']}")
        return render_template("index.html", qr_image=qr_b64, ssid=SSID)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return render_template("index.html", error_message="Something went wrong.")