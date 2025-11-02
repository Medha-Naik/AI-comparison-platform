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
    
    print(f"\n{'='*60}")
    print(f"[API] Academic Demo Mode")
    print(f"[API] Query: '{query}'")
    if store_filter:
        print(f"[API] Store Filter: {store_filter}")
    print(f"{'='*60}\n")
    
    
    stores = None
    if store_filter:
        stores = [store_filter]
    
   
    result = search_with_fallback(query, stores)
    
    
    # Attach tracking keys and record today's price per offer
    for offer in result['offers']:
        try:
            key = record_price(offer, offer.get('price'))
            offer['offer_key'] = key
        except Exception as e:
            # Non-fatal; continue without key
            offer['offer_key'] = None

    result['offers'].sort(key=lambda x: x['price'])
    
    print(f"\n{'='*60}")
    print(f"[API] Completed in {result['time_taken']}s")
    print(f"[API] Total offers: {len(result['offers'])}")
    print(f"[API] Data sources: {result['sources']}")
    print(f"{'='*60}\n")
    
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

    history = get_history(key)

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

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎓 AI Shopping Assistant - Academic Demo Mode")
    print("="*60)
    print("🏠 Home: http://127.0.0.1:5000/")
    print("📍 Search: http://127.0.0.1:5000/search?q=iphone+15")
    print("📍 Products: http://127.0.0.1:5000/products")
    print("📍 Health: http://127.0.0.1:5000/health")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000)