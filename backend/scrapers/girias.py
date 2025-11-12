"""
Optimized Girias scraper (fast)
Requirements:
  pip install playwright
  playwright install chromium
"""

from playwright.sync_api import sync_playwright
from urllib.parse import quote
from utils.normalize import parse_price


def search_offers(query: str, max_products: int = 12):
    safe_query = quote(query)
    url = f"https://giriasindia.com/search?q={safe_query}"

    print(f"[Girias] Searching: {url}")

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True, args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ])

            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
                locale="en-IN",
                timezone_id="Asia/Kolkata",
                color_scheme="light",
            )

            page = context.new_page()
            page.set_default_timeout(7000)

            # Block heavy resources to speed up
            def _block(route):
                r = route.request
                if r.resource_type in ("image", "font", "media"):  # keep HTML/CSS/JS only
                    return route.abort()
                return route.continue_()

            page.route("**/*", _block)

            # Light navigation and waits
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass

            # Wait for any product anchors to appear
            try:
                page.locator('a.p-3.pt-11.w-full[target="_blank"], a[href*="/product/"]').first.wait_for(timeout=5000)
            except Exception:
                pass

            # Prefer selecting the full card container (more reliable to find price outside the link)
            products = page.locator('div:has(a.p-3.pt-11.w-full[target="_blank"])').all()
            if len(products) == 0:
                products = page.locator('div:has(a[href*="/product/"])').all()
            # Final fallback: use anchors as items
            if len(products) == 0:
                products = page.locator('a.p-3.pt-11.w-full[target="_blank"]').all()
            if len(products) == 0:
                products = page.locator('a[href*="/product/"]').all()

            if len(products) == 0:
                browser.close()
                return []

            if len(products) > max_products:
                products = products[:max_products]

            offers = []

            for product in products:
                try:
                    # URL
                    # If the container isn't an <a>, find its anchor
                    link = product.get_attribute("href")
                    if not link:
                        try:
                            a = product.locator('a.p-3.pt-11.w-full[target="_blank"], a[href*="/product/"]').first
                            if a.count() > 0:
                                link = a.get_attribute('href')
                        except Exception:
                            pass
                    if not link:
                        continue
                    if link.startswith("/"):
                        link = "https://giriasindia.com" + link
                    if "/product/" not in link:
                        continue

                    # Title
                    title = None
                    h4 = product.locator("h4").first
                    if h4.count() > 0:
                        title = h4.inner_text().strip()
                    if not title:
                        # fallback from text
                        try:
                            text = product.inner_text()
                            if text:
                                title = text.split("\n")[0].strip()
                        except Exception:
                            pass
                    if not title:
                        continue

                    # Price (robust extraction)
                    price_text = None
                    # 1) Try direct text match within the card
                    try:
                        price_node = product.locator("text=/₹\\s*[\\d,]+/i").first
                        if price_node.count() > 0:
                            price_text = price_node.inner_text().strip()
                    except Exception:
                        pass
                    # 2) Try common selectors but ignore pure 'offer' badges
                    if not price_text:
                        price_candidates = [
                            'div.text-center.text-red-500.font-bold.text-sm.mt-2',
                            'div.text-red-500',
                            'div[class*="price"]',
                            'span[class*="price"]',
                        ]
                        for sel in price_candidates:
                            elem = product.locator(sel).first
                            if elem.count() > 0:
                                txt = elem.inner_text().strip()
                                lower = txt.lower()
                                if 'offer' in lower and ('₹' not in txt and 'rs' not in lower):
                                    continue
                                if txt and ("₹" in txt or "Rs" in txt or txt.replace(",", "").replace('.', '').isdigit()):
                                    price_text = txt
                                    break
                    # 3) Regex over full textContent (more complete than inner_text)
                    if not price_text:
                        try:
                            import re
                            all_text = product.evaluate("el => el.textContent") or ""
                            matches = re.findall(r"₹\s*[\d,]+|Rs\.?\s*[\d,]+|INR\s*[\d,]+", all_text, flags=re.I)
                            if matches:
                                price_text = matches[0].strip()
                        except Exception:
                            pass
                    # Final guard: if we still captured something without digits, drop it
                    if price_text and not any(ch.isdigit() for ch in price_text):
                        price_text = None

                    # Minimal image (may be blocked; optional)
                    image_url = None
                    try:
                        img = product.locator("img").first
                        if img.count() > 0:
                            image_url = img.get_attribute("src") or img.get_attribute("data-src")
                            if image_url:
                                if image_url.startswith("//"):
                                    image_url = "https:" + image_url
                                elif image_url.startswith("/"):
                                    image_url = "https://giriasindia.com" + image_url
                    except Exception:
                        pass

                    offer = {
                        "title": title,
                        "url": link,
                        "store": "girias",
                        "image": image_url,
                    }

                    if price_text:
                        offer["price"] = parse_price(price_text)
                        offer["price_display"] = price_text

                    offers.append(offer)
                except Exception:
                    continue

            browser.close()
            return offers
        except Exception as e:
            print(f"[Girias] Error: {e}")
            return []


if __name__ == "__main__":
    print(search_offers("iphone 15", max_products=8))


