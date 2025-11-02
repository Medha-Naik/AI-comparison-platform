"""
Wishlist API endpoints
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Blueprint, request, jsonify
from services.wishlist_service import wishlist_service
from flask import session
from models import create_tables

# Create wishlist blueprint
wishlist_bp = Blueprint('wishlist', __name__)

# Initialize database tables
create_tables()

@wishlist_bp.route('/wishlist/add', methods=['POST'])
def add_to_wishlist():
    """Add a product to wishlist"""
    try:
        # Require session auth FIRST
        if not session.get('user_id'):
            return jsonify({"success": False, "message": "Authentication required"}), 401
        
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        # Only product_name is required now (email comes from session)
        if 'product_name' not in data:
            return jsonify({"success": False, "message": "Missing required field: product_name"}), 400

        # Use email from session (not from request body)
        result = wishlist_service.add_to_wishlist(
            user_email=session.get('user_email'),
            product_name=data['product_name'],
            product_category=data.get('product_category'),
            target_price=data.get('target_price')
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

@wishlist_bp.route('/wishlist/remove', methods=['POST'])
def remove_from_wishlist():
    """Remove a product from wishlist"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        # Require session auth
        if not session.get('user_id'):
            return jsonify({"success": False, "message": "Authentication required"}), 401

        required_fields = ['wishlist_item_id']
        for field in required_fields:
            if field not in data:
                return jsonify({"success": False, "message": f"Missing required field: {field}"}), 400
        
        result = wishlist_service.remove_from_wishlist(
            user_email=session.get('user_email'),
            wishlist_item_id=data['wishlist_item_id']
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

@wishlist_bp.route('/wishlist/me', methods=['GET'])
def get_wishlist():
    """Get user's wishlist"""
    try:
        if not session.get('user_id'):
            return jsonify({"success": False, "message": "Authentication required"}), 401
        wishlist = wishlist_service.get_wishlist(session.get('user_email'))
        return jsonify({
            "success": True,
            "wishlist": wishlist
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

@wishlist_bp.route('/wishlist/update-target-price', methods=['POST'])
def update_target_price():
    """Update target price for a wishlist item"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        # Require session auth
        if not session.get('user_id'):
            return jsonify({"success": False, "message": "Authentication required"}), 401

        required_fields = ['wishlist_item_id', 'target_price']
        for field in required_fields:
            if field not in data:
                return jsonify({"success": False, "message": f"Missing required field: {field}"}), 400
        
        result = wishlist_service.update_target_price(
            user_email=session.get('user_email'),
            wishlist_item_id=data['wishlist_item_id'],
            target_price=float(data['target_price'])
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

@wishlist_bp.route('/wishlist/update-prices', methods=['POST'])
def update_prices():
    """Update prices for all wishlist items"""
    try:
        result = wishlist_service.update_all_prices()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

@wishlist_bp.route('/wishlist/update-item-prices/<int:wishlist_item_id>', methods=['POST'])
def update_item_prices(wishlist_item_id):
    """Update prices for a specific wishlist item"""
    try:
        result = wishlist_service.update_prices_for_item(wishlist_item_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

@wishlist_bp.route('/wishlist/check/<product_name>', methods=['GET'])
def check_in_wishlist(product_name):
    """Check if a product is in user's wishlist"""
    try:
        # Require session auth
        if not session.get('user_id'):
            return jsonify({"success": False, "message": "Authentication required"}), 401
        
        # Use email from session
        user_email = session.get('user_email')
        if not user_email:
            return jsonify({"success": False, "message": "User email not found in session"}), 401
        
        wishlist = wishlist_service.get_wishlist(user_email)
        
        for item in wishlist:
            if item['product_name'].lower() == product_name.lower():
                return jsonify({
                    "success": True,
                    "in_wishlist": True,
                    "wishlist_item": item
                }), 200
        
        return jsonify({
            "success": True,
            "in_wishlist": False
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500
    
@wishlist_bp.route('/wishlist/details/<int:wishlist_item_id>', methods=['GET'])
def get_wishlist_item_details(wishlist_item_id):
    """Get detailed information and price history for a wishlist item"""
    try:
        if not session.get('user_id'):
            return jsonify({"success": False, "message": "Authentication required"}), 401
        
        from models import get_db, WishlistItem, PriceHistory
        from datetime import datetime, timedelta
        
        db = next(get_db())
        try:
            # Get wishlist item
            item = db.query(WishlistItem).filter(
                WishlistItem.id == wishlist_item_id,
                WishlistItem.user_id == session.get('user_id')
            ).first()
            
            if not item:
                return jsonify({"success": False, "message": "Wishlist item not found"}), 404
            
            # Get latest price for each store (for current prices display)
            all_prices = db.query(PriceHistory).filter(
                PriceHistory.wishlist_item_id == wishlist_item_id
            ).order_by(PriceHistory.recorded_at.desc()).all()
            
            # Get the latest price for each store
            current_prices = {}
            seen_stores = set()
            for record in all_prices:
                store = record.store
                if store not in seen_stores:
                    seen_stores.add(store)
                    current_prices[store] = {
                        'price': record.price,
                        'price_display': record.price_display,
                        'url': record.product_url,
                        'title': record.product_title,
                        'image': record.product_image
                    }
            
            # Get price history for last 30 days (for chart)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            price_history = db.query(PriceHistory).filter(
                PriceHistory.wishlist_item_id == wishlist_item_id,
                PriceHistory.recorded_at >= thirty_days_ago
            ).order_by(PriceHistory.recorded_at.asc()).all()
            
            # Group price history by store
            history_by_store = {}
            for record in price_history:
                store = record.store
                if store not in history_by_store:
                    history_by_store[store] = []
                
                history_by_store[store].append({
                    'date': record.recorded_at.isoformat(),
                    'price': record.price,
                    'price_display': record.price_display,
                    'url': record.product_url
                })
            
            # Calculate lowest price
            lowest_price = min(current_prices.values(), key=lambda x: x['price'])['price'] if current_prices else None
            
            return jsonify({
                "success": True,
                "item": {
                    "id": item.id,
                    "product_name": item.product_name,
                    "product_category": item.product_category,
                    "target_price": item.target_price,
                    "created_at": item.created_at.strftime('%Y-%m-%d')
                },
                "current_prices": current_prices,
                "price_history": history_by_store,
                "lowest_price": lowest_price
            }), 200
        finally:
            db.close()
        
    except Exception as e:
        import traceback
        print(f"Error getting wishlist item details: {traceback.format_exc()}")
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500