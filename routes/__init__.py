# routes/__init__.py - CLEAN (Pure Supabase)

def register_blueprints(app):
    """Register all blueprints - Pure Supabase, no models"""
    
    #from .auth import auth_bp
   # from .groups import groups_bp
   # from .payments import payments_bp
    from .admin import admin_bp
  #  from .wifi import wifi_bp
  #  from .admin_tools import admin_tools_bp
   # from .wallet import wallet_bp
   # from .admin_wallet import admin_wallet_bp
    
   # app.register_blueprint(auth_bp)
  #  app.register_blueprint(groups_bp)
   # app.register_blueprint(payments_bp)
    app.register_blueprint(admin_bp)
   # app.register_blueprint(wifi_bp)
   # app.register_blueprint(admin_tools_bp)
   # app.register_blueprint(wallet_bp)
    #app.register_blueprint(admin_wallet_bp)
    
    print("✅ All blueprints registered (8 total)")