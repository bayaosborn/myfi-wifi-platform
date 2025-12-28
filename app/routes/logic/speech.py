# app/routes/logic_speech.py

from flask import Blueprint, request, jsonify
from groq import Groq
import os

logic_speech_bp = Blueprint('logic_speech', __name__, url_prefix='/api/logic')

groq = Groq(api_key=os.getenv('GROQ_API_KEY'))

@logic_speech_bp.route('/speech', methods=['POST'])
def transcribe_speech():
    """
    Transcribe audio using Groq Whisper API
    Fallback for browsers without Web Speech support
    """
    try:
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': 'No audio file'}), 400
        
        audio_file = request.files['audio']
        
        # Call Groq Whisper
        transcription = groq.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3",
            language="en"
        )
        
        text = transcription.text.strip()
        
        return jsonify({
            'success': True,
            'text': text
        }), 200
        
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500