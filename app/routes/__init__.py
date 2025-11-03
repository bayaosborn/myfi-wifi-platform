# routes/__init__.py - CLEAN (Pure Supabase)

def register_blueprints(app):
    """Register all blueprints - Pure Supabase, no models"""
    
    from .auth import auth_bp
   # from .groups import groups_bp
    from .payments import payments_bp
    from .admin import admin_bp
    from .wifi import wifi_bp
    from .admin_tools import admin_tools_bp
    from .wallet import wallet_bp
    from .admin_wallet import admin_wallet_bp
    from .mpesa import mpesa_bp
    from .manual_payment import manual_payment_bp
    from .cron import cron_bp
   # from routes.location import location_bp
    from app.routes.notifications import notifications_bp
    from app.routes.call_routes import call_bp

#def register_blueprints(app):
    # ... your existing blueprints
    



    
    app.register_blueprint(auth_bp)
   # app.register_blueprint(groups_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(wifi_bp)
    app.register_blueprint(admin_tools_bp)
    app.register_blueprint(wallet_bp)
    app.register_blueprint(admin_wallet_bp)
    app.register_blueprint(mpesa_bp, url_prefix='/api/mpesa')
    app.register_blueprint(manual_payment_bp)
    app.register_blueprint(cron_bp) 
    print("✅ All blueprints registered (8 total)")
   # app.register_blueprint(location_bp)

    app.register_blueprint(notifications_bp)
    app.register_blueprint(call_bp)