import json
import os

# Get the path to products.json
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PRODUCTS_FILE = os.path.join(CURRENT_DIR, 'products.json')

def load_products():
    """Load products from JSON file"""
    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {PRODUCTS_FILE} not found!")
        return {}
    except json.JSONDecodeError:
        print(f"Warning: Invalid JSON in {PRODUCTS_FILE}")
        return {}

def search_mock_offers(query, stores=None):
    """
    Search for products in mock data
    
    Args:
        query: search query (e.g., "iphone 15", "macbook")
        stores: list of stores to filter ['flipkart', 'amazon'] or None for all
    
    Returns:
        list of matching products
    """
    products = load_products()
    query_lower = query.lower().strip()
    
    results = []
    
    # Search through all product categories
    for product_name, product_list in products.items():
        # Check if query matches product name
        if query_lower in product_name.lower():
            for product in product_list:
                # Filter by store if specified
                if stores is None or product['store'] in stores:
                    results.append(product)
    
    # If no exact match, try fuzzy matching
    if len(results) == 0:
        # Try partial matches
        query_words = query_lower.split()
        for product_name, product_list in products.items():
            product_name_lower = product_name.lower()
            # If any query word is in product name
            if any(word in product_name_lower for word in query_words):
                for product in product_list:
                    if stores is None or product['store'] in stores:
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