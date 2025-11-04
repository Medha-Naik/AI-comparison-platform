from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

# Local imports
from scrapers.safe_scrapers import search_with_fallback
from utils.price_tracker import record_price, generate_offer_key, get_history
from wishlist_api import wishlist_bp
from auth_api import auth_bp, init_oauth
from review_api import review_bp  # <-- this handles /api/reviews/analyze

# Initialize Flask
app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static', static_url_path='')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-change-me')

# Flask config
app.config.update(
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=False,
    PREFERRED_URL_SCHEME='http'
)

# Enable CORS
CORS(app)

# Register blueprints (✅ ensure this comes AFTER app initialization)
app.register_blueprint(wishlist_bp, url_prefix='/api')
app.register_blueprint(auth_bp)
app.register_blueprint(review_bp, url_prefix='/api')  # ✅ FIXED PREFIX

# Initialize OAuth
init_oauth(app)

# -------------------------------
# 🏠 PAGE ROUTES
# -------------------------------

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
    """Redirect to results page"""
    query = request.args.get('q', '')
    if query:
        return redirect(f'/results?q={query}')
    return redirect('/')


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/signup')
def signup_page():
    return render_template('login.html')


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
    return render_template('wishlist_item_detail.html')


# -------------------------------
# ⚙️ API ROUTES
# -------------------------------

@app.route('/health')
def health():
    """Health check"""
    return jsonify({"status": "ok", "mode": "academic demo"})


@app.route('/routes')
def routes():
    """List all available routes"""
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
    """Search for products across supported stores"""
    query = request.args.get('q', '').strip()
    store_filter = request.args.get('store')  # Optional filter: 'flipkart', 'amazon', etc.

    if not query:
        return jsonify({"error": "Missing query parameter 'q'"}), 400

    stores = [store_filter] if store_filter else None
    result = search_with_fallback(query, stores)

    for offer in result['offers']:
        try:
            store = (offer.get('store') or '').strip().lower()
            url = (offer.get('url') or '').strip()
            title = (offer.get('title') or '').strip().lower()
            base = url if url else title
            offer['offer_key'] = f"{store}|{base}" if base else None
        except Exception:
            offer['offer_key'] = None

    result['offers'].sort(key=lambda x: x.get('price', 0))

    return jsonify({
        "query": result['query'],
        "count": len(result['offers']),
        "offers": result['offers'],
        "time_taken": result['time_taken'],
        "sources": result['sources'],
        "errors": result['errors']
    })


@app.route('/price-history')
def price_history():
    """Return price history for a given offer key"""
    key = request.args.get('key')
    if not key:
        store = request.args.get('store')
        url = request.args.get('url')
        title = request.args.get('title')
        offer_like = {'store': store, 'url': url, 'title': title}
        key = generate_offer_key(offer_like)

    if not key:
        return jsonify({"error": "Missing 'key' (or store+url/title)"}), 400

    offer_dict = {
        'store': request.args.get('store'),
        'url': request.args.get('url'),
        'title': request.args.get('title')
    }

    history = get_history(key, offer_dict if any(offer_dict.values()) else None)

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

    return jsonify({'key': key, 'history': history})


@app.route('/products')
def list_products():
    """List all available products"""
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
    """Serve product images"""
    from flask import send_from_directory
    from urllib.parse import unquote
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

    decoded_filename = unquote(filename)
    file_path = os.path.join(data_dir, decoded_filename)

    if os.path.exists(file_path):
        return send_from_directory(data_dir, decoded_filename)

    # Handle case-insensitive filenames (for Windows)
    if os.name == 'nt':
        for actual_file in os.listdir(data_dir):
            if actual_file.lower() == decoded_filename.lower() and os.path.isfile(os.path.join(data_dir, actual_file)):
                return send_from_directory(data_dir, actual_file)

    from flask import abort
    abort(404)


# -------------------------------
# 🚀 MAIN ENTRY POINT
# -------------------------------

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎓 AI Shopping Assistant - Academic Demo Mode")
    print("="*60)
    print("🏠 Home: http://127.0.0.1:5000/")
    print("📍 Search: http://127.0.0.1:5000/search?q=iphone+15")
    print("📍 Products: http://127.0.0.1:5000/products")
    print("📍 Health: http://127.0.0.1:5000/health")
    print("="*60 + "\n")

    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() in ('1', 'true', 'yes')
    app.run(debug=debug_mode, port=5000)
