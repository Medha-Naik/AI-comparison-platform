from scrapers.girias import search_offers as girias_real
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.flipkart import search_offers as flipkart_real
from scrapers.reliance_digital import search_offers as reliance_real
# from scrapers.amazon_playwright import search_offers as amazon_real  # Use this if you have Playwright
from data.mock_data import search_mock_offers
import time

# Configuration - Enable real scrapers for specific stores via env flags
# WARNING: Real scrapers can get blocked! Use mock data for reliable demos.
REAL_SCRAPERS_CONFIG = {
    'flipkart': os.getenv('REAL_SCRAPER_FLIPKART', 'false').lower() in ('1', 'true', 'yes'),
    'reliance digital': os.getenv('REAL_SCRAPER_RELIANCE', 'false').lower() in ('1', 'true', 'yes'),
    'amazon': os.getenv('REAL_SCRAPER_AMAZON', 'false').lower() in ('1', 'true', 'yes')
}

# To enable real scrapers (risky):
# Set env vars REAL_SCRAPER_FLIPKART/RELIANCE/AMAZON to true/1/yes
# Be aware you may get blocked, rate-limited, or CAPTCHAs

FALLBACK_TO_MOCK = os.getenv('FALLBACK_TO_MOCK', 'true').lower() in ('1', 'true', 'yes')

def search_with_fallback(query, stores=None):
    """
    Smart scraper with fallback to mock data
    
    Perfect for academic demos - always works!
    
    Args:
        query: search query
        stores: list of stores ['flipkart', 'amazon', 'reliance digital', 'croma'] or None for all
    
    Returns:
        dict with offers and metadata
    """
    if stores is None:
        stores = ['flipkart', 'amazon', 'reliance digital', 'croma', 'girias']
    
    all_offers = []
    sources = {}  # Track which data source was used
    errors = []
    
    start_time = time.time()
    
    # Try Flipkart
    if 'flipkart' in stores:
        if REAL_SCRAPERS_CONFIG.get('flipkart', False):
            try:
                print(f"[SafeScraper] Trying real Flipkart scraper...")
                flipkart_offers = flipkart_real(query)
                
                if len(flipkart_offers) > 0:
                    all_offers.extend(flipkart_offers)
                    sources['flipkart'] = 'real'
                    print(f"[SafeScraper] ✅ Flipkart REAL: {len(flipkart_offers)} products")
                else:
                    raise Exception("No products returned")
                    
            except Exception as e:
                print(f"[SafeScraper] ⚠️  Flipkart scraper failed: {e}")
                errors.append(f"Flipkart: {str(e)}")
                
                if FALLBACK_TO_MOCK:
                    mock_flipkart = search_mock_offers(query, ['flipkart'])
                    all_offers.extend(mock_flipkart)
                    sources['flipkart'] = 'mock'
                    print(f"[SafeScraper] 🔄 Flipkart FALLBACK: {len(mock_flipkart)} products")
        else:
            # Always use mock
            mock_flipkart = search_mock_offers(query, ['flipkart'])
            all_offers.extend(mock_flipkart)
            sources['flipkart'] = 'mock'
            print(f"[SafeScraper] 📋 Flipkart MOCK: {len(mock_flipkart)} products")
    
    # Try Amazon (similar logic)
    if 'amazon' in stores:
        if REAL_SCRAPERS_CONFIG.get('amazon', False):
            try:
                print(f"[SafeScraper] Trying real Amazon scraper...")
                # If you have amazon scraper working:
                # amazon_offers = amazon_real(query)
                # For now, raise exception to use mock
                raise Exception("Amazon scraper not available (demo mode)")
                
            except Exception as e:
                print(f"[SafeScraper] ⚠️  Amazon scraper failed: {e}")
                errors.append(f"Amazon: {str(e)}")
                
                if FALLBACK_TO_MOCK:
                    mock_amazon = search_mock_offers(query, ['amazon'])
                    all_offers.extend(mock_amazon)
                    sources['amazon'] = 'mock'
                    print(f"[SafeScraper] 🔄 Amazon FALLBACK: {len(mock_amazon)} products")
        else:
            mock_amazon = search_mock_offers(query, ['amazon'])
            all_offers.extend(mock_amazon)
            sources['amazon'] = 'mock'
            print(f"[SafeScraper] 📋 Amazon MOCK: {len(mock_amazon)} products")
    
    # Croma - Always use mock data
    if 'croma' in stores:
        mock_croma = search_mock_offers(query, ['croma'])
        all_offers.extend(mock_croma)
        sources['croma'] = 'mock'
        print(f"[SafeScraper] 📋 Croma MOCK: {len(mock_croma)} products")
    
    # Try Reliance Digital
    if 'reliance digital' in stores:
        if REAL_SCRAPERS_CONFIG.get('reliance digital', False):
            try:
                print(f"[SafeScraper] Trying real Reliance Digital scraper...")
                reliance_offers = reliance_real(query)
                
                if len(reliance_offers) > 0:
                    all_offers.extend(reliance_offers)
                    sources['reliance digital'] = 'real'
                    print(f"[SafeScraper] ✅ Reliance Digital REAL: {len(reliance_offers)} products")
                else:
                    raise Exception("No products returned")
                    
            except Exception as e:
                print(f"[SafeScraper] ⚠️  Reliance Digital scraper failed: {e}")
                errors.append(f"Reliance Digital: {str(e)}")
                
                if FALLBACK_TO_MOCK:
                    mock_reliance = search_mock_offers(query, ['reliance digital'])
                    all_offers.extend(mock_reliance)
                    sources['reliance digital'] = 'mock'
                    print(f"[SafeScraper] 🔄 Reliance Digital FALLBACK: {len(mock_reliance)} products")
        else:
            mock_reliance = search_mock_offers(query, ['reliance digital'])
            all_offers.extend(mock_reliance)
            sources['reliance digital'] = 'mock'
            print(f"[SafeScraper] 📋 Reliance Digital MOCK: {len(mock_reliance)} products")

    # Try Girias (fast Playwright scraper)
    if 'girias' in stores:
        try:
            print(f"[SafeScraper] Trying real Girias scraper...")
            girias_offers = girias_real(query)
            if len(girias_offers) > 0:
                all_offers.extend(girias_offers)
                sources['girias'] = 'real'
                print(f"[SafeScraper] ✅ Girias REAL: {len(girias_offers)} products")
            else:
                print(f"[SafeScraper] ⚠️  Girias returned no products")
        except Exception as e:
            print(f"[SafeScraper] ⚠️  Girias scraper failed: {e}")
            errors.append(f"Girias: {str(e)}")
    
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