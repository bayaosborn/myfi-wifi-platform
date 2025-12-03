from flask import Blueprint, request, jsonify, session
#from supabase import create_client
import os

# Direct imports - logic is now a proper package under app/
from app.logic.engine import LogicEngine
#from app.logic.security import SecurityFilter
#from app.logic.q_engine import QueryQuotient

logic_bp = Blueprint('logic', __name__)


logic = LogicEngine()
#security = SecurityFilter()
#q_engine = QueryQuotient()

@logic_bp.route('/upload', methods=['POST'])
def upload_csv():
    """Upload and load contacts CSV/VCF"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'})
    
    file = request.files['file']
    
    if not file.filename.endswith(('.csv', '.vcf')):
        return jsonify({'success': False, 'error': 'File must be CSV/VCF'})
    
    try:
        # Read CSV
        content = file.read().decode('utf-8')
        count = logic.load_contacts(content)
        
        return jsonify({
            'success': True,
            'count': count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })





        

@logic_bp.route('/chat', methods=['POST'])
def chat():
    """Chat with Logic"""
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'success': False, 'error': 'Empty message'})
    
    if not logic.contacts:
        return jsonify({'success': False, 'error': 'No contacts loaded'})
    
    try:
        response = logic.chat(message)
        return jsonify({
            'success': True,
            'response': response
        })
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to process message'
        })




#adding contacts to database

