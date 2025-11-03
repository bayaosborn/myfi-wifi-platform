# app.py

from flask import Flask, render_template, jsonify
from datetime import timedelta
import os
from dotenv import load_dotenv
from flask import send_from_directory
from flask_socketio import SocketIO

load_dotenv()

#app = Flask(__name__)
app = Flask(
    __name__,
    template_folder='app/templates',
    static_folder='app/static'
)

# Session config
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-CHANGE-THIS')
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False

# Initialize SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    logger=True,
    engineio_logger=True
)

# Register blueprints
from app.routes import register_blueprints
register_blueprints(app)

# ⭐ ADD THIS LINE - Register SocketIO events for calls
from app.routes.call_routes import register_socketio_events
register_socketio_events(socketio)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/serviceworker.js')
def service_worker():
    return send_from_directory('app/static', 'serviceworker.js', mimetype='application/javascript')

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)



