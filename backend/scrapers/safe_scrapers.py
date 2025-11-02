# LAZY IMPORTS: Only import scrapers if needed (for performance)
# Since all scrapers are disabled, we don't need to import them
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.mock_data import search_mock_offers

# Lazy import scrapers only when actually needed
_girias_real = None
_flipkart_real = None
_reliance_real = None

def _get_girias_scraper():
    """Lazy load girias scraper only when needed"""
    global _girias_real
    if _girias_real is None:
        try:
            from scrapers.girias import search_offers as girias_real
            _girias_real = girias_real
        except ImportError:
            _girias_real = False  # Mark as unavailable
    return _girias_real if _girias_real else None

def _get_flipkart_scraper():
    """Lazy load flipkart scraper only when needed"""
    global _flipkart_real
    if _flipkart_real is None:
        try:
            from scrapers.flipkart import search_offers as flipkart_real
            _flipkart_real = flipkart_real
        except ImportError:
            _flipkart_real = False
    return _flipkart_real if _flipkart_real else None

def _get_reliance_scraper():
    """Lazy load reliance scraper only when needed"""
    global _reliance_real
    if _reliance_real is None:
        try:
            from scrapers.reliance_digital import search_offers as reliance_real
            _reliance_real = reliance_real
        except ImportError:
            _reliance_real = False
    return _reliance_real if _reliance_real else None

# Configuration - Enable real scrapers for specific stores via env flags
# WARNING: Real scrapers can get blocked! Use mock data for reliable demos.
# STATIC DATA MODE: All scrapers disabled - using only static JSON files
REAL_SCRAPERS_CONFIG = {
    'flipkart': False,  # DISABLED - using static data only
    'reliance digital': False,  # DISABLED - using static data only
    'amazon': False,  # DISABLED - using static data only
    'girias': False  # DISABLED - using static data only
}

# To enable real scrapers (risky - currently disabled for static data mode):
# Set env vars REAL_SCRAPER_FLIPKART/RELIANCE/AMAZON to true/1/yes
# Be aware you may get blocked, rate-limited, or CAPTCHAs

FALLBACK_TO_MOCK = os.getenv('FALLBACK_TO_MOCK', 'true').lower() in ('1', 'true', 'yes')

def search_with_fallback(query, stores=None):
    """
    Smart scraper with fallback to mock data - OPTIMIZED VERSION
    
    Perfect for academic demos - always works!
    
    Args:
        query: search query
        stores: list of stores ['flipkart', 'amazon', 'reliance digital', 'croma'] or None for all
    
    Returns:
        dict with offers and metadata
    """
    if stores is None:
        stores = ['flipkart', 'amazon', 'reliance digital', 'croma', 'girias']
    
    start_time = time.time()
    
    # OPTIMIZATION: Since all scrapers are disabled, just load all products once
    # and filter in a single pass instead of multiple calls
    if all(not REAL_SCRAPERS_CONFIG.get(store.lower(), False) for store in stores):
        # All stores use mock data - optimize by doing ONE search for all stores
        from data.mock_data import search_mock_offers
        all_offers = search_mock_offers(query, stores)
        
        # Build sources dict
        sources = {}
        for offer in all_offers:
            store = offer.get('store', '').lower()
            if store not in sources:
                sources[store] = 'mock'
        
        elapsed = time.time() - start_time
        return {
            'offers': all_offers,
            'sources': sources,
            'errors': None,
            'time_taken': round(elapsed, 2),
            'query': query
        }
    
    # Fallback to original logic if any real scrapers are enabled
    all_offers = []
    sources = {}  # Track which data source was used
    errors = []
    
    # Try Flipkart
    if 'flipkart' in stores:
        if REAL_SCRAPERS_CONFIG.get('flipkart', False):
            try:
                flipkart_fn = _get_flipkart_scraper()
                if flipkart_fn:
                    flipkart_offers = flipkart_fn(query)
                    if len(flipkart_offers) > 0:
                        all_offers.extend(flipkart_offers)
                        sources['flipkart'] = 'real'
                else:
                    raise Exception("Flipkart scraper not available")
            except Exception as e:
                errors.append(f"Flipkart: {str(e)}")
                if FALLBACK_TO_MOCK:
                    mock_flipkart = search_mock_offers(query, ['flipkart'])
                    all_offers.extend(mock_flipkart)
                    sources['flipkart'] = 'mock'
        else:
            mock_flipkart = search_mock_offers(query, ['flipkart'])
            all_offers.extend(mock_flipkart)
            sources['flipkart'] = 'mock'
    
    # Try Amazon
    if 'amazon' in stores:
        if REAL_SCRAPERS_CONFIG.get('amazon', False):
            try:
                raise Exception("Amazon scraper not available")
            except Exception as e:
                errors.append(f"Amazon: {str(e)}")
                if FALLBACK_TO_MOCK:
                    mock_amazon = search_mock_offers(query, ['amazon'])
                    all_offers.extend(mock_amazon)
                    sources['amazon'] = 'mock'
        else:
            mock_amazon = search_mock_offers(query, ['amazon'])
            all_offers.extend(mock_amazon)
            sources['amazon'] = 'mock'
    
    # Croma
    if 'croma' in stores:
        mock_croma = search_mock_offers(query, ['croma'])
        all_offers.extend(mock_croma)
        sources['croma'] = 'mock'
    
    # Reliance Digital
    if 'reliance digital' in stores:
        if REAL_SCRAPERS_CONFIG.get('reliance digital', False):
            try:
                reliance_fn = _get_reliance_scraper()
                if reliance_fn:
                    reliance_offers = reliance_fn(query)
                    if len(reliance_offers) > 0:
                        all_offers.extend(reliance_offers)
                        sources['reliance digital'] = 'real'
                else:
                    raise Exception("Reliance scraper not available")
            except Exception as e:
                errors.append(f"Reliance Digital: {str(e)}")
                if FALLBACK_TO_MOCK:
                    mock_reliance = search_mock_offers(query, ['reliance digital'])
                    all_offers.extend(mock_reliance)
                    sources['reliance digital'] = 'mock'
        else:
            mock_reliance = search_mock_offers(query, ['reliance digital'])
            all_offers.extend(mock_reliance)
            sources['reliance digital'] = 'mock'

    # Girias
    if 'girias' in stores:
        if REAL_SCRAPERS_CONFIG.get('girias', False):
            try:
                girias_fn = _get_girias_scraper()
                if girias_fn:
                    girias_offers = girias_fn(query)
                    if len(girias_offers) > 0:
                        all_offers.extend(girias_offers)
                        sources['girias'] = 'real'
                else:
                    raise Exception("Girias scraper not available")
            except Exception as e:
                errors.append(f"Girias: {str(e)}")
                if FALLBACK_TO_MOCK:
                    mock_girias = search_mock_offers(query, ['girias'])
                    all_offers.extend(mock_girias)
                    sources['girias'] = 'mock'
        else:
            mock_girias = search_mock_offers(query, ['girias'])
            all_offers.extend(mock_girias)
            sources['girias'] = 'mock'
    
    elapsed = time.time() - start_time
    
    return {
        'offers': all_offers,
        'sources': sources,
        'errors': errors if errors else None,
        'time_taken': round(elapsed, 2),
        'query': query
    }

# Test function
if __name__ == "__main__":
    print("Testing Safe Scraper with Fallback\n")
    print("="*60)
    
    result = search_with_fallback("iphone 15")
    
    print("\n" + "="*60)
    print(f"Query: {result['query']}")
    print(f"Total Offers: {len(result['offers'])}")
    print(f"Time Taken: {result['time_taken']}s")
    print(f"\nData Sources:")
    for store, source in result['sources'].items():
        print(f"  - {store}: {source}")
    
    if result['errors']:
        print(f"\nErrors: {result['errors']}")
    
    print("\nFirst 3 products:")
    for i, offer in enumerate(result['offers'][:3], 1):
        print(f"\n{i}. {offer['title']}")
        print(f"   Store: {offer['store']}")
        print(f"   Price: {offer['price_display']}")