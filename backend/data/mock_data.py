import json
import os

# Get the path to products.json
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PRODUCTS_FILE = os.path.join(CURRENT_DIR, 'products.json')

# Global cache for products - load once, use many times
_products_cache = None

def load_products():
    """Load products from JSON file (with caching)"""
    global _products_cache
    if _products_cache is not None:
        return _products_cache
    
    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            _products_cache = json.load(f)
            return _products_cache
    except FileNotFoundError:
        print(f"Warning: {PRODUCTS_FILE} not found!")
        return {}
    except json.JSONDecodeError:
        print(f"Warning: Invalid JSON in {PRODUCTS_FILE}")
        return {}

def clear_cache():
    """Clear the products cache (useful for testing or reloading)"""
    global _products_cache
    _products_cache = None

def search_mock_offers(query, stores=None):
    """
    Search for products in mock data - OPTIMIZED VERSION with STRICT MATCHING
    
    Args:
        query: search query (e.g., "iphone 15", "macbook")
        stores: list of stores to filter ['flipkart', 'amazon'] or None for all
    
    Returns:
        list of matching products
    """
    products = load_products()  # Uses cache - fast
    query_lower = query.lower().strip()
    query_words = query_lower.split()
    
    # Filter: Keep words that are meaningful (length > 1 OR multi-digit numbers like "15", "12", etc.)
    # This keeps "15" in "iphone 15" but helps filter very short words
    meaningful_words = []
    for w in query_words:
        if len(w) > 1:  # Keep words longer than 1 char
            # Keep multi-digit numbers (like "15", "12") but prefer non-numeric words
            if not (len(w) == 2 and w.isdigit()):  # Filter out 2-digit numbers when alone
                meaningful_words.append(w)
            elif len([w2 for w2 in query_words if not w2.isdigit()]) > 0:  # Keep if there are non-numeric words
                meaningful_words.append(w)
    
    # Normalize stores to lowercase set for fast lookup
    if stores:
        stores_set = {s.lower().strip() for s in stores}
    else:
        stores_set = None
    
    results = []
    
    # Single pass through all products
    for product_name, product_list in products.items():
        product_name_lower = product_name.lower()
        
        # STRICT MATCHING: Require full query as substring OR multiple meaningful words match
        # This prevents "iphone 15" from matching "Dell 15DC15250" (only matches "15")
        matches_query = False
        
        # Priority 1: Full query as substring (best match - e.g., "iphone 15" matches "iphone 15")
        if len(query_lower) > 3 and query_lower in product_name_lower:
            matches_query = True
        
        # Priority 2: Multiple meaningful words must match
        # For "iphone 15": ["iphone", "15"] must both match product name
        elif len(meaningful_words) >= 2:
            matching_count = sum(1 for word in meaningful_words if word in product_name_lower)
            # Require ALL words to match (strict matching)
            if matching_count == len(meaningful_words):
                matches_query = True
        
        # Priority 3: Single meaningful word (only if it's substantial, not a short number)
        elif len(meaningful_words) == 1:
            word = meaningful_words[0]
            # Only match if word is at least 3 chars OR it's part of a multi-word product name
            if len(word) >= 3 and word in product_name_lower:
                matches_query = True
        
        if matches_query:
            for product in product_list:
                # Fast store filter using set lookup
                if stores_set is None or product.get('store', '').lower().strip() in stores_set:
                    results.append(product)
    
    return results

# For backward compatibility - get products by exact key
def get_products_by_key(key):
    """Get products by exact key match"""
    products = load_products()
    return products.get(key, [])

# Test function
if __name__ == "__main__":
    print("Testing Mock Data Loader\n")
    
    # Test 1: Search for iPhone
    print("1. Searching for 'iphone 15':")
    results = search_mock_offers("iphone 15")
    print(f"   Found {len(results)} products")
    
    # Test 2: Search with store filter
    print("\n2. Searching for 'macbook' (Flipkart only):")
    results = search_mock_offers("macbook", stores=['flipkart'])
    print(f"   Found {len(results)} products")
    for r in results:
        print(f"   - {r['title'][:50]}... | {r['store']}")
    
    # Test 3: Fuzzy search
    print("\n3. Searching for 'laptop':")
    results = search_mock_offers("laptop")
    print(f"   Found {len(results)} products")
    
    # Test 4: List all available products
    print("\n4. Available product categories:")
    products = load_products()
    for key in products.keys():
        print(f"   - {key}")