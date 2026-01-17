"""
Call Routes - Clean Implementation for MyFi v2.2
Handles WebRTC signaling, call history, and contact management
"""

from flask import Blueprint, render_template, request, jsonify, session
from flask_socketio import emit
from app.backend.supabase_client import supabase
from datetime import datetime
import uuid

call_bp = Blueprint('call', __name__, url_prefix='/call')

# Store active user sessions: {user_id: socket_id}
active_users = {}


# ==================== UTILITY FUNCTIONS ====================

def normalize_phone_number(phone):
    """
    Normalize phone number to match database format (254XXXXXXXXX)
    - Removes spaces, dashes, and other non-numeric characters
    - Replaces leading 0 with 254 (Kenya country code)
    
    Examples:
        0759335278 -> 254759335278
        0159335278 -> 254159335278
        254759335278 -> 254759335278 (already normalized)
    """
    if not phone:
        return phone
    
    # Remove spaces, dashes, and other non-numeric characters
    normalized = ''.join(filter(str.isdigit, phone))
    
    # Replace leading 0 with 254
    if normalized.startswith('0'):
        normalized = '254' + normalized[1:]
    
    return normalized


# ==================== HTTP ROUTES ====================

@call_bp.route('/')
def call_page():
    """Main call interface page"""
    user_id = session.get('user_id')
    if not user_id:
        return render_template('auth/login.html')
    return render_template('call/call.html')


@call_bp.route('/api/search', methods=['POST'])
def search_user():
    """
    Search for a MyFi user by phone number
    
    POST /call/api/search
    {
        "phone_number": "0712345678"
    }
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.get_json()
    search_phone = data.get('phone_number', '').strip()
    
    if not search_phone:
        return jsonify({"error": "Phone number required"}), 400
    
    # Normalize phone number
    normalized_phone = normalize_phone_number(search_phone)
    
    try:
        # Search in profiles table
        result = supabase.select('profiles', filters={'phone_number': normalized_phone})
        
        if not result:
            return jsonify({
                "found": False,
                "message": "User not found on MyFi",
                "phone_number": normalized_phone
            }), 404
        
        found_user = result[0]
        
        # Check if user is trying to call themselves
        if found_user['id'] == user_id:
            return jsonify({
                "found": False,
                "message": "You cannot call yourself"
            }), 400
        
        # Check if user is online
        is_online = found_user['id'] in active_users
        
        # Check if already saved as contact
        saved = supabase.select('contacts', filters={'user_id': user_id, 'phone': normalized_phone})
        
        is_saved = len(saved) > 0
        contact_info = saved[0] if is_saved else None
        
        return jsonify({
            "found": True,
            "user": {
                "id": found_user['id'],
                "phone_number": found_user['phone_number'],
                "full_name": found_user.get('full_name'),
                "avatar_url": found_user.get('avatar_url'),
                "online": is_online,
                "is_saved": is_saved,
                "contact_info": contact_info
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        return jsonify({"error": "Search failed"}), 500


@call_bp.route('/api/contacts/save', methods=['POST'])
def save_contact():
    """
    Save a user as contact
    
    POST /call/api/contacts/save
    {
        "phone_number": "0712345678",
        "name": "John Doe",
        "tag": "Friends"
    }
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.get_json()
    phone_number = data.get('phone_number', '').strip()
    name = data.get('name', '').strip()
    tag = data.get('tag', 'General')
    
    if not phone_number or not name:
        return jsonify({"error": "Phone number and name required"}), 400
    
    # Normalize phone number
    normalized_phone = normalize_phone_number(phone_number)
    
    try:
        # Check if already exists
        existing = supabase.select('contacts', filters={'user_id': user_id, 'phone': normalized_phone})
        
        if existing:
            return jsonify({
                "success": False,
                "message": "Contact already saved"
            }), 400
        
        # Create new contact
        result = supabase.insert('contacts', {
            'user_id': user_id,
            'name': name,
            'phone': normalized_phone,
            'tag': tag
        })
        
        if result['success']:
            return jsonify({
                "success": True,
                "message": "Contact saved successfully"
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Failed to save contact"
            }), 400
        
    except Exception as e:
        print(f"❌ Save contact error: {e}")
        return jsonify({"error": "Failed to save contact"}), 500


@call_bp.route('/api/contacts', methods=['GET'])
def get_contacts():
    """Get user's saved contacts with MyFi status"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    try:
        # Get all contacts
        contacts = supabase.select('contacts', filters={'user_id': user_id})
        
        if not contacts:
            return jsonify({"success": True, "contacts": []}), 200
        
        # Sort by name
        contacts_sorted = sorted(contacts, key=lambda x: x.get('name', '').lower())
        
        # Enrich with MyFi status and online status
        enriched_contacts = []
        for contact in contacts_sorted:
            # Check if phone number exists in MyFi
            myfi_user = supabase.select('profiles', filters={'phone_number': contact['phone']})
            
            is_myfi = len(myfi_user) > 0
            myfi_user_id = myfi_user[0]['id'] if is_myfi else None
            
            enriched_contacts.append({
                'id': contact['id'],
                'name': contact['name'],
                'phone': contact['phone'],
                'email': contact.get('email'),
                'tag': contact.get('tag', 'General'),
                'is_favorite': contact.get('is_favorite', False),
                'avatar_url': contact.get('avatar_url') or (myfi_user[0].get('avatar_url') if is_myfi else None),
                'is_myfi': is_myfi,
                'myfi_user_id': myfi_user_id,
                'online': myfi_user_id in active_users if is_myfi else False
            })
        
        return jsonify({
            "success": True,
            "contacts": enriched_contacts
        }), 200
        
    except Exception as e:
        print(f"❌ Get contacts error: {e}")
        return jsonify({"error": "Failed to load contacts"}), 500


@call_bp.route('/api/history', methods=['GET'])
def get_call_history():
    """Get recent call history (last 20 calls)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    try:
        # Get calls where user was caller or callee
        # Using manual query since we need OR condition
        all_calls = supabase.select('calls')
        
        # Filter for user's calls (caller OR callee)
        user_calls = [
            call for call in all_calls 
            if call.get('caller_id') == user_id or call.get('callee_id') == user_id
        ]
        
        # Sort by started_at descending
        user_calls_sorted = sorted(
            user_calls,
            key=lambda x: x.get('started_at', ''),
            reverse=True
        )[:20]  # Limit to 20
        
        # Enrich with caller/callee info
        enriched_calls = []
        for call in user_calls_sorted:
            # Get caller info
            caller = supabase.select('profiles', filters={'id': call['caller_id']})
            caller_info = caller[0] if caller else {}
            
            # Get callee info
            callee = supabase.select('profiles', filters={'id': call['callee_id']})
            callee_info = callee[0] if callee else {}
            
            # Determine direction
            direction = 'outgoing' if call['caller_id'] == user_id else 'incoming'
            
            enriched_calls.append({
                'id': call['id'],
                'caller_id': call['caller_id'],
                'callee_id': call['callee_id'],
                'caller_phone': caller_info.get('phone_number'),
                'callee_phone': callee_info.get('phone_number'),
                'caller_name': caller_info.get('full_name'),
                'callee_name': callee_info.get('full_name'),
                'status': call['status'],
                'duration': call.get('duration'),
                'started_at': call['started_at'],
                'answered_at': call.get('answered_at'),
                'ended_at': call.get('ended_at'),
                'direction': direction
            })
        
        return jsonify({
            "success": True,
            "calls": enriched_calls
        }), 200
        
    except Exception as e:
        print(f"❌ Get call history error: {e}")
        return jsonify({"error": "Failed to load call history"}), 500


@call_bp.route('/keep-alive')
def keep_alive():
    """Keep server awake (Render free tier)"""
    return jsonify({
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "active_users": len(active_users)
    }), 200


# ==================== SOCKETIO EVENTS ====================

def register_socketio_events(socketio):
    """Register WebSocket events for real-time calling"""
    
    @socketio.on('connect')
    def handle_connect():
        user_id = session.get('user_id')
        if user_id:
            active_users[user_id] = request.sid
            print(f"✅ User {user_id} connected (socket: {request.sid})")
            print(f"📊 Active users: {len(active_users)}")
        else:
            print(f"⚠️ Anonymous connection: {request.sid}")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        user_id = session.get('user_id')
        if user_id and user_id in active_users:
            del active_users[user_id]
            print(f"❌ User {user_id} disconnected")
            print(f"📊 Active users: {len(active_users)}")
    
    @socketio.on('call_user')
    def handle_call_user(data):
        """Initiate call to another user"""
        caller_id = session.get('user_id')
        callee_id = data.get('callee_id')
        offer = data.get('offer')
        
        if not caller_id or not callee_id or not offer:
            emit('call_failed', {'reason': 'Missing required data'})
            return
        
        print(f"📞 Call: {caller_id} → {callee_id}")
        
        # Create call record
        try:
            call_record = supabase.insert('calls', {
                'caller_id': caller_id,
                'callee_id': callee_id,
                'status': 'active',
                'started_at': datetime.utcnow().isoformat()
            })
            
            call_id = call_record['data'][0]['id'] if call_record['success'] and call_record['data'] else None
            print(f"✅ Call record created: {call_id}")
        except Exception as e:
            print(f"❌ Failed to create call record: {e}")
            call_id = None
        
        # Get caller info
        try:
            caller = supabase.select('profiles', filters={'id': caller_id})
            caller_info = caller[0] if caller else {}
        except:
            caller_info = {}
        
        # Send call to callee if online
        if callee_id in active_users:
            callee_socket = active_users[callee_id]
            socketio.emit('incoming_call', {
                'caller_id': caller_id,
                'caller_phone': caller_info.get('phone_number'),
                'caller_name': caller_info.get('full_name'),
                'caller_avatar': caller_info.get('avatar_url'),
                'offer': offer,
                'call_id': call_id
            }, room=callee_socket)
            print(f"✅ Call sent to {callee_id}")
        else:
            # User offline - update call as missed
            if call_id:
                supabase.update('calls', {'id': call_id}, {
                    'status': 'missed',
                    'ended_at': datetime.utcnow().isoformat()
                })
            
            emit('call_failed', {'reason': 'User is offline'})
            print(f"❌ User {callee_id} is offline")
    
    @socketio.on('answer_call')
    def handle_answer_call(data):
        """Callee answers the call"""
        callee_id = session.get('user_id')
        caller_id = data.get('caller_id')
        answer = data.get('answer')
        call_id = data.get('call_id')
        
        if not caller_id or not answer:
            return
        
        print(f"✅ Call answered: {callee_id} ← {caller_id}")
        
        # Update call status
        if call_id:
            try:
                supabase.update('calls', {'id': call_id}, {
                    'status': 'active',
                    'answered_at': datetime.utcnow().isoformat()
                })
            except Exception as e:
                print(f"⚠️ Failed to update call status: {e}")
        
        # Send answer to caller
        if caller_id in active_users:
            caller_socket = active_users[caller_id]
            socketio.emit('call_answered', {
                'callee_id': callee_id,
                'answer': answer,
                'call_id': call_id
            }, room=caller_socket)
    
    @socketio.on('reject_call')
    def handle_reject_call(data):
        """Callee rejects the call"""
        callee_id = session.get('user_id')
        caller_id = data.get('caller_id')
        call_id = data.get('call_id')
        
        print(f"❌ Call rejected: {callee_id} rejected {caller_id}")
        
        # Update call as rejected
        if call_id:
            supabase.update('calls', {'id': call_id}, {
                'status': 'rejected',
                'ended_at': datetime.utcnow().isoformat()
            })
        
        # Notify caller
        if caller_id in active_users:
            socketio.emit('call_rejected', {}, room=active_users[caller_id])
    
    @socketio.on('ice_candidate')
    def handle_ice_candidate(data):
        """Exchange ICE candidates for WebRTC"""
        sender_id = session.get('user_id')
        recipient_id = data.get('recipient_id')
        candidate = data.get('candidate')
        
        if recipient_id in active_users:
            socketio.emit('ice_candidate', {
                'sender_id': sender_id,
                'candidate': candidate
            }, room=active_users[recipient_id])
    
    @socketio.on('hang_up')
    def handle_hang_up(data):
        """End the call"""
        user_id = session.get('user_id')
        other_user_id = data.get('other_user_id')
        call_id = data.get('call_id')
        duration = data.get('duration', 0)
        
        print(f"📴 Call ended: {user_id} ↔ {other_user_id} ({duration}s)")
        
        # Update call record
        if call_id:
            try:
                supabase.update('calls', {'id': call_id}, {
                    'status': 'completed',
                    'duration': duration,
                    'ended_at': datetime.utcnow().isoformat()
                })
                print(f"✅ Call record updated: {call_id}")
            except Exception as e:
                print(f"❌ Failed to update call record: {e}")
        
        # Notify other user
        if other_user_id in active_users:
            socketio.emit('call_ended', {
                'user_id': user_id
            }, room=active_users[other_user_id])