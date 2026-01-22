"""
MyFi Local Business Directory - Main Routes
app/routes/directory.py

Public pages, API endpoints, and merchant onboarding
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
        "tags": ["handmade", "organic"],
        "status": "OPEN",
        "stock_status": "IN_STOCK"
    }
    """
    try:
        data = request.get_json() or {}
        
        category = data.get('category')
        tags = data.get('tags', [])
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
            
            # Check tags (if merchant has tags that match search tags)
            if tags:
                merchant_tags = m.get('tags') or []
                if not any(tag in merchant_tags for tag in tags):
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


# ==================== MERCHANT ONBOARDING ====================

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
                'tags': data.get('tags', []),  # Array of tags
                'description': data.get('description'),
                'contact_phone': data.get('contact_phone') or data.get('owner_phone'),
                'contact_email': data.get('contact_email'),
                'location': data.get('location'),
                'status': 'CLOSED',  # Start closed
                'stock_status': 'OUT_OF_STOCK',  # Start out of stock
                'is_active': True
            }
            
            result = supabase.insert('merchants', merchant_data)
            
            if result['success']:
                merchant = result['data'][0]
                
                # Set session
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
        opening_time = merchant.get('opening_time')
        closing_time = merchant.get('closing_time')
        
        if not opening_time or not closing_time:
            return True  # No hours set, assume always open
        
        # Get current time in EAT
        eat_tz = pytz.timezone('Africa/Nairobi')
        now = datetime.now(eat_tz).time()
        
        # Parse times
        if isinstance(opening_time, str):
            opening_time = dt_time.fromisoformat(opening_time)
        if isinstance(closing_time, str):
            closing_time = dt_time.fromisoformat(closing_time)
        
        return opening_time <= now <= closing_time
        
    except Exception as e:
        print(f"⚠️ Hours check error: {e}")
        return True  # Default to open if check fails