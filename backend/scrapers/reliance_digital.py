from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import quote
import sys
import time
import re
from pathlib import Path
import os

sys.path.append(str(Path(__file__).parent.parent))

try:
    from utils.normalize import parse_price
except ImportError:
    def parse_price(price_text):
        """Extract numeric price from text like '₹53,990'"""
        cleaned = re.sub(r'[^\d]', '', price_text)
        return int(cleaned) if cleaned else 0

def setup_driver():
    """Setup Chrome driver with stealth settings"""
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    )
    
    # Speed up navigation: don't wait for all resources
    try:
        chrome_options.page_load_strategy = 'eager'
    except Exception:
        pass

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def _best_from_srcset(srcset: str) -> str:
    """Pick the highest-resolution URL from a srcset string."""
    try:
        parts = [p.strip() for p in srcset.split(',') if p.strip()]
        if not parts:
            return ''
        # each part like: https://... 1x or https://... 320w
        # pick the last assuming it's the largest
        last = parts[-1].split()[0]
        return last
    except Exception:
        return ''

def extract_image_url(product, driver) -> str:
    """
    Robustly extract an image URL from a product card. Handles lazy-loaded
    attributes like data-src, data-original, srcset/picture sources and
    CSS background images.
    """
    try:
        # Try the most specific selector first (based on site markup)
        try:
            img_elem = product.find_element(By.CSS_SELECTOR, 'a.product-card-image picture img.fy_img')
        except Exception:
            # Generic fallback
            img_elem = product.find_element(By.CSS_SELECTOR, "img")
        # Scroll into view to trigger lazy-loading
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img_elem)
        except Exception:
            pass

        # Prefer higher-resolution candidates first
        candidates = []

        # srcset on img (prefer highest)
        srcset = img_elem.get_attribute('srcset')
        if srcset:
            candidates.append(_best_from_srcset(srcset))

        # picture > source[srcset] (prefer highest)
        try:
            sources = product.find_elements(By.CSS_SELECTOR, 'picture source')
            for s in sources:
                sset = s.get_attribute('srcset')
                if sset:
                    candidates.append(_best_from_srcset(sset))
        except Exception:
            pass

        # Direct srcs (thumbnails)
        candidates.extend([
            img_elem.get_attribute('src'),
            img_elem.get_attribute('data-src'),
            img_elem.get_attribute('data-original'),
            img_elem.get_attribute('data-lazy'),
        ])

        # CSS background-image
        try:
            style = img_elem.get_attribute('style') or ''
            if 'background-image' in style:
                import re as _re
                m = _re.search(r"url\((['\"]?)(.+?)\1\)", style)
                if m:
                    candidates.append(m.group(2))
        except Exception:
            pass

        # Normalize protocol-relative URLs
        for url in candidates:
            if url and isinstance(url, str):
                if url.startswith('//'):
                    return 'https:' + url
                return url
    except Exception:
        pass

    return None

def search_offers(query="iphone 15", max_products=20):
    """
    Search Reliance Digital for products
    
    Args:
        query: Search term (default: "iphone 15")
        max_products: Max products to extract
    
    Returns:
        List of product dictionaries
    """
    
    # Map common queries to collection URLs
    query_lower = query.lower()
    
    if "iphone 15 plus" in query_lower:
        url = "https://www.reliancedigital.in/collection/apple-iphone-15-plus-mobiles"
    elif "iphone 15 pro max" in query_lower:
        url = "https://www.reliancedigital.in/collection/apple-iphone-15-pro-max-mobiles"
    elif "iphone 15 pro" in query_lower:
        url = "https://www.reliancedigital.in/collection/apple-iphone-15-pro-mobiles"
    elif "iphone 15" in query_lower:
        url = "https://www.reliancedigital.in/collection/apple-iphone-15-mobiles"
    elif "iphone 16" in query_lower:
        url = "https://www.reliancedigital.in/collection/apple-iphone-16-mobiles"
    elif "iphone" in query_lower:
        url = "https://www.reliancedigital.in/collection/apple-smartphones"
    else:
        safe_query = quote(query)
        url = f"https://www.reliancedigital.in/search?q={safe_query}"
    
    print(f"[Reliance Digital] Accessing: {url}")
    
    driver = None
    offers = []
    
    try:
        driver = setup_driver()
        driver.get(url)

        print("[Reliance Digital] Page loaded, waiting for products...")

        # Prefer explicit wait over fixed sleeps
        try:
            WebDriverWait(driver, 6).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='product'], div[class*='ProductCard'], .sp__product, .product-item, article"))
            )
        except TimeoutException:
            pass

        # Light scroll to trigger lazy-loading
        for i in range(2):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.5);")
            time.sleep(0.8)
        
        # Save for debugging (optional via env)
        if os.getenv('SAVE_SCRAPER_HTML', 'false').lower() in ('1', 'true', 'yes'):
            with open('reliance_digital_page.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("[Reliance Digital] HTML saved to reliance_digital_page.html")
        
        # Try multiple product selectors
        product_selectors = [
            "div[class*='product-card']",
            "div.sp__product",
            "div[class*='ProductCard']",
            "li[class*='product']",
            "div[data-product]",
            "article",
            ".product-item"
        ]
        
        products = []
        for selector in product_selectors:
            products = driver.find_elements(By.CSS_SELECTOR, selector)
            if products:
                print(f"[Reliance Digital] ✓ Found {len(products)} products using: {selector}")
                break
        
        # Fallback: find product links
        if not products:
            print("[Reliance Digital] Using fallback: searching for product links...")
            all_links = driver.find_elements(By.TAG_NAME, "a")
            products = []
            seen_urls = set()
            
            for link in all_links:
                href = link.get_attribute('href')
                if href and '/product/' in href and href not in seen_urls:
                    products.append(link)
                    seen_urls.add(href)
            
            if products:
                print(f"[Reliance Digital] ✓ Found {len(products)} product links")
        
        if not products:
            print("[Reliance Digital] ❌ No products found")
            return []
        
        # Allow environment override for max products (e.g., RELIANCE_MAX_PRODUCTS=8)
        try:
            env_max = int(os.getenv('RELIANCE_MAX_PRODUCTS', '').strip() or 0)
            if env_max > 0:
                max_products = min(max_products, env_max)
        except Exception:
            pass

        print(f"[Reliance Digital] Processing products (limit: {max_products})...")
        
        seen_titles = set()
        
        for idx, product in enumerate(products[:max_products * 2], 1):
            if len(offers) >= max_products:
                break
                
            try:
                # Get product URL
                if product.tag_name == 'a':
                    product_url = product.get_attribute('href')
                else:
                    try:
                        link_elem = product.find_element(By.TAG_NAME, "a")
                        product_url = link_elem.get_attribute('href')
                    except:
                        continue
                
                if not product_url or 'reliancedigital.in' not in product_url:
                    continue
                
                # Extract title - prioritize image alt
                title = None
                
                # Method 1: Image alt (most reliable)
                try:
                    img = product.find_element(By.TAG_NAME, "img")
                    alt_text = img.get_attribute('alt')
                    if alt_text and len(alt_text) > 10 and 'apple' in alt_text.lower():
                        title = alt_text
                except:
                    pass
                
                # Method 2: Heading tags with product name
                if not title:
                    try:
                        for tag in ['h2', 'h3', 'h4', 'h1']:
                            heading = product.find_element(By.TAG_NAME, tag)
                            text = heading.text.strip()
                            if text and 'apple' in text.lower() and len(text) > 15:
                                title = text
                                break
                    except:
                        pass
                
                # Method 3: Parse from visible text - skip promo lines
                if not title:
                    try:
                        lines = [l.strip() for l in product.text.split('\n') if l.strip()]
                        skip_words = ['off', 'bank', 'icici', 'hdfc', 'offer', 'limited', 
                                      'get rs', 'cashback', 'emi', 'no cost']
                        
                        for line in lines:
                            # Skip promotional text
                            if any(skip in line.lower() for skip in skip_words):
                                continue
                            
                            # Check if line looks like a product name
                            if (len(line) > 15 and 
                                'apple' in line.lower() and
                                not line.startswith('₹') and
                                not line.replace('.', '').isdigit()):
                                title = line
                                break
                    except:
                        pass
                
                # Method 4: Extract from URL
                if not title:
                    try:
                        url_parts = product_url.split('/product/')[-1]
                        name = url_parts.split('?')[0]
                        name = name.rsplit('-', 1)[0]
                        title = name.replace('-', ' ').title()
                    except:
                        pass
                
                if not title:
                    continue
                
                # Skip duplicates
                if title in seen_titles:
                    continue
                seen_titles.add(title)
                
                # Extract price
                price_text = None
                
                # Method 1: Price elements
                try:
                    price_selectors = [
                        "[class*='price']", 
                        "[class*='Price']", 
                        "[class*='amount']", 
                        ".sp__price"
                    ]
                    
                    for sel in price_selectors:
                        try:
                            price_elem = product.find_element(By.CSS_SELECTOR, sel)
                            text = price_elem.text
                            if '₹' in text:
                                price_text = text
                                break
                        except:
                            continue
                except:
                    pass
                
                # Method 2: Find ₹ in text
                if not price_text:
                    try:
                        text = product.text
                        matches = re.findall(r'₹[\d,]+(?:\.\d+)?', text)
                        if matches:
                            price_text = matches[0]
                    except:
                        pass
                
                if not price_text:
                    continue
                
                # Extract image (robust)
                image_url = extract_image_url(product, driver)
                
                # Build basic offer
                offer = {
                    "title": title.strip(),
                    "price": parse_price(price_text),
                    "price_display": price_text.strip(),
                    "url": product_url,
                    "store": "reliance digital",
                    "image": image_url
                }
                
                # Quick extract of visible info
                try:
                    text = product.text
                    
                    # Rating
                    rating_match = re.search(r'(\d+\.?\d*)\s*(?:★|star|out of)', text, re.IGNORECASE)
                    if rating_match:
                        rating_val = float(rating_match.group(1))
                        if 0 <= rating_val <= 5:
                            offer['rating'] = rating_val
                    
                    # Review count
                    review_match = re.search(r'\((\d+(?:,\d+)*)\s*(?:review|rating)', text, re.IGNORECASE)
                    if review_match:
                        offer['review_count'] = int(review_match.group(1).replace(',', ''))
                    
                    # Discount
                    discount_match = re.search(r'(\d+)%\s*(?:off)', text, re.IGNORECASE)
                    if discount_match:
                        offer['discount_percent'] = int(discount_match.group(1))
                    
                    # Original price
                    all_prices = re.findall(r'₹[\d,]+(?:\.\d+)?', text)
                    if len(all_prices) >= 2:
                        original_val = parse_price(all_prices[1])
                        current_val = offer['price']
                        
                        if original_val > current_val:
                            offer['original_price'] = original_val
                            offer['original_price_display'] = all_prices[1]
                            
                            if 'discount_percent' not in offer:
                                offer['discount_percent'] = round(
                                    ((original_val - current_val) / original_val) * 100, 1
                                )
                
                except:
                    pass
                
                print(f"\n✅ Product {len(offers) + 1}:")
                print(f"   {title[:70]}{'...' if len(title) > 70 else ''}")
                print(f"   💰 {price_text}")
                if 'rating' in offer:
                    print(f"   ⭐ {offer['rating']}", end='')
                    if 'review_count' in offer:
                        print(f" ({offer['review_count']} reviews)", end='')
                    print()
                if 'discount_percent' in offer:
                    print(f"   🏷️  {offer['discount_percent']}% OFF")
                
                offers.append(offer)
                
            except Exception as e:
                print(f"[Reliance Digital] Error parsing product {idx}: {e}")
                continue
        
        print(f"\n[Reliance Digital] ✅ Extracted {len(offers)} products")
        
    except Exception as e:
        print(f"[Reliance Digital] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            driver.quit()
    
    return offers

if __name__ == "__main__":
    results = search_offers("iphone 15", max_products=15)
    
    if results:
        print("\n" + "="*70)
        print("FINAL RESULTS - RELIANCE DIGITAL IPHONE 15:")
        print("="*70)
        
        for i, offer in enumerate(results, 1):
            print(f"\n{i}. {offer['title']}")
            print(f"   💰 Price: {offer['price_display']}")
            
            if 'original_price_display' in offer:
                print(f"   🏷️  Was: {offer['original_price_display']} "
                      f"(Save {offer.get('discount_percent', 'N/A')}%)")
            
            if 'rating' in offer:
                stars = '⭐' * int(offer['rating'])
                reviews = f" ({offer['review_count']} reviews)" if 'review_count' in offer else ""
                print(f"   {stars} {offer['rating']}{reviews}")
            
            if 'delivery' in offer:
                print(f"   🚚 {offer['delivery']}")
            
            print(f"   🔗 {offer['url']}")
    else:
        print("\n❌ No results found. Check reliance_digital_page.html")