# routes/groups.py
import os
import random
import string
from flask import Blueprint, render_template, request, jsonify, session
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

groups_bp = Blueprint('groups', __name__)

@groups_bp.route('/groups')
def groups_page():
    """View all groups"""
    try:
        result = supabase.table('group').select('*').execute()
        all_groups = result.data or []
        return render_template('groups/groups.html', groups=all_groups)
    except Exception as e:
        print(f"Error loading groups: {e}")
        return render_template('groups/groups.html', groups=[])


@groups_bp.route('/create-group')
def create_group_page():
    """Create group page"""
    user_id = session.get('user_id')
    if not user_id:
        return render_template('auth/login.html')
    return render_template('groups/create_group.html')


@groups_bp.route('/api/create-group', methods=['POST'])
def api_create_group():
    """Create a new group"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        if not data.get('group_name') or len(data['group_name']) < 3:
            return jsonify({"success": False, "message": "Group name must be at least 3 characters"}), 400
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"success": False, "message": "Not logged in"}), 401
        
        # ✅ Fetch user from Supabase
        user_result = supabase.table('user').select('*').eq('id', user_id).execute()
        
        if not user_result.data:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        user = user_result.data[0]
        
        # Check if user already in a group
        if user.get('member_id'):
            return jsonify({"success": False, "message": "You're already in a group. Leave it first."}), 400
        
        # Check wallet balance
        if user.get('wallet_balance', 0) < 100:
            return jsonify({"success": False, "message": "Insufficient wallet balance. Please credit your wallet first."}), 402
        
        # Generate unique group code
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # Calculate week_end (7 days from now)
        week_end = (datetime.utcnow() + timedelta(days=7)).isoformat()

        # ✅ Create group in Supabase
        group_result = supabase.table('group').insert({
            'name': data['group_name'],
            'admin_id': user_id,
            'target_amount': 400.0,  # 4 members × 100 KSh
            'current_amount': 0.0,
            'week_start': datetime.utcnow().isoformat(),
            'week_end': week_end,
            'is_active': True
        }).execute()
        
        new_group = group_result.data[0]
        
        # ✅ Create member in Supabase
        member_result = supabase.table('member').insert({
            'name': user['username'],
            'phone': user.get('default_mpesa_phone'),
            'group_id': new_group['id'],
            'amount_contributed': 0.0
        }).execute()
        
        new_member = member_result.data[0]
        
        # ✅ Link user to member
        supabase.table('user').update({
            'member_id': new_member['id']
        }).eq('id', user_id).execute()
        
        return jsonify({
            "success": True,
            "message": "Group created!",
            "group_code": code,
            "group_id": new_group['id']
        }), 201
        
    except Exception as e:
        print(f"Create group error: {e}")
        return jsonify({"success": False, "message": f"Failed to create group: {str(e)}"}), 500


@groups_bp.route('/api/join-group', methods=['POST'])
def api_join_group():
    """Join an existing group"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        if not data.get('group_code'):
            return jsonify({"success": False, "message": "Group code required"}), 400
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"success": False, "message": "Not logged in"}), 401
        
        # ✅ Fetch user from Supabase
        user_result = supabase.table('user').select('*').eq('id', user_id).execute()
        
        if not user_result.data:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        user = user_result.data[0]
        
        if user.get('member_id'):
            return jsonify({"success": False, "message": "You're already in a group. Leave it first."}), 400
        
        # Check wallet balance
        if user.get('wallet_balance', 0) < 100:
            return jsonify({"success": False, "message": "Insufficient wallet balance. Credit your wallet first."}), 402
        
        # ✅ Find group by code (need to add group_code column!)
        # For now, let's search by name or implement group_code
        group_result = supabase.table('group').select('*, member(*)').eq('name', data['group_code'].upper()).execute()
        
        if not group_result.data:
            return jsonify({"success": False, "message": "Group not found. Check the code."}), 404
        
        group = group_result.data[0]
        
        # Count members
        members_count = len(group.get('member', []))
        if members_count >= 4:
            return jsonify({"success": False, "message": "Group is full (max 4 members)"}), 400

        # ✅ Create member
        member_result = supabase.table('member').insert({
            'name': user['username'],
            'phone': user.get('default_mpesa_phone'),
            'group_id': group['id'],
            'amount_contributed': 0.0
        }).execute()
        
        new_member = member_result.data[0]
        
        # ✅ Link user to member
        supabase.table('user').update({
            'member_id': new_member['id']
        }).eq('id', user_id).execute()
        
        return jsonify({
            "success": True,
            "message": f"Joined {group['name']}!",
            "group_id": group['id']
        }), 200
        
    except Exception as e:
        print(f"Join group error: {e}")
        return jsonify({"success": False, "message": f"Failed to join group: {str(e)}"}), 500


@groups_bp.route('/api/search-group', methods=['GET'])
def search_group():
    """Search for a group by code or name"""
    try:
        code = request.args.get('code', '').upper().strip()
        
        if not code:
            return jsonify({"found": False, "message": "No code provided"})
        
        # Search by name (until we add group_code column)
        group_result = supabase.table('group').select('*, member(*)').eq('name', code).execute()
        
        if not group_result.data:
            return jsonify({"found": False})
        
        group = group_result.data[0]
        members_count = len(group.get('member', []))
        
        return jsonify({
            "found": True,
            "group": {
                "name": group['name'],
                "current_amount": group['current_amount'],
                "target_amount": group['target_amount'],
                "member_count": members_count,
                "remaining": group['target_amount'] - group['current_amount']
            }
        })
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({"found": False, "message": "Search failed"}), 500


@groups_bp.route('/api/leave-group', methods=['POST'])
def leave_group():
    """Leave current group"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"success": False, "message": "Not logged in"}), 401
        
        # ✅ Unlink user from member
        supabase.table('user').update({
            'member_id': None
        }).eq('id', user_id).execute()
        
        return jsonify({"success": True, "message": "You've left the group successfully"})
        
    except Exception as e:
        print(f"Leave group error: {e}")
        return jsonify({"success": False, "message": "Failed to leave group"}), 500



        