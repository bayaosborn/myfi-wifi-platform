"""
Logic Routes - AI Chat Interface
Updated for phone authentication (no access_token)
"""

from flask import Blueprint, request, jsonify, session, redirect
from functools import wraps
from app.logic.engine import get_logic_engine

logic_bp = Blueprint('logic', __name__, url_prefix='/api/logic')

# ==================== HELPER ====================

def login_required(f):
    """
    Protect routes - user must be logged in
    Phone authentication compatible (only checks user_id)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# ==================== ROUTES ====================

@logic_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """
    Main Logic AI chat endpoint
    
    REQUEST:
        POST /api/logic/chat
        {
            "message": "Call Sarah"
        }
    
    RESPONSE:
        {
            "success": true,
            "message": "Calling Sarah...",
            "hidden_commands": [
                {
                    "action": "call",
                    "contact_id": "abc-123",
                    "contact_name": "Sarah",
                    "phone": "0742107097"
                }
            ]
        }
    
    HOW IT WORKS:
    1. Get user_id from session (phone auth)
    2. Get message from request body
    3. Create Logic engine for this user
    4. Process message with AI
    5. Return response + hidden commands for frontend
    """
    try:
        # 1. Get user info from session
        user_id = session.get('user_id')
        
        # 2. Get request data
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
        
        message = data['message'].strip()
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'Message cannot be empty'
            }), 400
        
        print(f"💬 Logic chat from user {user_id[:8]}: {message[:50]}...")
        
        # 3. Create Logic engine for this user
        # Note: get_logic_engine now only needs user_id (no access_token)
        engine = get_logic_engine(user_id)
        
        # 4. Process message with AI
        result = engine.chat(message)
        
        print(f"✅ Logic response: {result['response'][:50]}...")
        if result.get('hidden_commands'):
            print(f"🎯 Hidden commands: {len(result['hidden_commands'])}")
        
        # 5. Return response
        return jsonify({
            'success': True,
            'message': result['response'],
            'hidden_commands': result.get('hidden_commands', [])
        }), 200
        
    except Exception as e:
        print(f"❌ Chat error: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': 'Something went wrong. Please try again.'
        }), 500

@logic_bp.route('/history', methods=['GET'])
@login_required
def get_chat_history():
    """
    Get user's Logic chat history
    Optional endpoint for displaying past conversations
    """
    try:
        user_id = session.get('user_id')
        
        # Get chat history from Logic engine
        engine = get_logic_engine(user_id)
        history = engine.get_history()
        
        return jsonify({
            'success': True,
            'history': history
        }), 200
        
    except Exception as e:
        print(f"❌ History error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load history'
        }), 500

@logic_bp.route('/clear-history', methods=['POST'])
@login_required
def clear_history():
    """
    Clear user's Logic chat history
    Optional endpoint for privacy
    """
    try:
        user_id = session.get('user_id')
        
        # Clear history in Logic engine
        engine = get_logic_engine(user_id)
        engine.clear_history()
        
        return jsonify({
            'success': True,
            'message': 'Chat history cleared'
        }), 200
        
    except Exception as e:
        print(f"❌ Clear history error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to clear history'
        }), 500