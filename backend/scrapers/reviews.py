"""
Flipkart Review Scraper

DISCLAIMER: This code is for educational purposes only.
- Check Flipkart's Terms of Service before using
- Review their robots.txt file
- Use responsibly with appropriate delays
- Consider legal implications in your jurisdiction
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import pandas as pd
import json

class FlipkartReviewScraper:
    def __init__(self, headless=True):
        """Initialize the scraper with Chrome options"""
        self.options = Options()
        if headless:
            self.options.add_argument('--headless')
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--no-sandbox')
        self.driver = None
        
    def start_driver(self):
        """Start the Chrome driver"""
        self.driver = webdriver.Chrome(options=self.options)
        
    def close_driver(self):
        """Close the Chrome driver"""
        if self.driver:
            self.driver.quit()
            
    def scrape_reviews(self, product_url, max_pages=5):
        """
        Scrape reviews from a Flipkart product page
        
        Args:
            product_url: URL of the product page
            max_pages: Maximum number of review pages to scrape
            
        Returns:
            List of dictionaries containing review data
        """
        if not self.driver:
            self.start_driver()
            
        reviews_data = []
        
        try:
            # Navigate to the product page
            print(f"Navigating to: {product_url}")
            self.driver.get(product_url)
            time.sleep(3)  # Wait for page to load
            
            # Click on "Read More" or reviews section if needed
            try:
                # Try to find and click the reviews/ratings section
                reviews_link = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Ratings & Reviews')]"))
                )
                reviews_link.click()
                time.sleep(2)
            except:
                print("Reviews section not found or already visible")
            
            # Scrape multiple pages
            for page in range(max_pages):
                print(f"Scraping page {page + 1}...")
                
                # Get page source and parse with BeautifulSoup
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Find all review containers - these class names may need updating
                review_containers = soup.find_all('div', class_='col')
                
                # Alternative selectors if above doesn't work
                if not review_containers:
                    review_containers = soup.find_all('div', {'class': lambda x: x and 'review' in x.lower()})
                
                for container in review_containers:
                    try:
                        review = {}
                        
                        # Extract rating (look for star ratings)
                        rating_elem = container.find('div', class_=lambda x: x and ('rating' in str(x).lower() or 'star' in str(x).lower()))
                        if rating_elem:
                            review['rating'] = rating_elem.text.strip()
                        
                        # Extract review title
                        title_elem = container.find('p', class_=lambda x: x and 'title' in str(x).lower())
                        if title_elem:
                            review['title'] = title_elem.text.strip()
                        
                        # Extract review text
                        text_elems = container.find_all('div', class_='')
                        for elem in text_elems:
                            if elem.text and len(elem.text.strip()) > 50:
                                review['review_text'] = elem.text.strip()
                                break
                        
                        # Extract reviewer name
                        name_elem = container.find('p', class_=lambda x: x and 'name' in str(x).lower())
                        if name_elem:
                            review['reviewer_name'] = name_elem.text.strip()
                        
                        # Extract review date
                        date_elem = container.find('p', class_=lambda x: x and 'date' in str(x).lower())
                        if date_elem:
                            review['review_date'] = date_elem.text.strip()
                        
                        # Extract helpful votes
                        votes_elem = container.find('div', class_=lambda x: x and 'vote' in str(x).lower())
                        if votes_elem:
                            review['helpful_votes'] = votes_elem.text.strip()
                        
                        # Only add if we got some data
                        if review and len(review) > 1:
                            reviews_data.append(review)
                            
                    except Exception as e:
                        print(f"Error parsing review: {e}")
                        continue
                
                # Try to go to next page
                if page < max_pages - 1:
                    try:
                        next_button = self.driver.find_element(By.XPATH, "//a[contains(text(), 'Next')]")
                        next_button.click()
                        time.sleep(3)  # Wait for next page to load
                    except:
                        print("No more pages or next button not found")
                        break
                        
        except Exception as e:
            print(f"Error during scraping: {e}")
            
        return reviews_data
    
    def save_to_csv(self, reviews_data, filename='flipkart_reviews.csv'):
        """Save reviews to CSV file"""
        df = pd.DataFrame(reviews_data)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Saved {len(reviews_data)} reviews to {filename}")
        
    def save_to_json(self, reviews_data, filename='flipkart_reviews.json'):
        """Save reviews to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(reviews_data, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(reviews_data)} reviews to {filename}")


# Example usage
if __name__ == "__main__":
    # Replace with actual Flipkart product URL
    PRODUCT_URL = "https://www.flipkart.com/your-product-url-here"
    
    # Initialize scraper
    scraper = FlipkartReviewScraper(headless=False)  # Set True to hide browser
    
    try:
        # Scrape reviews
        reviews = scraper.scrape_reviews(PRODUCT_URL, max_pages=3)
        
        print(f"\nScraped {len(reviews)} reviews")
        
        # Display first few reviews
        for i, review in enumerate(reviews[:3], 1):
            print(f"\n--- Review {i} ---")
            for key, value in review.items():
                print(f"{key}: {value}")
        
        # Save to files
        if reviews:
            scraper.save_to_csv(reviews)
            scraper.save_to_json(reviews)
            
    finally:
        # Always close the driver
        scraper.close_driver()