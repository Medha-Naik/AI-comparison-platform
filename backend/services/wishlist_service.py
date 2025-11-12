"""
Wishlist service - FIXED PRODUCT MATCHING
✅ Better fuzzy matching for product names
✅ Partial matching (e.g., "Dell XPS" matches "Dell 15DC15250")
✅ Multiple matching strategies
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import get_db, WishlistItem, PriceHistory, PriceNotification, User
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

class WishlistService:
    """Service for managing wishlist operations"""
    
    def __init__(self):
        pass
    
    def _get_db(self):
        """Get a new database session"""
        return next(get_db())
    
    def _get_mock_prices(self, product_name: str) -> List[Dict]:
        """Get current prices from mock data (static demo mode) with improved matching"""
        try:
            from data.mock_data import search_mock_offers, load_products
            from difflib import get_close_matches
            
            print(f"[MOCK PRICES] Searching for: {product_name}")
            
            # Strategy 1: Try exact match first
            results = search_mock_offers(product_name)
            
            if results:
                print(f"[MOCK PRICES] ✅ Exact match found")
                print(f"[MOCK PRICES] Found {len(results)} offers")
                for offer in results:
                    print(f"[MOCK PRICES]   - {offer.get('store')}: ₹{offer.get('price'):,}")
                return results
            
            # Strategy 2: Load all products for fuzzy matching
            all_products = load_products()
            all_keys = list(all_products.keys())
            product_lower = product_name.lower().strip()
            
            print(f"[MOCK PRICES] No exact match, trying fuzzy matching...")
            print(f"[MOCK PRICES] Available products: {all_keys}")
            
            # Strategy 3: Partial word matching (e.g., "Dell XPS" matches "Dell 15DC15250")
            matching_key = None
            
            # Extract significant words from search query (ignore common words)
            search_words = [w for w in product_lower.split() if len(w) > 2]
            print(f"[MOCK PRICES] Search words: {search_words}")
            
            for key in all_keys:
                key_lower = key.lower()
                # Check if all search words are present in the product key
                if all(word in key_lower for word in search_words):
                    matching_key = key
                    print(f"[MOCK PRICES] ✅ Partial match found: '{key}'")
                    break
            
            if not matching_key:
                # Strategy 4: Check if any significant word matches
                for key in all_keys:
                    key_lower = key.lower()
                    if any(word in key_lower for word in search_words):
                        matching_key = key
                        print(f"[MOCK PRICES] ✅ Partial word match found: '{key}'")
                        break
            
            if not matching_key:
                # Strategy 5: Use difflib for fuzzy matching with lower cutoff
                matches = get_close_matches(
                    product_lower, 
                    [k.lower() for k in all_keys], 
                    n=1, 
                    cutoff=0.2  # Lowered from 0.3 for more lenient matching
                )
                
                if matches:
                    # Find the original key (preserve case)
                    for k in all_keys:
                        if k.lower() == matches[0]:
                            matching_key = k
                            print(f"[MOCK PRICES] ✅ Fuzzy match found: '{k}'")
                            break
            
            if matching_key:
                results = all_products.get(matching_key, [])
                print(f"[MOCK PRICES] Found {len(results)} offers for '{matching_key}'")
                for offer in results:
                    print(f"[MOCK PRICES]   - {offer.get('store')}: ₹{offer.get('price'):,}")
                return results
            else:
                print(f"[MOCK PRICES] ❌ No matching product found")
                print(f"[MOCK PRICES] Available products: {', '.join(all_keys)}")
                return []
            
        except Exception as e:
            print(f"[MOCK PRICES] ❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def add_to_wishlist(self, user_email: str, product_name: str, 
                       product_category: str = None, target_price: float = None) -> Dict:
        """Add a product to user's wishlist"""
        db = self._get_db()
        try:
            print(f"\n{'='*60}")
            print(f"[WISHLIST] Adding product: {product_name}")
            print(f"[WISHLIST] Target price: ₹{target_price:,.2f}" if target_price else "[WISHLIST] No target price set")
            print(f"{'='*60}")
            
            # Get or create user
            user = db.query(User).filter(User.email == user_email).first()
            if not user:
                user = User(email=user_email)
                db.add(user)
                db.commit()
                db.refresh(user)
                print(f"[WISHLIST] Created new user: {user_email}")
            
            # Check if product already exists in wishlist
            existing_item = db.query(WishlistItem).filter(
                WishlistItem.user_id == user.id,
                WishlistItem.product_name == product_name,
                WishlistItem.is_active == True
            ).first()
            
            if existing_item:
                print(f"[WISHLIST] Product already in wishlist (ID: {existing_item.id})")
                return {
                    "success": False,
                    "message": "Product already in wishlist",
                    "wishlist_item_id": existing_item.id
                }
            
            # Create new wishlist item
            wishlist_item = WishlistItem(
                user_id=user.id,
                product_name=product_name,
                product_category=product_category,
                target_price=target_price
            )
            
            db.add(wishlist_item)
            db.commit()
            db.refresh(wishlist_item)
            
            print(f"[WISHLIST] ✅ Created wishlist item ID: {wishlist_item.id}")
            
            # Check prices immediately (using mock data)
            if target_price:
                print(f"[WISHLIST] Checking if current mock prices meet target...")
                self.check_target_price_alerts_mock(wishlist_item, db)
            
            return {
                "success": True,
                "message": "Product added to wishlist",
                "wishlist_item_id": wishlist_item.id
            }
            
        except Exception as e:
            db.rollback()
            import traceback
            print(f"[WISHLIST] ❌ Error adding to wishlist: {traceback.format_exc()}")
            return {
                "success": False,
                "message": f"Error adding to wishlist: {str(e)}"
            }
        finally:
            db.close()
    
    def remove_from_wishlist(self, user_email: str, wishlist_item_id: int) -> Dict:
        """Remove a product from user's wishlist"""
        db = self._get_db()
        try:
            user = db.query(User).filter(User.email == user_email).first()
            if not user:
                return {"success": False, "message": "User not found"}
            
            wishlist_item = db.query(WishlistItem).filter(
                WishlistItem.id == wishlist_item_id,
                WishlistItem.user_id == user.id
            ).first()
            
            if not wishlist_item:
                return {"success": False, "message": "Wishlist item not found"}
            
            # Soft delete
            wishlist_item.is_active = False
            db.commit()
            
            return {"success": True, "message": "Product removed from wishlist"}
            
        except Exception as e:
            db.rollback()
            import traceback
            print(f"[WISHLIST] Error removing from wishlist: {traceback.format_exc()}")
            return {"success": False, "message": f"Error removing from wishlist: {str(e)}"}
        finally:
            db.close()
    
    def get_wishlist(self, user_email: str) -> List[Dict]:
        """Get user's wishlist with current prices from mock data"""
        db = self._get_db()
        try:
            user = db.query(User).filter(User.email == user_email).first()
            if not user:
                return []
            
            wishlist_items = db.query(WishlistItem).filter(
                WishlistItem.user_id == user.id,
                WishlistItem.is_active == True
            ).all()
            
            result = []
            for item in wishlist_items:
                # Get current prices from mock data (not database)
                mock_offers = self._get_mock_prices(item.product_name)
                
                store_prices = {}
                lowest_price = None
                
                for offer in mock_offers:
                    store = offer.get('store', '').lower().strip()
                    price = offer.get('price')
                    
                    if not store or price is None:
                        continue
                    
                    if store not in store_prices or price < store_prices[store]['price']:
                        store_prices[store] = {
                            "price": price,
                            "price_display": offer.get('price_display', f"₹{price:,}"),
                            "url": offer.get('url', ''),
                            "title": offer.get('title', ''),
                            "image": offer.get('image', ''),
                            "recorded_at": datetime.now().isoformat()
                        }
                        
                        if lowest_price is None or price < lowest_price:
                            lowest_price = price
                
                result.append({
                    "id": item.id,
                    "product_name": item.product_name,
                    "product_category": item.product_category,
                    "target_price": item.target_price,
                    "created_at": item.created_at.isoformat(),
                    "current_prices": store_prices,
                    "lowest_price": lowest_price
                })
            
            return result
            
        except Exception as e:
            import traceback
            print(f"[WISHLIST] Error getting wishlist: {traceback.format_exc()}")
            return []
        finally:
            db.close()
    
    def update_target_price(self, user_email: str, wishlist_item_id: int, target_price: float) -> Dict:
        """Update target price for a wishlist item"""
        db = self._get_db()
        try:
            print(f"\n{'='*60}")
            print(f"[TARGET PRICE] Updating target price for item {wishlist_item_id}")
            print(f"[TARGET PRICE] New target: ₹{target_price:,.2f}")
            print(f"{'='*60}")
            
            user = db.query(User).filter(User.email == user_email).first()
            if not user:
                print(f"[TARGET PRICE] ❌ User not found: {user_email}")
                return {"success": False, "message": "User not found"}
            
            wishlist_item = db.query(WishlistItem).filter(
                WishlistItem.id == wishlist_item_id,
                WishlistItem.user_id == user.id
            ).first()
            
            if not wishlist_item:
                print(f"[TARGET PRICE] ❌ Wishlist item not found: {wishlist_item_id}")
                return {"success": False, "message": "Wishlist item not found"}
            
            old_target = wishlist_item.target_price
            wishlist_item.target_price = target_price
            db.commit()
            db.refresh(wishlist_item)
            
            print(f"[TARGET PRICE] ✅ Target price updated: ₹{old_target or 0:,.2f} → ₹{target_price:,.2f}")
            
            # Check if current mock prices meet the new target
            print(f"[TARGET PRICE] Checking if current prices meet target...")
            self.check_target_price_alerts_mock(wishlist_item, db)
            
            return {"success": True, "message": "Target price updated"}
            
        except Exception as e:
            db.rollback()
            import traceback
            print(f"[TARGET PRICE] ❌ Error updating target price: {traceback.format_exc()}")
            return {"success": False, "message": f"Error updating target price: {str(e)}"}
        finally:
            db.close()
    
    def check_target_price_alerts_mock(self, wishlist_item: WishlistItem, db: Session):
        """Check if any current MOCK price meets the target price"""
        print(f"\n{'='*60}")
        print(f"[PRICE ALERT] Checking alerts for item {wishlist_item.id}")
        print(f"[PRICE ALERT] Product: {wishlist_item.product_name}")
        print(f"{'='*60}")
        
        if not wishlist_item.target_price:
            print(f"[PRICE ALERT] ⚠️ No target price set, skipping")
            return
        
        print(f"[PRICE ALERT] Target price: ₹{wishlist_item.target_price:,.2f}")
        
        try:
            # Get current prices from MOCK DATA (not database)
            mock_offers = self._get_mock_prices(wishlist_item.product_name)
            
            if not mock_offers:
                print(f"[PRICE ALERT] ⚠️ No mock prices found")
                return
            
            print(f"[PRICE ALERT] Found {len(mock_offers)} mock offers")
            
            # Check if any price is at or below target
            alerts_sent = 0
            for offer in mock_offers:
                store = offer.get('store', '').lower().strip()
                price = offer.get('price')
                
                if not store or price is None:
                    continue
                
                print(f"[PRICE ALERT]   - {store}: ₹{price:,.2f}")
                
                if price <= wishlist_item.target_price:
                    print(f"\n[PRICE ALERT] 🎯 TARGET MET! {store}: ₹{price:,.2f} <= ₹{wishlist_item.target_price:,.2f}")
                    
                    # Check if we already sent a notification for this price
                    existing_notification = db.query(PriceNotification).filter(
                        PriceNotification.wishlist_item_id == wishlist_item.id,
                        PriceNotification.store == store,
                        PriceNotification.current_price == price
                    ).first()
                    
                    if existing_notification:
                        print(f"[PRICE ALERT] ℹ️ Notification already sent for this price, skipping")
                        continue
                    
                    print(f"[PRICE ALERT] Creating notification record...")
                    
                    # Create notification record
                    notification = PriceNotification(
                        user_id=wishlist_item.user_id,
                        wishlist_item_id=wishlist_item.id,
                        store=store,
                        current_price=price,
                        target_price=wishlist_item.target_price,
                        product_url=offer.get('url', '')
                    )
                    db.add(notification)
                    db.commit()
                    print(f"[PRICE ALERT] ✅ Notification record created (ID: {notification.id})")
                    
                    # Get user email
                    user = db.query(User).filter(User.id == wishlist_item.user_id).first()
                    if not user or not user.email:
                        print(f"[PRICE ALERT] ⚠️ No email found for user {wishlist_item.user_id}")
                        continue
                    
                    print(f"[PRICE ALERT] Sending email to {user.email}...")
                    
                    # Create mock price history object for email
                    price_data = type('PriceData', (), {
                        'store': store,
                        'price': price,
                        'price_display': offer.get('price_display', f"₹{price:,}"),
                        'product_url': offer.get('url', ''),
                        'product_title': offer.get('title', wishlist_item.product_name),
                        'product_image': offer.get('image')
                    })()
                    
                    # Send email in background thread
                    try:
                        import threading
                        thread = threading.Thread(
                            target=self.send_price_alert_email,
                            args=(wishlist_item, price_data, user.email),
                            daemon=True
                        )
                        thread.start()
                        alerts_sent += 1
                        print(f"[PRICE ALERT] ✅ Email thread started")
                    except Exception as thread_error:
                        print(f"[PRICE ALERT] ❌ Error starting email thread: {str(thread_error)}")
                        import traceback
                        traceback.print_exc()
            
            if alerts_sent == 0:
                print(f"[PRICE ALERT] No prices meet target (all above ₹{wishlist_item.target_price:,.2f})")
            else:
                print(f"[PRICE ALERT] ✅ {alerts_sent} alert(s) triggered")
                
        except Exception as e:
            print(f"[PRICE ALERT] ❌ Error checking alerts: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print(f"{'='*60}\n")
    
    def send_price_alert_email(self, wishlist_item: WishlistItem, price_data, user_email: str):
        """Send email notification for price alert"""
        print(f"\n{'='*60}")
        print(f"[EMAIL] Starting email send process")
        print(f"[EMAIL] To: {user_email}")
        print(f"[EMAIL] Product: {wishlist_item.product_name}")
        print(f"{'='*60}")
        
        try:
            if not user_email:
                print(f"[EMAIL] ❌ No email provided")
                return
            
            # Email configuration
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_username = os.getenv('SMTP_USERNAME', '')
            smtp_password = os.getenv('SMTP_PASSWORD', '')
            
            print(f"[EMAIL] SMTP Config:")
            print(f"[EMAIL]   Server: {smtp_server}:{smtp_port}")
            print(f"[EMAIL]   Username: {smtp_username}")
            print(f"[EMAIL]   Password: {'*' * len(smtp_password) if smtp_password else 'NOT SET'}")
            
            if not smtp_username or not smtp_password:
                print(f"[EMAIL] ❌ SMTP credentials not configured!")
                print(f"[EMAIL] Set SMTP_USERNAME and SMTP_PASSWORD in .env file")
                return
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = user_email
            msg['Subject'] = f"🎉 Price Alert: {wishlist_item.product_name} is now {price_data.price_display}!"
            
            # Calculate savings
            savings = wishlist_item.target_price - price_data.price
            
            # Email body
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #10b981;">🎉 Great News! Your Target Price Has Been Reached!</h2>
                    
                    <div style="background: #f0fdf4; border-left: 4px solid #10b981; padding: 15px; margin: 20px 0;">
                        <p style="margin: 5px 0;"><strong>Product:</strong> {wishlist_item.product_name}</p>
                        <p style="margin: 5px 0;"><strong>Store:</strong> {price_data.store.title()}</p>
                        <p style="margin: 5px 0;"><strong>Current Price:</strong> <span style="color: #10b981; font-size: 1.2em; font-weight: bold;">{price_data.price_display}</span></p>
                        <p style="margin: 5px 0;"><strong>Your Target Price:</strong> ₹{wishlist_item.target_price:,.2f}</p>
                        <p style="margin: 10px 0 0 0;"><strong>You're within budget by:</strong> <span style="color: #10b981; font-size: 1.1em; font-weight: bold;">₹{abs(savings):,.2f}</span>!</p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{price_data.product_url}" style="background-color: #2b59c3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">🛒 Buy Now</a>
                    </div>
                    
                    <p style="color: #666; font-size: 0.9em; margin-top: 30px;">
                        Happy Shopping! 🛍️<br>
                        - AI Shopping Assistant
                    </p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            print(f"[EMAIL] Connecting to SMTP server...")
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            print(f"[EMAIL] Logging in...")
            server.login(smtp_username, smtp_password)
            print(f"[EMAIL] Sending email...")
            text = msg.as_string()
            server.sendmail(smtp_username, user_email, text)
            server.quit()
            
            print(f"[EMAIL] ✅ Email sent successfully to {user_email}!")
            print(f"{'='*60}\n")
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"[EMAIL] ❌ SMTP Authentication Error: {str(e)}")
            print(f"[EMAIL] Check your SMTP_USERNAME and SMTP_PASSWORD")
            print(f"[EMAIL] For Gmail, use an App Password from: https://myaccount.google.com/apppasswords")
        except Exception as e:
            print(f"[EMAIL] ❌ Error sending email: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            print(f"{'='*60}\n")

# Global instance
wishlist_service = WishlistService()