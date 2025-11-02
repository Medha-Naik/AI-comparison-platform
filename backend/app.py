from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
from dotenv import load_dotenv
import os

from scrapers.safe_scrapers import search_with_fallback
from utils.price_tracker import record_price, generate_offer_key, get_history
from wishlist_api import wishlist_bp
from auth_api import auth_bp, init_oauth

load_dotenv()

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static', static_url_path='')
# Secret key for sessions (set via env in production)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-change-me')

# Session and URL settings optimized for local OAuth
app.config.update(
    SESSION_COOKIE_SAMESITE='Lax',   # allow top-level GET redirects to send cookies
    SESSION_COOKIE_SECURE=False,     # http during local dev
    PREFERRED_URL_SCHEME='http'
)

CORS(app)

# Register wishlist blueprint
app.register_blueprint(wishlist_bp, url_prefix='/api')
app.register_blueprint(auth_bp)

# Initialize OAuth providers
init_oauth(app)


@app.route('/')
def home():
    """Serve the landing page"""
    return render_template('home.html')

@app.route('/results')
def results():
    """Serve the results page"""
    return render_template('results.html')

@app.route('/wishlist')
def wishlist():
    """Serve the wishlist page"""
    if not session.get('user_id'):
        return redirect(url_for('login_page'))
    return render_template('wishlist.html')

@app.route('/product-details')
def product_details():
    """Serve the product details page"""
    return render_template('product_details.html')

@app.route('/product')
def product():
    """Redirect to results page (product.html removed)"""
    from flask import redirect, request
    query = request.args.get('q', '')
    if query:
        return redirect(f'/results?q={query}')
    return redirect('/')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    # Reuse the same page; it already has a Create account action
    return render_template('login.html')


# (Aliases no longer needed since auth blueprint is at root)

@app.route('/health')
def health():
    return jsonify({"status": "ok", "mode": "academic demo"})

# Debug: list all routes (temporary helper)
@app.route('/routes')
def routes():
    try:
        rules = []
        for rule in app.url_map.iter_rules():
            rules.append({
                'rule': str(rule),
                'endpoint': rule.endpoint,
                'methods': sorted(list(rule.methods))
            })
        return jsonify({'count': len(rules), 'routes': sorted(rules, key=lambda r: r['rule'])})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    store_filter = request.args.get('store')  # Optional: 'flipkart' or 'amazon'
    
    if not query:
        return jsonify({"error": "Missing query parameter 'q'"}), 400
    
    # Reduced logging for better performance (can enable for debugging)
    # print(f"[API] Query: '{query}'")
    
    
    stores = None
    if store_filter:
        stores = [store_filter]
    
   
    result = search_with_fallback(query, stores)
    
    # ULTRA-FAST PATH: Generate keys without loading any price history files
    # Just create keys from offer data - no file I/O at all
    for offer in result['offers']:
        try:
            # Generate key directly without importing anything that loads files
            store = (offer.get('store') or '').strip().lower()
            url = (offer.get('url') or '').strip()
            title = (offer.get('title') or '').strip().lower()
            base = url if url else title
            offer['offer_key'] = f"{store}|{base}" if base else None
        except Exception:
            offer['offer_key'] = None

    # Sort by price
    result['offers'].sort(key=lambda x: x.get('price', 0))
    
    # Reduced logging (can enable for debugging)
    # print(f"[API] Completed in {result['time_taken']}s, Found {len(result['offers'])} offers")
    
    return jsonify({
        "query": result['query'],
        "count": len(result['offers']),
        "offers": result['offers'],
        "time_taken": result['time_taken'],
        "sources": result['sources'],  
        "errors": result['errors']
    })

@app.route('/profile')
def profile():
    """Serve the profile page"""
    if not session.get('user_id'):
        return redirect(url_for('login_page', next='/profile'))
    return render_template('profile.html')

@app.route('/wishlist/details/<int:item_id>')
def wishlist_item_detail(item_id):
    """Serve the wishlist item detail page"""
    if not session.get('user_id'):
        return redirect(url_for('login_page'))
    return render_template('wishlist_item_detail.html', item_id=item_id)

@app.route('/price-history')
def price_history():
    """Return price history for a given offer key.
    Query params: key=..., or provide store + url/title to build the key.
    """
    key = request.args.get('key')
    if not key:
        # Try to synthesize key if store + url/title provided
        store = request.args.get('store')
        url = request.args.get('url')
        title = request.args.get('title')
        offer_like = { 'store': store, 'url': url, 'title': title }
        key = generate_offer_key(offer_like)

    if not key:
        return jsonify({"error": "Missing 'key' (or store+url/title)"}), 400

    # Build offer dict from params to help with static format lookup
    offer_dict = {
        'store': request.args.get('store'),
        'url': request.args.get('url'),
        'title': request.args.get('title')
    }
    history = get_history(key, offer_dict if any(offer_dict.values()) else None)

    # Optional filter: days=N (e.g., 30)
    days_param = request.args.get('days')
    if days_param:
        try:
            from datetime import datetime, timedelta
            days_int = int(days_param)
            cutoff = datetime.utcnow() - timedelta(days=days_int)
            def parse_date(d):
                return datetime.strptime(d, '%Y-%m-%d')
            history = [h for h in history if parse_date(h.get('date', '1970-01-01')) >= cutoff]
        except Exception:
            pass

    return jsonify({
        'key': key,
        'history': history
    })

@app.route('/product-reviews')
def product_reviews():
    """Return reviews for a given offer key (mock/demo)."""
    key = request.args.get('key')
    if not key:
        return jsonify({"error": "Missing 'key'"}), 400
    reviews = [
        {"author": "Aditi", "rating": 5, "title": "Great value", "body": "Battery life is excellent and camera is solid."},
        {"author": "Rahul", "rating": 4, "title": "Good but pricey", "body": "Performance is top-notch, wish it was cheaper."},
        {"author": "Meera", "rating": 3, "title": "Average camera", "body": "Daylight photos are fine, low light is mediocre."}
    ]
    return jsonify({"key": key, "reviews": reviews})

@app.route('/products')
def list_products():
    """List all available products in mock data"""
    from data.mock_data import load_products
    
    products_dict = load_products()
    products = []
    for key, items in products_dict.items():
        products.append({
            'id': key,
            'name': key.title(),
            'count': len(items)
        })
    
    return jsonify({
        "products": products,
        "total": len(products)
    })

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve product images from backend/data directory"""
    from flask import send_from_directory
    import os
    from urllib.parse import unquote
    
    # Images are stored in backend/data directory
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    
    # Decode URL-encoded filename (handles spaces like "Dell 15DC15250.jpg")
    decoded_filename = unquote(filename)
    
    # Try to find the file (case-insensitive for Windows)
    # First try exact match
    file_path = os.path.join(data_dir, decoded_filename)
    if os.path.exists(file_path):
        return send_from_directory(data_dir, decoded_filename)
    
    # If not found, try case-insensitive search (for Windows compatibility)
    if os.name == 'nt':  # Windows
        for actual_file in os.listdir(data_dir):
            if actual_file.lower() == decoded_filename.lower() and os.path.isfile(os.path.join(data_dir, actual_file)):
                return send_from_directory(data_dir, actual_file)
    
    # If still not found, return 404
    from flask import abort
    abort(404)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎓 AI Shopping Assistant - Academic Demo Mode")
    print("="*60)
    print("🏠 Home: http://127.0.0.1:5000/")
    print("📍 Search: http://127.0.0.1:5000/search?q=iphone+15")
    print("📍 Products: http://127.0.0.1:5000/products")
    print("📍 Health: http://127.0.0.1:5000/health")
    print("="*60 + "\n")
    
    # Disable debug mode for production/performance
    # Set debug=False or use environment variable
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() in ('1', 'true', 'yes')
    app.run(debug=debug_mode, port=5000)