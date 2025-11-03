# routes/call_routes.py

from flask import Blueprint, render_template, request, jsonify, session
from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

call_bp = Blueprint('call', __name__)

# Store active user sessions: {user_id: socket_id}
active_users = {}

@call_bp.route('/search')
def search_page():
    """The search/phone page"""
    user_id = session.get('user_id')
    if not user_id:
        return render_template('auth/login.html')
    return render_template('search/search.html')


@call_bp.route('/api/search-user', methods=['POST'])
def search_user():
    """Search for a user by username"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.get_json()
    search_username = data.get('username', '').lower().strip()
    
    if not search_username:
        return jsonify({"error": "Username required"}), 400
    
    try:
        result = supabase.table('user').select('id, username').eq('username', search_username).execute()
        
        if not result.data:
            return jsonify({"found": False, "message": "User not found"}), 404
        
        found_user = result.data[0]
        
        if found_user['id'] == user_id:
            return jsonify({"found": False, "message": "You cannot call yourself"}), 400
        
        # Check if user is online
        is_online = found_user['id'] in active_users
        
        # Check if already saved as contact
        saved = supabase.table('contacts')\
            .select('id, custom_name')\
            .eq('user_id', user_id)\
            .eq('contact_user_id', found_user['id'])\
            .execute()
        
        is_saved = len(saved.data) > 0
        custom_name = saved.data[0]['custom_name'] if is_saved else None
        
        print(f"🔍 User {found_user['username']} online: {is_online}, saved: {is_saved}")
        
        return jsonify({
            "found": True,
            "user": {
                "id": found_user['id'],
                "username": found_user['username'],
                "online": is_online,
                "is_saved": is_saved,
                "custom_name": custom_name
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        return jsonify({"error": str(e)}), 500


@call_bp.route('/api/contacts/save', methods=['POST'])
def save_contact():
    """Save a contact with optional custom name"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.get_json()
    contact_user_id = data.get('contact_user_id')
    custom_name = data.get('custom_name', '').strip()
    
    if not contact_user_id:
        return jsonify({"error": "Contact user ID required"}), 400
    
    try:
        # Check if already saved
        existing = supabase.table('contacts')\
            .select('id')\
            .eq('user_id', user_id)\
            .eq('contact_user_id', contact_user_id)\
            .execute()
        
        if existing.data:
            # Update custom name
            supabase.table('contacts').update({
                'custom_name': custom_name if custom_name else None
            }).eq('id', existing.data[0]['id']).execute()
            
            return jsonify({
                "success": True,
                "message": "Contact updated"
            }), 200
        else:
            # Create new contact
            supabase.table('contacts').insert({
                'user_id': user_id,
                'contact_user_id': contact_user_id,
                'custom_name': custom_name if custom_name else None
            }).execute()
            
            return jsonify({
                "success": True,
                "message": "Contact saved"
            }), 200
            
    except Exception as e:
        print(f"❌ Save contact error: {e}")
        return jsonify({"error": str(e)}), 500


@call_bp.route('/api/contacts', methods=['GET'])
def get_contacts():
    """Get user's saved contacts"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    try:
        # Get contacts with user info
        contacts = supabase.table('contacts')\
            .select('id, contact_user_id, custom_name, saved_at')\
            .eq('user_id', user_id)\
            .order('saved_at', desc=True)\
            .execute()
        
        # Enrich with user details and online status
        enriched_contacts = []
        for contact in contacts.data:
            user_info = supabase.table('user')\
                .select('username')\
                .eq('id', contact['contact_user_id'])\
                .execute()
            
            if user_info.data:
                enriched_contacts.append({
                    'id': contact['id'],
                    'user_id': contact['contact_user_id'],
                    'username': user_info.data[0]['username'],
                    'custom_name': contact['custom_name'],
                    'online': contact['contact_user_id'] in active_users
                })
        
        return jsonify({
            "success": True,
            "contacts": enriched_contacts
        }), 200
        
    except Exception as e:
        print(f"❌ Get contacts error: {e}")
        return jsonify({"error": str(e)}), 500


@call_bp.route('/api/contacts/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    """Delete a saved contact"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    try:
        supabase.table('contacts')\
            .delete()\
            .eq('id', contact_id)\
            .eq('user_id', user_id)\
            .execute()
        
        return jsonify({"success": True}), 200
        
    except Exception as e:
        print(f"❌ Delete contact error: {e}")
        return jsonify({"error": str(e)}), 500





@call_bp.route('/api/call-history', methods=['GET'])
def get_call_history():
    """Get recent call history (last 5)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    try:
        # Get calls where user was caller
        caller_calls = supabase.table('call_history')\
            .select('*')\
            .eq('caller_id', user_id)\
            .order('started_at', desc=True)\
            .execute()
        
        # Get calls where user was callee
        callee_calls = supabase.table('call_history')\
            .select('*')\
            .eq('callee_id', user_id)\
            .order('started_at', desc=True)\
            .execute()
        
        # Combine all calls
        all_calls = (caller_calls.data or []) + (callee_calls.data or [])
        
        # Sort by started_at (newest first)
        all_calls.sort(key=lambda x: x['started_at'], reverse=True)
        
        # Take only last 5
        recent_calls = all_calls[:5]
        
        print(f"📋 Found {len(all_calls)} total calls for user {user_id}")
        print(f"📋 Returning {len(recent_calls)} recent calls")
        
        # Enrich with usernames
        enriched_calls = []
        for call in recent_calls:
            # Determine the other user in the call
            if call['caller_id'] == user_id:
                other_user_id = call['callee_id']
                direction = 'outgoing'
            else:
                other_user_id = call['caller_id']
                direction = 'incoming'
            
            # Get other user's username
            try:
                user_info = supabase.table('user')\
                    .select('username')\
                    .eq('id', other_user_id)\
                    .execute()
                
                other_username = user_info.data[0]['username'] if user_info.data else 'Unknown'
            except Exception as e:
                print(f"⚠️ Error fetching username for user {other_user_id}: {e}")
                other_username = 'Unknown'
            
            enriched_calls.append({
                'id': call['id'],
                'other_user_id': other_user_id,
                'other_username': other_username,
                'direction': direction,
                'status': call['call_status'],
                'duration': call.get('call_duration', 0),
                'started_at': call['started_at']
            })
        
        return jsonify({
            "success": True,
            "calls": enriched_calls
        }), 200
        
    except Exception as e:
        print(f"❌ Get call history error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500



'''''
@call_bp.route('/api/call-history', methods=['GET'])
def get_call_history():
    """Get recent call history (last 5)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    try:
        # Get calls where user was caller or callee
        calls = supabase.rpc('get_user_call_history', {
            'p_user_id': user_id,
            'p_limit': 5
        }).execute()
        
        # If RPC doesn't exist, use direct query
        if not calls.data:
            caller_calls = supabase.table('call_history')\
                .select('*')\
                .eq('caller_id', user_id)\
                .order('started_at', desc=True)\
                .limit(5)\
                .execute()
            
            callee_calls = supabase.table('call_history')\
                .select('*')\
                .eq('callee_id', user_id)\
                .order('started_at', desc=True)\
                .limit(5)\
                .execute()
            
            # Combine and sort
            all_calls = caller_calls.data + callee_calls.data
            all_calls.sort(key=lambda x: x['started_at'], reverse=True)
            calls_data = all_calls[:5]
        else:
            calls_data = calls.data
        
        # Enrich with usernames
        enriched_calls = []
        for call in calls_data:
            other_user_id = call['callee_id'] if call['caller_id'] == user_id else call['caller_id']
            
            user_info = supabase.table('user')\
                .select('username')\
                .eq('id', other_user_id)\
                .execute()
            
            enriched_calls.append({
                'id': call['id'],
                'other_username': user_info.data[0]['username'] if user_info.data else 'Unknown',
                'direction': 'outgoing' if call['caller_id'] == user_id else 'incoming',
                'status': call['call_status'],
                'duration': call['call_duration'],
                'started_at': call['started_at']
            })
        
        return jsonify({
            "success": True,
            "calls": enriched_calls
        }), 200
        
    except Exception as e:
        print(f"❌ Get call history error: {e}")
        return jsonify({"error": str(e)}), 500
'''





#New sockerio events handlers to see why database table is not being updated. Logging on console to see possible errors 

def register_socketio_events(socketio):
    """Register WebSocket events for calling"""
    
    @socketio.on('connect')
    def handle_connect():
        user_id = session.get('user_id')
        if user_id:
            active_users[user_id] = request.sid
            print(f"✅ User {user_id} connected with socket {request.sid}")
            print(f"📋 Active users: {list(active_users.keys())}")
        else:
            print(f"⚠️ Connection without user_id")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        user_id = session.get('user_id')
        if user_id and user_id in active_users:
            del active_users[user_id]
            print(f"❌ User {user_id} disconnected")
            print(f"📋 Active users: {list(active_users.keys())}")
    
    @socketio.on('call_user')
    def handle_call_user(data):
        """Initiate call to another user"""
        caller_id = session.get('user_id')
        callee_id = data.get('callee_id')
        offer = data.get('offer')
        
        try:
            callee_id = int(callee_id)
        except (ValueError, TypeError):
            print(f"❌ Invalid callee_id: {callee_id}")
            socketio.emit('call_failed', {'reason': 'Invalid user ID'}, room=request.sid)
            return
        
        print(f"📞 Call from {caller_id} to {callee_id}")
        
        if not caller_id or not callee_id:
            print(f"❌ Missing caller_id or callee_id")
            return
        
        # CREATE CALL HISTORY RECORD
        call_id = None
        try:
            print(f"💾 Creating call history record...")
            call_record = supabase.table('call_history').insert({
                'caller_id': caller_id,
                'callee_id': callee_id,
                'call_status': 'initiated',
                'started_at': datetime.utcnow().isoformat()
            }).execute()
            
            if call_record.data and len(call_record.data) > 0:
                call_id = call_record.data[0]['id']
                print(f"✅ Call history created with ID: {call_id}")
            else:
                print(f"⚠️ Call history insert returned no data")
                
        except Exception as e:
            print(f"❌ FAILED to create call history: {e}")
            import traceback
            traceback.print_exc()
        
        # Get caller username
        try:
            caller = supabase.table('user').select('username').eq('id', caller_id).execute()
            caller_username = caller.data[0]['username'] if caller.data else 'Unknown'
        except Exception as e:
            print(f"⚠️ Error fetching caller username: {e}")
            caller_username = 'Unknown'
        
        # Check if callee is online
        if callee_id in active_users:
            callee_socket = active_users[callee_id]
            print(f"✅ Sending call to {callee_id} at socket {callee_socket}")
            socketio.emit('incoming_call', {
                'caller_id': caller_id,
                'caller_username': caller_username,
                'offer': offer,
                'call_id': call_id
            }, room=callee_socket)
        else:
            print(f"❌ User {callee_id} is offline")
            
            # Update call as failed
            if call_id:
                try:
                    print(f"💾 Updating call {call_id} status to 'failed'")
                    supabase.table('call_history').update({
                        'call_status': 'failed',
                        'ended_at': datetime.utcnow().isoformat()
                    }).eq('id', call_id).execute()
                    print(f"✅ Call {call_id} marked as failed")
                except Exception as e:
                    print(f"❌ Failed to update call status: {e}")
            
            socketio.emit('call_failed', {'reason': 'User is offline'}, room=request.sid)
    
    @socketio.on('answer_call')
    def handle_answer_call(data):
        """Callee answers the call"""
        callee_id = session.get('user_id')
        caller_id = data.get('caller_id')
        answer = data.get('answer')
        call_id = data.get('call_id')
        
        try:
            caller_id = int(caller_id)
        except (ValueError, TypeError):
            print(f"❌ Invalid caller_id: {caller_id}")
            return
        
        print(f"✅ Call answered by {callee_id} to {caller_id}")
        
        # UPDATE CALL STATUS TO ANSWERED
        if call_id:
            try:
                print(f"💾 Updating call {call_id} status to 'answered'")
                result = supabase.table('call_history').update({
                    'call_status': 'answered'
                }).eq('id', call_id).execute()
                print(f"✅ Call {call_id} marked as answered. Updated: {result.data}")
            except Exception as e:
                print(f"❌ Failed to update call status: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"⚠️ No call_id provided in answer_call")
        
        if caller_id in active_users:
            caller_socket = active_users[caller_id]
            socketio.emit('call_answered', {
                'callee_id': callee_id,
                'answer': answer,
                'call_id': call_id
            }, room=caller_socket)
        else:
            print(f"❌ Caller {caller_id} not in active_users")
    
    @socketio.on('ice_candidate')
    def handle_ice_candidate(data):
        """Exchange ICE candidates"""
        sender_id = session.get('user_id')
        recipient_id = data.get('recipient_id')
        candidate = data.get('candidate')
        
        try:
            recipient_id = int(recipient_id)
        except (ValueError, TypeError):
            print(f"❌ Invalid recipient_id: {recipient_id}")
            return
        
        if recipient_id in active_users:
            recipient_socket = active_users[recipient_id]
            socketio.emit('ice_candidate', {
                'sender_id': sender_id,
                'candidate': candidate
            }, room=recipient_socket)
    
    @socketio.on('hang_up')
    def handle_hang_up(data):
        """End the call"""
        user_id = session.get('user_id')
        other_user_id = data.get('other_user_id')
        call_id = data.get('call_id')
        duration = data.get('duration', 0)
        
        try:
            other_user_id = int(other_user_id)
        except (ValueError, TypeError):
            print(f"❌ Invalid other_user_id: {other_user_id}")
            return
        
        print(f"📴 Hang up from {user_id} to {other_user_id}")
        print(f"📊 Call ID: {call_id}, Duration: {duration}s")
        
        # UPDATE CALL HISTORY WITH DURATION
        if call_id:
            try:
                print(f"💾 Updating call {call_id} with duration {duration}s")
                result = supabase.table('call_history').update({
                    'call_status': 'completed',
                    'call_duration': duration,
                    'ended_at': datetime.utcnow().isoformat()
                }).eq('id', call_id).execute()
                print(f"✅ Call {call_id} updated with duration. Result: {result.data}")
            except Exception as e:
                print(f"❌ FAILED to update call history: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"⚠️ No call_id provided in hang_up - cannot save duration!")
        
        if other_user_id in active_users:
            other_socket = active_users[other_user_id]
            socketio.emit('call_ended', {'user_id': user_id}, room=other_socket)
        else:
            print(f"⚠️ User {other_user_id} already disconnected")



''''
# SocketIO event handlers

#This code fails to record calls in rhe database 


def register_socketio_events(socketio):
    """Register WebSocket events for calling"""
    
    @socketio.on('connect')
    def handle_connect():
        user_id = session.get('user_id')
        if user_id:
            active_users[user_id] = request.sid
            print(f"✅ User {user_id} connected with socket {request.sid}")
            print(f"📋 Active users: {list(active_users.keys())}")
        else:
            print(f"⚠️ Connection without user_id")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        user_id = session.get('user_id')
        if user_id and user_id in active_users:
            del active_users[user_id]
            print(f"❌ User {user_id} disconnected")
            print(f"📋 Active users: {list(active_users.keys())}")
    
    @socketio.on('call_user')
    def handle_call_user(data):
        """Initiate call to another user"""
        caller_id = session.get('user_id')
        callee_id = data.get('callee_id')
        offer = data.get('offer')
        
        try:
            callee_id = int(callee_id)
        except (ValueError, TypeError):
            print(f"❌ Invalid callee_id: {callee_id}")
            socketio.emit('call_failed', {'reason': 'Invalid user ID'}, room=request.sid)
            return
        
        print(f"📞 Call from {caller_id} to {callee_id}")
        
        if not caller_id or not callee_id:
            return
        
        # Create call history record
        try:
            call_record = supabase.table('call_history').insert({
                'caller_id': caller_id,
                'callee_id': callee_id,
                'call_status': 'initiated'
            }).execute()
            
            call_id = call_record.data[0]['id'] if call_record.data else None
        except Exception as e:
            print(f"⚠️ Failed to create call history: {e}")
            call_id = None
        
        # Get caller username
        try:
            caller = supabase.table('user').select('username').eq('id', caller_id).execute()
            caller_username = caller.data[0]['username'] if caller.data else 'Unknown'
        except Exception as e:
            print(f"⚠️ Error fetching caller username: {e}")
            caller_username = 'Unknown'
        
        if callee_id in active_users:
            callee_socket = active_users[callee_id]
            print(f"✅ Sending call to {callee_id} at socket {callee_socket}")
            socketio.emit('incoming_call', {
                'caller_id': caller_id,
                'caller_username': caller_username,
                'offer': offer,
                'call_id': call_id
            }, room=callee_socket)
        else:
            print(f"❌ User {callee_id} is offline")
            
            # Update call as failed
            if call_id:
                supabase.table('call_history').update({
                    'call_status': 'failed',
                    'ended_at': datetime.utcnow().isoformat()
                }).eq('id', call_id).execute()
            
            socketio.emit('call_failed', {'reason': 'User is offline'}, room=request.sid)
    
    @socketio.on('answer_call')
    def handle_answer_call(data):
        """Callee answers the call"""
        callee_id = session.get('user_id')
        caller_id = data.get('caller_id')
        answer = data.get('answer')
        call_id = data.get('call_id')
        
        try:
            caller_id = int(caller_id)
        except (ValueError, TypeError):
            print(f"❌ Invalid caller_id: {caller_id}")
            return
        
        print(f"✅ Call answered by {callee_id} to {caller_id}")
        
        # Update call status
        if call_id:
            try:
                supabase.table('call_history').update({
                    'call_status': 'answered'
                }).eq('id', call_id).execute()
            except Exception as e:
                print(f"⚠️ Failed to update call status: {e}")
        
        if caller_id in active_users:
            caller_socket = active_users[caller_id]
            socketio.emit('call_answered', {
                'callee_id': callee_id,
                'answer': answer,
                'call_id': call_id
            }, room=caller_socket)
        else:
            print(f"❌ Caller {caller_id} not in active_users")
    
    @socketio.on('ice_candidate')
    def handle_ice_candidate(data):
        """Exchange ICE candidates"""
        sender_id = session.get('user_id')
        recipient_id = data.get('recipient_id')
        candidate = data.get('candidate')
        
        try:
            recipient_id = int(recipient_id)
        except (ValueError, TypeError):
            print(f"❌ Invalid recipient_id: {recipient_id}")
            return
        
        if recipient_id in active_users:
            recipient_socket = active_users[recipient_id]
            socketio.emit('ice_candidate', {
                'sender_id': sender_id,
                'candidate': candidate
            }, room=recipient_socket)
    
    @socketio.on('hang_up')
    def handle_hang_up(data):
        """End the call"""
        user_id = session.get('user_id')
        other_user_id = data.get('other_user_id')
        call_id = data.get('call_id')
        duration = data.get('duration', 0)
        
        try:
            other_user_id = int(other_user_id)
        except (ValueError, TypeError):
            print(f"❌ Invalid other_user_id: {other_user_id}")
            return
        
        print(f"📴 Hang up from {user_id} to {other_user_id}, duration: {duration}s")
        
        # Update call history
        if call_id:
            try:
                supabase.table('call_history').update({
                    'call_status': 'completed',
                    'call_duration': duration,
                    'ended_at': datetime.utcnow().isoformat()
                }).eq('id', call_id).execute()
            except Exception as e:
                print(f"⚠️ Failed to update call history: {e}")
        
        if other_user_id in active_users:
            other_socket = active_users[other_user_id]
            socketio.emit('call_ended', {'user_id': user_id}, room=other_socket)

''' 






@call_bp.route('/debug/call-history')
def debug_call_history():
    """Debug: See all call history records"""
    user_id = session.get('user_id')
    if not user_id:
        return "Not logged in", 401
    
    try:
        # Get ALL calls for this user
        all_calls = supabase.table('call_history')\
            .select('*')\
            .or_(f'caller_id.eq.{user_id},callee_id.eq.{user_id}')\
            .order('started_at', desc=True)\
            .execute()
        
        html = f"<h2>Call History Debug</h2>"
        html += f"<p>User ID: {user_id}</p>"
        html += f"<p>Total Calls: {len(all_calls.data)}</p><hr>"
        
        if all_calls.data:
            for call in all_calls.data:
                html += f"<div style='border:1px solid #ccc; padding:10px; margin:10px 0;'>"
                html += f"<strong>Call ID:</strong> {call['id']}<br>"
                html += f"<strong>Caller ID:</strong> {call['caller_id']}<br>"
                html += f"<strong>Callee ID:</strong> {call['callee_id']}<br>"
                html += f"<strong>Status:</strong> {call['call_status']}<br>"
                html += f"<strong>Duration:</strong> {call.get('call_duration', 0)} seconds<br>"
                html += f"<strong>Started:</strong> {call['started_at']}<br>"
                html += f"<strong>Ended:</strong> {call.get('ended_at', 'N/A')}<br>"
                html += f"</div>"
        else:
            html += "<p><strong>NO CALL HISTORY FOUND!</strong></p>"
        
        return html
    except Exception as e:
        return f"Error: {str(e)}", 500