"""
Interactions Tracking Routes
Logs user interactions with contacts
"""

from flask import Blueprint, request, jsonify, session
from functools import wraps
from app.backend.supabase_client import supabase
import uuid

interactions_bp = Blueprint('interactions', __name__, url_prefix='/api/interactions')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@interactions_bp.route('/log', methods=['POST'])
@login_required
def log_interaction():
    """
    Log an interaction
    
    Request:
        {
            "contact_id": "uuid",
            "type": "call|message|email",
            "source": "button|logic",
            "metadata": {}
        }
    """
    try:
        user_id = session.get('user_id')
        
        data = request.get_json()
        
        contact_id = data.get('contact_id')
        interaction_type = data.get('type')
        source = data.get('source', 'button')
        metadata = data.get('metadata', {})
        
        if not contact_id or not interaction_type:
            return jsonify({
                'success': False,
                'error': 'contact_id and type required'
            }), 400
        
        # Validate type
        valid_types = ['call', 'message', 'email']
        if interaction_type not in valid_types:
            return jsonify({
                'success': False,
                'error': f'Invalid type. Must be: {valid_types}'
            }), 400
        
        # Prepare interaction data
        interaction_data = {
            'id': str(uuid.uuid4()),  # ✅ GENERATE ID
            'user_id': user_id,
            'contact_id': contact_id,
            'interaction_type': interaction_type,
            'source': source
        }
        
        # Add optional fields
        if metadata.get('duration'):
            interaction_data['duration'] = metadata['duration']
        
        if metadata.get('subject') or metadata.get('notes'):
            interaction_data['notes'] = metadata.get('subject') or metadata.get('notes')
        
        print(f"📊 Logging interaction: {interaction_type} with contact {contact_id[:8]}...")
        
        # Insert into Supabase (without access_token)
        result = supabase.insert('interactions', interaction_data)
        
        if result['success']:
            print(f"✅ Interaction logged successfully")
            return jsonify({
                'success': True,
                'message': 'Interaction logged'
            }), 200
        else:
            print(f"❌ Insert failed: {result.get('error')}")
            return jsonify({
                'success': False,
                'error': result.get('error')
            }), 400
            
    except Exception as e:
        print(f"❌ Log interaction error: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@interactions_bp.route('/history', methods=['GET'])
@login_required
def get_history():
    """
    Get interaction history
    
    Query params:
        - limit: Number of interactions (default: 50)
        - contact_id: Filter by contact
        - type: Filter by type (call|message|email)
    """
    try:
        user_id = session.get('user_id')
        
        limit = int(request.args.get('limit', 50))
        contact_id = request.args.get('contact_id')
        interaction_type = request.args.get('type')
        
        # Build filters
        filters = {'user_id': user_id}
        if contact_id:
            filters['contact_id'] = contact_id
        if interaction_type:
            filters['interaction_type'] = interaction_type
        
        # Get interactions (without access_token)
        interactions = supabase.select('interactions', filters=filters)
        
        # Sort by date (newest first)
        interactions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Limit results
        interactions = interactions[:limit]
        
        return jsonify({
            'success': True,
            'interactions': interactions,
            'count': len(interactions)
        }), 200
        
    except Exception as e:
        print(f"❌ Get history error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'interactions': []
        }), 500

@interactions_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """
    Get interaction statistics
    
    Returns counts by type and source
    """
    try:
        user_id = session.get('user_id')
        
        # Get all interactions
        interactions = supabase.select('interactions', filters={'user_id': user_id})
        
        # Calculate stats
        stats = {
            'total': len(interactions),
            'by_type': {},
            'by_source': {},
            'by_contact': {}
        }
        
        for interaction in interactions:
            # By type
            itype = interaction.get('interaction_type', 'unknown')
            stats['by_type'][itype] = stats['by_type'].get(itype, 0) + 1
            
            # By source
            source = interaction.get('source', 'unknown')
            stats['by_source'][source] = stats['by_source'].get(source, 0) + 1
            
            # By contact (top 10)
            contact_id = interaction.get('contact_id')
            if contact_id:
                stats['by_contact'][contact_id] = stats['by_contact'].get(contact_id, 0) + 1
        
        # Sort by_contact by count
        sorted_contacts = sorted(
            stats['by_contact'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        stats['top_contacts'] = [
            {'contact_id': cid, 'count': count}
            for cid, count in sorted_contacts
        ]
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
        
    except Exception as e:
        print(f"❌ Get stats error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



