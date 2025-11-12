import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from utils.normalize import parse_price

def search_offers(query):
    safe_query = quote(query)
    url = f"https://www.flipkart.com/search?q={safe_query}"
    
    print(f"[Flipkart] Searching: {url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("[Flipkart] Success!")
    else:
        print(f"[Flipkart] Failed! Status: {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    products = soup.find_all('a', {'class': 'CGtC98'})
    print(f"[Flipkart] Found {len(products)} products")
    
    offers = []

    for product in products:
        try:
            # Extract title
            title_elem = product.find('div', class_='KzDlHZ')
            if not title_elem:
                continue
            title = title_elem.get_text().strip()

            # Extract price
            price_elem = product.find('div', class_='Nx9bqj')
            if not price_elem:
                continue
            price_text = price_elem.get_text().strip()

            # Extract link (product itself is the <a> tag)
            link = product.get('href')
            if not link:
                continue
            
            if link.startswith('/'):
                link = 'https://www.flipkart.com' + link
            
            # Extract image
            image_url = None
            try:
                img_elem = product.find('img')
                if img_elem:
                    image_url = img_elem.get('src') or img_elem.get('data-src')
                    if image_url and image_url.startswith('//'):
                        image_url = 'https:' + image_url
            except:
                pass

            # Debug print
            print(f"\n✅ Product {len(offers) + 1}:")
            print(f"   Title: {title}")
            print(f"   Price: {price_text}")
            if image_url:
                print(f"   Image: {image_url[:60]}...")

            offer = {
                "title": title,
                "price": parse_price(price_text),  # Integer for sorting
                "price_display": price_text,       # String for display
                "url": link,
                "store": "flipkart",
                "image": image_url
            }

            offers.append(offer)

        except Exception as e:
            print(f"[Flipkart] Error: {e}")
            continue

    print(f"\n[Flipkart] ✅ Total extracted: {len(offers)}")
    return offers

if __name__ == "__main__":
    results = search_offers("iphone 15")