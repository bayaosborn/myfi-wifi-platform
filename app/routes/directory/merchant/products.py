"""
Merchant Products Routes
app/routes/merchant_products.py

Products and services management
"""

from flask import Blueprint, request, jsonify, render_template, session, redirect
from app.backend.supabase_client import supabase

merchant_products_bp = Blueprint('merchant_products', __name__, url_prefix='/directory/merchant')


@merchant_products_bp.route('/products')
def products_page():
    """Products management page"""
    user_id = session.get('user_id')

    if not user_id:
        return redirect('/auth/login')

    try:
        merchant = supabase.select(
            'merchants',
            filters={'profile_user_id': user_id}
        )

        if not merchant:
            return redirect('/directory/merchant/onboard')
        
        merchant_id = merchant[0]['id']
        
        # Get all products/services
        products = supabase.select(
            'merchant_products',
            filters={'merchant_id': merchant_id}
        )

        return render_template(
            'directory/merchant/products.html',
            merchant=merchant[0],
            products=products or []
        )

    except Exception as e:
        print(f"❌ Products page error: {e}")
        return "Error loading products", 500


@merchant_products_bp.route('/products/add', methods=['POST'])
def add_product():
    """Add new product or service"""
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
        
        product_data = {
            'merchant_id': merchant_id,
            'name': data.get('name'),
            'description': data.get('description'),
            'type': data.get('type', 'PRODUCT'),  # 'PRODUCT' or 'SERVICE'
            'price': data.get('price'),
            'currency': 'KES',
            'is_available': data.get('is_available', True),
            'delivery_required': data.get('delivery_required', True),
            'service_location': data.get('service_location'),  # For services
            'image_url': data.get('image_url'),
        }
        
        result = supabase.insert('merchant_products', product_data)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Product added successfully',
                'product': result['data'][0]
            }), 201
        else:
            return jsonify({'success': False, 'error': 'Insert failed'}), 400
        
    except Exception as e:
        print(f"❌ Add product error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@merchant_products_bp.route('/products/<product_id>/update', methods=['POST'])
def update_product(product_id):
    """Update existing product"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        # Verify ownership
        merchant = supabase.select('merchants', filters={'profile_user_id': user_id})
        
        if not merchant:
            return jsonify({'success': False, 'error': 'Merchant not found'}), 404
        
        merchant_id = merchant[0]['id']
        
        # Verify product belongs to merchant
        product = supabase.select('merchant_products', filters={'id': product_id, 'merchant_id': merchant_id})
        
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        data = request.get_json()
        updates = {}
        
        if 'name' in data:
            updates['name'] = data['name']
        if 'description' in data:
            updates['description'] = data['description']
        if 'price' in data:
            updates['price'] = data['price']
        if 'is_available' in data:
            updates['is_available'] = data['is_available']
        if 'delivery_required' in data:
            updates['delivery_required'] = data['delivery_required']
        if 'service_location' in data:
            updates['service_location'] = data['service_location']
        if 'image_url' in data:
            updates['image_url'] = data['image_url']
        
        success = supabase.update('merchant_products', {'id': product_id}, updates)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Product updated successfully'
            }), 200
        else:
            return jsonify({'success': False, 'error': 'Update failed'}), 400
        
    except Exception as e:
        print(f"❌ Update product error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@merchant_products_bp.route('/products/<product_id>/delete', methods=['POST'])
def delete_product(product_id):
    """Delete product"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        # Verify ownership
        merchant = supabase.select('merchants', filters={'profile_user_id': user_id})
        
        if not merchant:
            return jsonify({'success': False, 'error': 'Merchant not found'}), 404
        
        merchant_id = merchant[0]['id']
        
        # Verify product belongs to merchant
        product = supabase.select('merchant_products', filters={'id': product_id, 'merchant_id': merchant_id})
        
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        success = supabase.delete('merchant_products', {'id': product_id})
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Product deleted successfully'
            }), 200
        else:
            return jsonify({'success': False, 'error': 'Delete failed'}), 400
        
    except Exception as e:
        print(f"❌ Delete product error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500