"""
MyFi - Logic First Implementation
Copyright (c) 2025 MyFi. All rights reserved.

Simple Flask app focused on Logic AI.
SocketIO will be added later for WebRTC calls.
"""

from flask import Flask, render_template, jsonify, session, redirect
from datetime import timedelta
import os
from dotenv import load_dotenv



from flask import send_from_directory



#from flask import Flask, request, jsonify, render_template
import csv
import io

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




"""
Add these routes to your main.py or create a new blueprint
"""

from flask import send_from_directory, render_template

# Serve service worker (needed if Flask doesn't auto-serve static files)
@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js', mimetype='application/javascript')

# Serve manifest
@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/manifest+json')

# Offline fallback page
@app.route('/offline.html')
def offline():
    return render_template('offline.html')

# API endpoint to check PWA status
@app.route('/api/pwa/status', methods=['GET'])
def pwa_status():
    return jsonify({
        'pwa_enabled': True,
        'version': '1.0.0',
        'cache_name': 'myfi-v2.2.0'
    })








# Register blueprints
from app.routes import register_blueprints
register_blueprints(app)

# Routes
# Home route
@app.route('/')
def index():
    """Main L chat inte route"""
    # Check if user is authenticated
    if 'user_id' not in session:
        return redirect('/login')
    
    # User is authenticated, show the app
    return render_template('index.html')  # Your existing chat UI
    





# Your chat UI


@app.route('/logic')
def logic():
    """Logic Chat page"""
    return render_template('logic.html')












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
        "service": "myfi",
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