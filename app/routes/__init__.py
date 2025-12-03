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
    # from app.routes.auth import auth_bp
    from app.routes.logic_routes import logic_bp
    from app.routes.addCustomContact import addCustomContact_bp
  #  from app.routes.notes import notes_bp

    # Register blueprints
    # app.register_blueprint(auth_bp)
    app.register_blueprint(logic_bp)
    app.register_blueprint(addCustomContact_bp)
  #  app.register_blueprint(notes_bp)

    #print("✅ Registered blueprints:")
    # print("   - auth_bp (authentication)")
   # print("   - logic_bp (AI assistant)")
   # print("   - addCustomContact_bp (custom contacts)")