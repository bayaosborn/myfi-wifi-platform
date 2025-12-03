"""
MyFi - Logic First Implementation
Copyright (c) 2025 MyFi. All rights reserved.

Simple Flask app focused on Logic AI.
SocketIO will be added later for WebRTC calls.
"""

from flask import Flask, render_template, jsonify
from datetime import timedelta
import os
from dotenv import load_dotenv


from flask import send_from_directory



#from flask import Flask, request, jsonify, render_template
import csv
import io
from app.backend.database import (
    get_all_contacts, 
    get_contact_by_id, 
    create_contact, 
    update_contact, 
    delete_contact,
    search_contacts,
    get_contacts_by_tag,
    bulk_insert_contacts
)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(
    __name__,
    template_folder='app/templates',
    static_folder='app/static'
)

# Session configuration
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-CHANGE-THIS')
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set True in production with HTTPS

# Register blueprints
from app.routes import register_blueprints
register_blueprints(app)

# Routes
@app.route('/')
def index():
    """Main Logic chat interface"""
    return render_template('index.html')  # Your chat UI


@app.route('/logic')
def logic():
    """Logic Chat page"""
    return render_template('logic.html')





# Service Worker
@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('app/static', 'service-worker.js', mimetype='application/javascript')

# Manifest
@app.route('/manifest.json')
def manifest():
    return send_from_directory('app/static', 'manifest.json', mimetype='application/json')





@app.route('/settings')
def settings():

    return render_template('settings.html')

@app.route('/contacts')
def contacts():
    return render_template('contacts.html')



@app.route('/health')
def health_check():
    """Health check for monitoring"""
    return jsonify({
        "status": "healthy",
        "service": "myfi-logic",
        "version": "1.0.0"
    }), 200


@app.errorhandler(404)
def not_found(error):
    """404 handler"""
    return jsonify({
        "error": "Not found",
        "message": "The requested resource does not exist"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500 handler"""
    return jsonify({
        "error": "Internal server error",
        "message": "Something went wrong. Please try again."
    }), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    ''''
    print(f"""
    ╔═══════════════════════════════════════╗
    ║   MyFi Logic AI Server                ║
    ║   Port: {port}                        ║
    ║   Debug: {debug}                      ║
    ╚═══════════════════════════════════════╝
    """)
    '''
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )