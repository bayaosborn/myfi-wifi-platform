"""
MyFi Routes Package
Copyright (c) 2025 MyFi. All rights reserved.

Registers all blueprints.
"""

def register_blueprints(app):
    """
    Register all blueprints with the Flask app.
    
    Currently registered:
    - auth_bp: Authentication (login, signup, logout)
    - logic_bp: Logic AI assistant
    
    To add later:
    - call_bp: WebRTC calling
    - airdrop_bp: Contact sharing
    """

    # Import blueprints
    from app.routes.auth import auth_bp
    from app.routes.contacts.contacts import contacts_bp
    from app.routes.contacts.cImport import cont_import_bp
    from app.routes.contacts.merge import cont_merge_bp
    
    from app.routes.logic.logic import logic_bp
    from app.routes.interactions import interactions_bp
    #from app.routes.pages import pages_bp
    from app.routes.logic.speech import logic_speech_bp
    from app.logic.contacts.routes import logic_contacts_bp
    from app.routes.notes.routes import notes_bp
    from app.routes.call.call_routes import call_bp
    

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(contacts_bp)
    # app.register_blueprint(contacts_import_bp)
    app.register_blueprint(cont_import_bp)
    app.register_blueprint(cont_merge_bp)

    app.register_blueprint(logic_bp)
    app.register_blueprint(interactions_bp)
    #app.register_blueprint(pages_bp)
    app.register_blueprint(logic_speech_bp)
    app.register_blueprint(logic_contacts_bp)
    app.register_blueprint(notes_bp)
    app.register_blueprint(call_bp)
    

    # Debug prints (optional)
    # print("✅ Registered blueprints:")
    # print("   - auth_bp (authentication)")
    # print("   - logic_bp (AI assistant)")
    # print("   - addCustomContact_bp (custom contacts)")