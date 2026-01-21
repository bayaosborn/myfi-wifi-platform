"""
MyFi Local Business Directory Routes
app/routes/directory.py

Simple directory for merchants like Sherryl (Monique Botique)
"""

from flask import Blueprint, request, jsonify, render_template, session, redirect
from app.backend.supabase_client import supabase
from datetime import datetime, time as dt_time
import pytz

directory_bp = Blueprint('directory', __name__, url_prefix='/directory')


# ==================== PUBLIC ROUTES ====================

@directory_bp.route('/')
def directory_home():
    """Public directory page - browse all businesses"""
    return render_template('directory/browse.html')


@directory_bp.route('/merchant/<merchant_id>')
def merchant_detail(merchant_id):
    """Public merchant profile page"""
    try:
        merchant = supabase.select('merchants', filters={'id': merchant_id})
        
        if not merchant or not merchant[0].get('is_active'):
            return "Merchant not found", 404
        
        merchant_data = merchant[0]
        
        # Get products
        products = supabase.select('merchant_products', filters={'merchant_id': merchant_id})
        
        return render_template('directory/merchant/merchant.html', 
                             merchant=merchant_data,
                             products=products or [])
        
    except Exception as e:
        print(f"❌ Error loading merchant: {e}")
        return "Error loading merchant", 500


# ==================== API ROUTES (For Logic) ====================

@directory_bp.route('/api/search', methods=['POST'])
def search_merchants():
    """
    Search for available merchants
    
    POST /directory/api/search
    {
        "category": "soap",
        "status": "OPEN",
        "stock_status": "IN_STOCK"
    }
    """
    try:
        data = request.get_json() or {}
        
        category = data.get('category')
        status = data.get('status', 'OPEN')
        stock_status = data.get('stock_status', 'IN_STOCK')
        
        # Get all active merchants
        merchants = supabase.select('merchants', filters={'is_active': True})
        
        # Filter by criteria
        filtered = []
        for m in merchants:
            # Check category
            if category and m.get('category') != category:
                continue
            
            # Check status
            if m.get('status') != status:
                continue
            
            # Check stock
            if m.get('stock_status') != stock_status:
                continue
            
            filtered.append(m)
        
        return jsonify({
            'success': True,
            'count': len(filtered),
            'merchants': filtered
        }), 200
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@directory_bp.route('/api/merchants/<merchant_id>', methods=['GET'])
def get_merchant(merchant_id):
    """Get merchant details"""
    try:
        merchant = supabase.select('merchants', filters={'id': merchant_id})
        
        if not merchant:
            return jsonify({'success': False, 'error': 'Merchant not found'}), 404
        
        return jsonify({
            'success': True,
            'merchant': merchant[0]
        }), 200
        
    except Exception as e:
        print(f"❌ Get merchant error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@directory_bp.route('/api/check-availability/<merchant_id>', methods=['GET'])
def check_availability(merchant_id):
    """
    Check if merchant is currently available
    
    Returns:
        {
            "available": true/false,
            "status": "OPEN/CLOSED",
            "stock_status": "IN_STOCK/OUT_OF_STOCK",
            "message": "..."
        }
    """
    try:
        merchant = supabase.select('merchants', filters={'id': merchant_id})
        
        if not merchant or not merchant[0].get('is_active'):
            return jsonify({
                'available': False,
                'status': 'INACTIVE',
                'stock_status': 'OUT_OF_STOCK',
                'message': 'Merchant not found or inactive'
            }), 404
        
        m = merchant[0]
        
        # Check if open
        is_open = m.get('status') == 'OPEN'
        
        # Check if in stock
        has_stock = m.get('stock_status') == 'IN_STOCK'
        
        # Check operating hours (optional)
        within_hours = _check_operating_hours(m)
        
        available = is_open and has_stock and within_hours
        
        # Build message
        if not is_open:
            message = f"{m['business_name']} is currently closed"
        elif not has_stock:
            message = f"{m['business_name']} is out of stock"
        elif not within_hours:
            message = f"{m['business_name']} is outside operating hours"
        else:
            message = f"{m['business_name']} is available"
        
        return jsonify({
            'available': available,
            'status': m.get('status'),
            'stock_status': m.get('stock_status'),
            'message': message,
            'business_name': m['business_name'],
            'contact_phone': m.get('contact_phone')
        }), 200
        
    except Exception as e:
        print(f"❌ Availability check error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== MERCHANT DASHBOARD ====================



@directory_bp.route('/merchant/dashboard')
def merchant_dashboard():
    """
    Merchant dashboard resolved via logged-in user
    No merchant_id in URL
    """

    user_id = session.get('user_id')

    if not user_id:
        return render_template('auth/login.html')

    try:
        # 🔑 Resolve merchant using user ID
        merchant = supabase.select(
            'merchants',
            filters={'profile_user_id': user_id}
        )

        # If user has no merchant yet → onboard
        if not merchant:
            return redirect('/directory/merchant/onboard')

        merchant = merchant[0]

        # Cache for later routes (optional)
        session['merchant_id'] = merchant['id']

        # Load merchant data
        orders = supabase.select(
            'merchant_orders',
            filters={'merchant_id': merchant['id']}
        )

        return render_template(
            'directory/merchant/dashboard.html',
            merchant=merchant,
            orders=orders or []
        )

    except Exception as e:
        print(f"❌ Merchant dashboard error: {e}")
        return "Error loading merchant dashboard", 500








@directory_bp.route('/merchant/dashboard/me')
def merchant_dashboard_me():
    """Merchant's own dashboard (simple auth via session for now)"""
    
    merchant_id = session.get('merchant_id')
    
    if not merchant_id:
        return redirect('/directory/merchant/login')
    
    try:
        merchant = supabase.select('merchants', filters={'id': merchant_id})
        
        if not merchant:
            return "Merchant not found", 404
            
        
        # Get recent orders
        orders = supabase.select('merchant_orders', filters={'merchant_id': merchant_id})
        
        return render_template('directory/merchant/dashboard.html',
                             merchant=merchant[0],
                             orders=orders or [])
        
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        return "Error loading dashboard", 500


@directory_bp.route('/merchant/update-status', methods=['POST'])
def update_status():
    """Merchant updates their status (OPEN/CLOSED, IN_STOCK/OUT_OF_STOCK)"""
    merchant_id = session.get('merchant_id')
    
    if not merchant_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
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


@directory_bp.route('/merchant/products', methods=['GET', 'POST'])
def manage_products():
    """Add/update products"""
    merchant_id = session.get('merchant_id')
    
    if not merchant_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    if request.method == 'GET':
        # List products
        products = supabase.select('merchant_products', filters={'merchant_id': merchant_id})
        return jsonify({'success': True, 'products': products or []}), 200
    
    elif request.method == 'POST':
        # Add product
        try:
            data = request.get_json()
            
            product_data = {
                'merchant_id': merchant_id,
                'product_name': data.get('product_name'),
                'product_description': data.get('product_description'),
                'category': data.get('category'),
                'is_available': data.get('is_available', True),
                'price': data.get('price'),
                'currency': 'KES'
            }
            
            result = supabase.insert('merchant_products', product_data)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': 'Product added',
                    'product': result['data'][0]
                }), 201
            else:
                return jsonify({'success': False, 'error': 'Insert failed'}), 400
            
        except Exception as e:
            print(f"❌ Add product error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500


# ==================== ONBOARDING ====================

@directory_bp.route('/merchant/onboard', methods=['GET', 'POST'])
def merchant_onboard():
    """Simple merchant onboarding"""
    if request.method == 'GET':
        return render_template('directory/merchant/onboard.html')
    
    elif request.method == 'POST':
        try:
            data = request.get_json()

            user_id = session.get('user_id')
            
            merchant_data = {
                   'profile_user_id': user_id,
                'business_name': data.get('business_name'),
                'owner_name': data.get('owner_name'),
                'owner_phone': data.get('owner_phone'),
                'category': data.get('category'),
                'subcategory': data.get('subcategory'),
                'description': data.get('description'),
                'contact_phone': data.get('contact_phone') or data.get('owner_phone'),
                'contact_email': data.get('contact_email'),
                'status': 'CLOSED',  # Start closed
                'stock_status': 'OUT_OF_STOCK',  # Start out of stock
                'is_active': True
            }
            
            result = supabase.insert('merchants', merchant_data)
            
            if result['success']:
                merchant = result['data'][0]
                
                # Set session (simple auth for now)
                session['merchant_id'] = merchant['id']
                
                return jsonify({
                    'success': True,
                    'message': 'Welcome to MyFi Directory!',
                    'merchant_id': merchant['id']
                }), 201
            else:
                return jsonify({'success': False, 'error': result.get('error')}), 400
            
        except Exception as e:
            print(f"❌ Onboarding error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500


# ==================== HELPER FUNCTIONS ====================

def _check_operating_hours(merchant):
    """Check if merchant is within operating hours"""
    try:
        opens_at = merchant.get('opens_at')
        closes_at = merchant.get('closes_at')
        
        if not opens_at or not closes_at:
            return True  # No hours set, assume always open
        
        # Get current time in EAT
        eat_tz = pytz.timezone('Africa/Nairobi')
        now = datetime.now(eat_tz).time()
        
        # Parse times
        if isinstance(opens_at, str):
            opens_at = dt_time.fromisoformat(opens_at)
        if isinstance(closes_at, str):
            closes_at = dt_time.fromisoformat(closes_at)
        
        return opens_at <= now <= closes_at
        
    except Exception as e:
        print(f"⚠️ Hours check error: {e}")
        return True  # Default to open if check fails