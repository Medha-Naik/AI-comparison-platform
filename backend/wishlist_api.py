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
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        required_fields = ['user_email', 'product_name']
        for field in required_fields:
            if field not in data:
                return jsonify({"success": False, "message": f"Missing required field: {field}"}), 400
        
        # Require session auth
        if not session.get('user_id'):
            return jsonify({"success": False, "message": "Authentication required"}), 401

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

@wishlist_bp.route('/wishlist/check/<user_email>/<product_name>', methods=['GET'])
def check_in_wishlist(user_email, product_name):
    """Check if a product is in user's wishlist"""
    try:
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

