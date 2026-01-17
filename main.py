"""
MyFi - Logic First Implementation with WebRTC Calls
Copyright (c) 2025 MyFi. All rights reserved.

Flask app with SocketIO for real-time calling.
"""

from flask import Flask, render_template, jsonify, session, redirect, send_from_directory
from flask_socketio import SocketIO
from datetime import timedelta
import os
from dotenv import load_dotenv

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

# Initialize SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    logger=False,  # Set True for debugging
    engineio_logger=False  # Set True for debugging
)

print("✅ SocketIO initialized")

# Register blueprints
from app.routes import register_blueprints
register_blueprints(app)

# Register SocketIO events for calls
try:
    from app.routes.call.call_routes import register_socketio_events
    register_socketio_events(socketio)
    print("✅ SocketIO events registered")
except Exception as e:
    print(f"⚠️ Could not register SocketIO events: {e}")

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Main app route"""
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('index.html')


@app.route('/logic')
def logic():
    """Logic Chat page"""
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('logic.html')


@app.route('/settings')
def settings():
    """Settings page"""
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('settings.html')


@app.route('/contacts')
def contacts():
    """Contacts page"""
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('contacts.html')


# ==================== PWA ROUTES ====================

@app.route('/service-worker.js')
def service_worker():
    """Serve service worker"""
    return send_from_directory('app/static', 'service-worker.js', mimetype='application/javascript')


@app.route('/manifest.json')
def manifest():
    """Serve manifest"""
    return send_from_directory('app/static', 'manifest.json', mimetype='application/manifest+json')


@app.route('/offline.html')
def offline():
    """Offline fallback page"""
    return render_template('offline.html')


@app.route('/api/pwa/status', methods=['GET'])
def pwa_status():
    """PWA status endpoint"""
    return jsonify({
        'pwa_enabled': True,
        'version': '2.2.0',
        'cache_name': 'myfi-v2.2.0'
    })


# ==================== HEALTH CHECK ====================

@app.route('/health')
def health_check():
    """Health check for monitoring"""
    return jsonify({
        "status": "healthy",
        "service": "myfi",
        "version": "2.2.0",
        "socketio": True
    }), 200


# ==================== ERROR HANDLERS ====================

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


# ==================== RUN ====================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"""
    ╔═══════════════════════════════════════╗
    ║   MyFi v2.2 - Logic + Calls           ║
    ║   Port: {port}                        ║
    ║   Debug: {debug}                      ║
    ║   SocketIO: Enabled                   ║
    ╚═══════════════════════════════════════╝
    """)
    
    # Use socketio.run instead of app.run
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True  # For development only
    )