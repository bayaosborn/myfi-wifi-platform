"""
Merchant Dashboard Routes
app/routes/merchant_dashboard.py

Dashboard view and status updates
"""

from flask import Blueprint, request, jsonify, render_template, session, redirect
from app.backend.supabase_client import supabase

merchant_dashboard_bp = Blueprint('merchant_dashboard', __name__, url_prefix='/directory/merchant')


@merchant_dashboard_bp.route('/dashboard')
def dashboard():
    """
    Merchant dashboard resolved via logged-in user
    No merchant_id in URL
    """
    user_id = session.get('user_id')

    if not user_id:
        return redirect('/auth/login')

    try:
        # Resolve merchant using user ID
        merchant = supabase.select(
            'merchants',
            filters={'profile_user_id': user_id}
        )

        # If user has no merchant yet → onboard
        if not merchant:
            return redirect('/directory/merchant/onboard')

        merchant = merchant[0]

        # Cache for later routes
        session['merchant_id'] = merchant['id']

        # Load orders
        orders = supabase.select(
            'merchant_orders',
            filters={'merchant_id': merchant['id']}
        )
        
        # Count products
        products = supabase.select(
            'merchant_products',
            filters={'merchant_id': merchant['id']}
        )
        products_count = len(products) if products else 0

        return render_template(
            'directory/merchant/dashboard.html',
            merchant=merchant,
            orders=orders or [],
            products_count=products_count
        )

    except Exception as e:
        print(f"❌ Merchant dashboard error: {e}")
        return "Error loading merchant dashboard", 500


@merchant_dashboard_bp.route('/update-status', methods=['POST'])
def update_status():
    """Update merchant status (OPEN/CLOSED, IN_STOCK/OUT_OF_STOCK)"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        # Get merchant
        merchant = supabase.select('merchants', filters={'profile_user_id': user_id})
        
        if not merchant:
            return jsonify({'success': False, 'error': 'Merchant not found'}), 404
        
        merchant_id = merchant[0]['id']
        data = request.get_json()
        
        updates = {}
        
        if 'status' in data:
            if data['status'] in ['OPEN', 'CLOSED', 'TEMPORARILY_CLOSED']:
                updates['status'] = data['status']
        
        if 'stock_status' in data:
            if data['stock_status'] in ['IN_STOCK', 'OUT_OF_STOCK', 'LIMITED_STOCK']:
                updates['stock_status'] = data['stock_status']
        
        if not updates:
            return jsonify({'success': False, 'error': 'No valid updates'}), 400
        
        # Update merchant
        success = supabase.update('merchants', {'id': merchant_id}, updates)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Status updated successfully'
            }), 200
        else:
            return jsonify({'success': False, 'error': 'Update failed'}), 400
        
    except Exception as e:
        print(f"❌ Update status error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500