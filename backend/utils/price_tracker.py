import os
import json
from datetime import datetime
from threading import Lock


_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
_HISTORY_PATH = os.path.join(_DATA_DIR, 'price_history.json')
_lock = Lock()

# STATIC DATA MODE: Set to True to disable automatic price recording
# This preserves your static price_history.json file
DISABLE_PRICE_RECORDING = os.getenv('DISABLE_PRICE_RECORDING', 'false').lower() in ('1', 'true', 'yes')


def _ensure_store_file():
    if not os.path.isdir(_DATA_DIR):
        os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_HISTORY_PATH):
        with open(_HISTORY_PATH, 'w', encoding='utf-8') as f:
            json.dump({}, f)


# Cache for price history to avoid reloading on every lookup
_history_cache = None
_history_cache_time = 0
_HISTORY_CACHE_TTL = 300  # Cache for 5 minutes

def _load_all() -> dict:
    """Load price history with caching for better performance - LAZY LOADING"""
    global _history_cache, _history_cache_time
    import time
    
    # If DISABLE_PRICE_RECORDING is True, skip loading entirely
    if DISABLE_PRICE_RECORDING and _history_cache is None:
        # Return empty dict to avoid file I/O
        _history_cache = {}
        _history_cache_time = time.time()
        return _history_cache
    
    current_time = time.time()
    
    # Return cached data if available and fresh
    if (_history_cache is not None and 
        (current_time - _history_cache_time) < _HISTORY_CACHE_TTL):
        return _history_cache
    
    # Load fresh data
    _ensure_store_file()
    try:
        with open(_HISTORY_PATH, 'r', encoding='utf-8') as f:
            try:
                _history_cache = json.load(f)
                _history_cache_time = current_time
                return _history_cache
            except json.JSONDecodeError:
                _history_cache = {}
                _history_cache_time = current_time
                return _history_cache
    except FileNotFoundError:
        _history_cache = {}
        _history_cache_time = current_time
        return _history_cache


def _save_all(data: dict) -> None:
    """Save price history and update cache"""
    global _history_cache, _history_cache_time
    import time
    
    tmp_path = _HISTORY_PATH + '.tmp'
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, _HISTORY_PATH)
    
    # Update cache after saving
    _history_cache = data
    _history_cache_time = time.time()


def generate_offer_key(offer: dict) -> str:
    """
    Create a stable key for an offer combining store and a stable identifier.
    Preference order: url, title.
    """
    store = (offer.get('store') or '').strip().lower()
    url = (offer.get('url') or '').strip()
    title = (offer.get('title') or '').strip().lower()
    base = url if url else title
    return f"{store}|{base}"


def record_price(offer: dict, price: int) -> str:
    """
    Record today's price for the offer. Returns the offer key used.
    If a record for today already exists with the same price, do nothing.
    
    In STATIC DATA MODE, price recording is disabled to preserve static JSON files.
    Set DISABLE_PRICE_RECORDING=true environment variable to enable this mode.
    """
    key = generate_offer_key(offer)
    if not key or price is None:
        return key
    
    # Skip recording if in static mode (preserves static data)
    if DISABLE_PRICE_RECORDING:
        return key

    today = datetime.utcnow().strftime('%Y-%m-%d')

    with _lock:
        data = _load_all()
        history = data.get(key, [])

        if history and history[-1].get('date') == today:
            # Update same-day entry if price differs
            if history[-1].get('price') != price:
                history[-1]['price'] = price
        else:
            history.append({'date': today, 'price': price})

        data[key] = history
        _save_all(data)

    return key


# Cache for products to avoid reloading on every lookup
_products_cache = None
_products_cache_time = 0
_CACHE_TTL = 300  # Cache for 5 minutes

def _get_cached_products():
    """Get cached products, reloading if cache is stale"""
    global _products_cache, _products_cache_time
    import time
    current_time = time.time()
    
    if _products_cache is None or (current_time - _products_cache_time) > _CACHE_TTL:
        from data.mock_data import load_products
        _products_cache = load_products()
        _products_cache_time = current_time
    
    return _products_cache

def get_history(key: str, offer: dict = None) -> list:
    """
    Get price history for a given key.
    
    Supports two formats:
    1. Dynamic format: {"flipkart|url": [{"date": "...", "price": ...}]}
    2. Static format: {"iphone 15": {"flipkart": [{"date": "...", "price": ...}]}}
    
    Args:
        key: Offer key in format "store|url" or "store|title"
        offer: Optional offer dict with 'store', 'url', 'title' to help lookup in static format
    
    Returns:
        List of price history entries
    """
    if not key:
        return []
    
    with _lock:
        data = _load_all()
        
        # Try direct key lookup first (dynamic format) - fastest path
        if key in data and isinstance(data[key], list):
            return data.get(key, [])
        
        # Try static format lookup: product_name -> store -> history
        # Extract store from key (format: "store|...")
        if '|' in key:
            store = key.split('|')[0].lower().strip()
            key_base = key.split('|', 1)[1] if '|' in key else ''
            
            # Use cached products instead of loading every time
            products = _get_cached_products()
            
            # Optimize: If offer dict provided, use it for faster matching
            if offer:
                offer_store = (offer.get('store') or '').lower().strip()
                offer_url = (offer.get('url') or '').strip()
                offer_title = (offer.get('title') or '').lower().strip()
                
                # Search for matching product
                for product_name, product_list in products.items():
                    for product in product_list:
                        product_store = product.get('store', '').lower().strip()
                        
                        if product_store != store or product_store != offer_store:
                            continue
                        
                        product_url = product.get('url', '').strip()
                        product_title = product.get('title', '').lower().strip()
                        
                        # Fast exact match using offer dict
                        if (offer_url and offer_url == product_url) or \
                           (offer_title and offer_title == product_title):
                            if product_name in data and isinstance(data[product_name], dict):
                                store_history = data[product_name].get(store, [])
                                if store_history:
                                    return store_history
            
            # Fallback: Match by key pattern (slower but works without offer dict)
            for product_name, product_list in products.items():
                for product in product_list:
                    product_store = product.get('store', '').lower().strip()
                    
                    if product_store != store:
                        continue
                    
                    product_url = product.get('url', '').strip()
                    product_title = product.get('title', '').lower().strip()
                    
                    # Match if URL or title matches the key base
                    if (product_url and product_url in key_base) or \
                       (product_title and product_title in key_base.lower()):
                        if product_name in data and isinstance(data[product_name], dict):
                            store_history = data[product_name].get(store, [])
                            if store_history:
                                return store_history
        
        return []


