"""
Wishlist API endpoints - IMPROVED PRODUCT MATCHING
✅ Uses same fuzzy matching logic as wishlist_service
✅ Handles product name variations gracefully
✅ Better Dell laptop model matching
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Blueprint, request, jsonify, session
from services.wishlist_service import wishlist_service
from models import create_tables

wishlist_bp = Blueprint("wishlist", __name__)
create_tables()


# ---------------------------------------------------------------------------
# BASIC ROUTES (unchanged)
# ---------------------------------------------------------------------------

@wishlist_bp.route("/wishlist/add", methods=["POST"])
def add_to_wishlist():
    try:
        if not session.get("user_id"):
            return jsonify({"success": False, "message": "Authentication required"}), 401

        data = request.get_json()
        if not data or "product_name" not in data:
            return jsonify({"success": False, "message": "Missing product_name"}), 400

        result = wishlist_service.add_to_wishlist(
            user_email=session.get("user_email"),
            product_name=data["product_name"],
            product_category=data.get("product_category"),
            target_price=data.get("target_price"),
        )
        return jsonify(result), (200 if result["success"] else 400)
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


@wishlist_bp.route("/wishlist/remove", methods=["POST"])
def remove_from_wishlist():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        if not session.get("user_id"):
            return jsonify({"success": False, "message": "Authentication required"}), 401

        result = wishlist_service.remove_from_wishlist(
            user_email=session.get("user_email"),
            wishlist_item_id=data.get("wishlist_item_id"),
        )
        return jsonify(result), (200 if result["success"] else 400)
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


@wishlist_bp.route("/wishlist/me", methods=["GET"])
def get_wishlist():
    try:
        if not session.get("user_id"):
            return jsonify({"success": False, "message": "Authentication required"}), 401
        wishlist = wishlist_service.get_wishlist(session.get("user_email"))
        return jsonify({"success": True, "wishlist": wishlist}), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


# ---------------------------------------------------------------------------
# IMPROVED HELPER: Better product matching (same logic as wishlist_service)
# ---------------------------------------------------------------------------

def find_best_mock_product_match(product_name, all_products):
    """
    Find best matching product in mock data using multiple strategies.
    Returns the matched key and the product offers.
    """
    product_lower = product_name.lower().strip()
    
    print(f"[MATCH] Searching mock data for: {product_name}")
    print(f"[MATCH] Available products: {list(all_products.keys())}")
    
    # Strategy 1: Exact match
    for key in all_products.keys():
        if key.lower() == product_lower:
            print(f"[MATCH] ✅ Exact match: '{key}'")
            return key, all_products[key]
    
    # Strategy 2: Substring match
    for key in all_products.keys():
        key_lower = key.lower()
        if product_lower in key_lower or key_lower in product_lower:
            print(f"[MATCH] ✅ Substring match: '{key}'")
            return key, all_products[key]
    
    # Strategy 3: Word-based partial matching (ignore specs)
    skip_words = {"intel", "core", "gen", "th", "gb", "ram", "ssd", "hdd", 
                  "processor", "i5", "i7", "i9", "m1", "m2", "series", "edition",
                  "13th", "12th", "11th", "14th", "16gb", "512gb", "256gb", "1tb"}
    
    def get_significant_words(name):
        words = name.lower().replace("-", " ").replace("/", " ").split()
        return [w for w in words if w not in skip_words and len(w) > 2]
    
    search_words = get_significant_words(product_name)
    print(f"[MATCH] Search words (filtered): {search_words}")
    
    # Check if all significant words match
    for key in all_products.keys():
        key_words = get_significant_words(key)
        if all(word in ' '.join(key_words) for word in search_words):
            print(f"[MATCH] ✅ All words match: '{key}'")
            return key, all_products[key]
    
    # Check if any significant words match (at least 2)
    best_match = None
    best_score = 0
    
    for key in all_products.keys():
        key_words = set(get_significant_words(key))
        search_words_set = set(search_words)
        common = key_words.intersection(search_words_set)
        
        if len(common) >= 2:  # At least 2 common words
            score = len(common)
            if score > best_score:
                best_score = score
                best_match = key
    
    if best_match:
        print(f"[MATCH] ✅ Partial word match ({best_score} words): '{best_match}'")
        return best_match, all_products[best_match]
    
    # Strategy 4: Difflib fuzzy matching (last resort)
    from difflib import get_close_matches
    matches = get_close_matches(
        product_lower, 
        [k.lower() for k in all_products.keys()], 
        n=1, 
        cutoff=0.2
    )
    
    if matches:
        for key in all_products.keys():
            if key.lower() == matches[0]:
                print(f"[MATCH] ✅ Fuzzy match: '{key}'")
                return key, all_products[key]
    
    print(f"[MATCH] ❌ No match found")
    return None, []


# ---------------------------------------------------------------------------
# HELPER: Fuzzy product name matching (for price_history.json)
# ---------------------------------------------------------------------------

def find_matching_product_key(product_name, all_data):
    """Find best matching key in price_history.json (ignores specs like Intel/GB/etc.)"""
    product_name_lower = product_name.lower().strip()

    def normalize_words(name):
        skip = {"intel", "core", "gen", "th", "gb", "ram", "ssd", "hdd", "processor",
                "i5", "i7", "i9", "m1", "m2", "series", "edition", 
                "13th", "12th", "11th", "14th", "16gb", "512gb", "256gb", "1tb"}
        words = [w for w in name.replace("-", " ").replace("/", " ").split()
                 if w not in skip and len(w) > 1]
        return set(words)

    product_words = normalize_words(product_name_lower)
    best_match, best_score = None, 0

    for key in all_data.keys():
        key_lower = key.lower().strip()
        key_words = normalize_words(key_lower)

        # Direct or substring match first
        if (product_name_lower == key_lower or
            product_name_lower in key_lower or
            key_lower in product_name_lower):
            return key

        common = product_words.intersection(key_words)
        if not common:
            continue

        score = len(common) / max(len(product_words), len(key_words))
        if score > best_score and score > 0.25:  # 25% overlap threshold
            best_score, best_match = score, key

    return best_match


# ---------------------------------------------------------------------------
# MAIN ROUTE: Wishlist item details (FIXED MATCHING)
# ---------------------------------------------------------------------------

@wishlist_bp.route("/wishlist/details/<int:wishlist_item_id>", methods=["GET"])
def get_wishlist_item_details(wishlist_item_id):
    """
    Returns:
      {
        "item": {...},
        "current_prices": {...},
        "price_history": {...},
        "lowest_price": ...
      }
    """
    try:
        if not session.get("user_id"):
            return jsonify({"success": False, "message": "Authentication required"}), 401

        from models import get_db, WishlistItem
        from utils.price_tracker import _load_all
        from data.mock_data import load_products

        db = next(get_db())
        try:
            item = (
                db.query(WishlistItem)
                .filter(
                    WishlistItem.id == wishlist_item_id,
                    WishlistItem.user_id == session.get("user_id"),
                )
                .first()
            )
            if not item:
                return jsonify({"success": False, "message": "Wishlist item not found"}), 404

            product_name = item.product_name.strip()
            print(f"\n🔍 Loading details for: {product_name}")

            # -----------------------------------------------------------------
            # 🔹 Step 1: Get current prices (IMPROVED MATCHING)
            # -----------------------------------------------------------------
            all_products = load_products()
            matched_key, search_results = find_best_mock_product_match(product_name, all_products)

            current_prices, store_prices = {}, {}
            lowest_price = None

            # Normalize store names and group by store
            for product in search_results:
                store = (product.get("store") or "").lower().strip()
                price = product.get("price")

                store_aliases = {
                    "reliance digital": "reliance",
                    "reliance retail": "reliance",
                    "amazon.in": "amazon",
                    "flipkart india": "flipkart",
                    "croma india": "croma",
                }
                store = store_aliases.get(store, store)

                if not store or price is None:
                    continue

                if store not in store_prices or price < store_prices[store]["price"]:
                    store_prices[store] = product

            # Build final current price dictionary
            for store, product in store_prices.items():
                price = product.get("price")
                if lowest_price is None or price < lowest_price:
                    lowest_price = price
                current_prices[store] = {
                    "price": price,
                    "price_display": f"₹{price:,}",
                    "url": product.get("url", ""),
                    "title": product.get("title", ""),
                    "image": product.get("image", ""),
                }

            if current_prices:
                print(f"💰 Current prices from {len(current_prices)} stores (matched key: '{matched_key}')")
            else:
                print(f"⚠️ No current prices found")

            # -----------------------------------------------------------------
            # 🔹 Step 2: Load price history from JSON (with fuzzy key match)
            # -----------------------------------------------------------------
            all_data = _load_all()
            price_history = {}
            history_matched_key = find_matching_product_key(product_name, all_data)

            if history_matched_key:
                print(f"✅ Matched JSON key: '{history_matched_key}'")
                for store, history_list in all_data[history_matched_key].items():
                    if isinstance(history_list, list) and history_list:
                        price_history[store.lower()] = [
                            {
                                "date": entry["date"],
                                "price": entry["price"],
                                "price_display": f"₹{entry['price']:,}",
                            }
                            for entry in history_list
                        ]
            else:
                print(f"⚠️ No price history found for '{product_name}'")
                print("📋 Available keys in price_history.json:")
                for key in list(all_data.keys())[:5]:
                    print(f"   - {key}")

            print(f"📊 Price history: {len(price_history)} stores")

            # -----------------------------------------------------------------
            # 🔹 Step 3: Return combined response
            # -----------------------------------------------------------------
            return (
                jsonify(
                    {
                        "success": True,
                        "item": {
                            "id": item.id,
                            "product_name": product_name,
                            "product_category": item.product_category,
                            "target_price": item.target_price,
                            "created_at": item.created_at.strftime("%Y-%m-%d"),
                        },
                        "current_prices": current_prices,
                        "price_history": price_history,
                        "lowest_price": lowest_price,
                        "debug": {
                            "mock_data_match": matched_key,
                            "price_history_match": history_matched_key
                        }
                    }
                ),
                200,
            )

        finally:
            db.close()

    except Exception as e:
        import traceback
        print(f"❌ Error in wishlist details: {traceback.format_exc()}")
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


@wishlist_bp.route("/wishlist/update-target-price", methods=["POST"])
def update_target_price():
    """Update target price for a wishlist item"""
    try:
        if not session.get("user_id"):
            return jsonify({"success": False, "message": "Authentication required"}), 401

        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        wishlist_item_id = data.get("wishlist_item_id")
        target_price = data.get("target_price")
        
        if wishlist_item_id is None or target_price is None:
            return jsonify({
                "success": False, 
                "message": "Missing wishlist_item_id or target_price"
            }), 400

        result = wishlist_service.update_target_price(
            user_email=session.get("user_email"),
            wishlist_item_id=wishlist_item_id,
            target_price=float(target_price)
        )
        
        return jsonify(result), (200 if result["success"] else 400)
        
    except Exception as e:
        import traceback
        print(f"❌ Error updating target price: {traceback.format_exc()}")
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


@wishlist_bp.route("/wishlist/refresh-prices/<int:wishlist_item_id>", methods=["POST"])
def refresh_prices(wishlist_item_id):
    """Manually refresh prices for a wishlist item"""
    try:
        if not session.get("user_id"):
            return jsonify({"success": False, "message": "Authentication required"}), 401

        result = wishlist_service.update_prices_for_item(wishlist_item_id)
        return jsonify(result), (200 if result["success"] else 400)
        
    except Exception as e:
        import traceback
        print(f"❌ Error refreshing prices: {traceback.format_exc()}")
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500