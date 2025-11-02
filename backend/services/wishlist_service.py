"""
Wishlist service for managing user wishlists and price tracking
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import get_db, WishlistItem, PriceHistory, PriceNotification, User
from scrapers.safe_scrapers import search_with_fallback
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
        # Don't create DB session here - sessions should be created per request
        # This prevents session leaks and thread safety issues
        pass
    
    def _get_db(self):
        """Get a new database session"""
        return next(get_db())
    
    def add_to_wishlist(self, user_email: str, product_name: str, 
                       product_category: str = None, target_price: float = None) -> Dict:
        """Add a product to user's wishlist"""
        db = self._get_db()
        try:
            # Get or create user
            user = db.query(User).filter(User.email == user_email).first()
            if not user:
                user = User(email=user_email)
                db.add(user)
                db.commit()
                db.refresh(user)
            
            # Check if product already exists in wishlist
            existing_item = db.query(WishlistItem).filter(
                WishlistItem.user_id == user.id,
                WishlistItem.product_name == product_name,
                WishlistItem.is_active == True
            ).first()
            
            if existing_item:
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
            
            # Immediately fetch current prices
            self.update_prices_for_item(wishlist_item.id)
            
            return {
                "success": True,
                "message": "Product added to wishlist",
                "wishlist_item_id": wishlist_item.id
            }
            
        except Exception as e:
            db.rollback()
            import traceback
            print(f"[WishlistService] Error adding to wishlist: {traceback.format_exc()}")
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
            print(f"[WishlistService] Error removing from wishlist: {traceback.format_exc()}")
            return {"success": False, "message": f"Error removing from wishlist: {str(e)}"}
        finally:
            db.close()
    
    def get_wishlist(self, user_email: str) -> List[Dict]:
        """Get user's wishlist with current prices"""
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
                # Get latest prices for each store
                latest_prices = db.query(PriceHistory).filter(
                    PriceHistory.wishlist_item_id == item.id
                ).order_by(PriceHistory.recorded_at.desc()).all()
                
                # Group by store and get latest price for each
                store_prices = {}
                for price in latest_prices:
                    if price.store not in store_prices:
                        store_prices[price.store] = {
                            "price": price.price,
                            "price_display": price.price_display,
                            "url": price.product_url,
                            "title": price.product_title,
                            "image": price.product_image,
                            "recorded_at": price.recorded_at.isoformat()
                        }
                
                result.append({
                    "id": item.id,
                    "product_name": item.product_name,
                    "product_category": item.product_category,
                    "target_price": item.target_price,
                    "created_at": item.created_at.isoformat(),
                    "current_prices": store_prices,
                    "lowest_price": min([p["price"] for p in store_prices.values()]) if store_prices else None
                })
            
            return result
            
        except Exception as e:
            import traceback
            print(f"[WishlistService] Error getting wishlist: {traceback.format_exc()}")
            return []
        finally:
            db.close()
    
    def update_target_price(self, user_email: str, wishlist_item_id: int, target_price: float) -> Dict:
        """Update target price for a wishlist item"""
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
            
            wishlist_item.target_price = target_price
            db.commit()
            db.refresh(wishlist_item)
            
            # Check if current prices already meet the new target price
            # This ensures email is sent immediately if target is set below current price
            self.check_target_price_alerts(wishlist_item, db)
            
            return {"success": True, "message": "Target price updated"}
            
        except Exception as e:
            db.rollback()
            import traceback
            print(f"[WishlistService] Error updating target price: {traceback.format_exc()}")
            return {"success": False, "message": f"Error updating target price: {str(e)}"}
        finally:
            db.close()
    
    def update_prices_for_item(self, wishlist_item_id: int) -> Dict:
        """Update prices for a specific wishlist item"""
        db = self._get_db()
        try:
            wishlist_item = db.query(WishlistItem).filter(
                WishlistItem.id == wishlist_item_id
            ).first()
            
            if not wishlist_item:
                return {"success": False, "message": "Wishlist item not found"}
            
            # Search for the product across all platforms
            search_results = search_with_fallback(wishlist_item.product_name)
            
            if not search_results or not search_results.get('offers'):
                return {"success": False, "message": "No products found"}
            
            # Store price history for each offer
            for offer in search_results['offers']:
                price_history = PriceHistory(
                    wishlist_item_id=wishlist_item.id,
                    store=offer['store'],
                    price=offer['price'],
                    price_display=offer['price_display'],
                    product_url=offer['url'],
                    product_title=offer['title'],
                    product_image=offer.get('image')
                )
                db.add(price_history)
            
            db.commit()
            
            # Check for target price alerts (pass db session)
            self.check_target_price_alerts(wishlist_item, db)
            
            return {"success": True, "message": "Prices updated successfully"}
            
        except Exception as e:
            db.rollback()
            import traceback
            print(f"[WishlistService] Error updating prices: {traceback.format_exc()}")
            return {"success": False, "message": f"Error updating prices: {str(e)}"}
        finally:
            db.close()
    
    def check_target_price_alerts(self, wishlist_item: WishlistItem, db=None):
        """Check if any current price meets the target price"""
        if not wishlist_item.target_price:
            print(f"[PRICE ALERT] No target price set for item {wishlist_item.id}, skipping check")
            return
        
        print(f"[PRICE ALERT] Checking alerts for item {wishlist_item.id} '{wishlist_item.product_name}' with target price ₹{wishlist_item.target_price:,.2f}")
        
        # Use provided db session or create a new one
        if db is None:
            db = self._get_db()
            should_close = True
        else:
            should_close = False
        
        try:
            # Get latest prices for this item
            latest_prices = db.query(PriceHistory).filter(
                PriceHistory.wishlist_item_id == wishlist_item.id
            ).order_by(PriceHistory.recorded_at.desc()).all()
            
            if not latest_prices:
                print(f"[PRICE ALERT] No price history found for item {wishlist_item.id}")
                return
            
            # Group by store and get latest price for each
            store_prices = {}
            for price in latest_prices:
                if price.store not in store_prices:
                    store_prices[price.store] = price
            
            print(f"[PRICE ALERT] Found {len(store_prices)} stores with prices: {list(store_prices.keys())}")
            
            # Check if any price is at or below target
            for store, price_data in store_prices.items():
                print(f"[PRICE ALERT] Checking {store}: Current price ₹{price_data.price:,.2f} vs Target ₹{wishlist_item.target_price:,.2f}")
                if price_data.price <= wishlist_item.target_price:
                    print(f"[PRICE ALERT] ✅ Price condition met! {store} price ₹{price_data.price:,.2f} <= target ₹{wishlist_item.target_price:,.2f}")
                    # Check if we already sent a notification for this exact price
                    existing_notification = db.query(PriceNotification).filter(
                        PriceNotification.wishlist_item_id == wishlist_item.id,
                        PriceNotification.store == store,
                        PriceNotification.current_price == price_data.price
                    ).first()
                    
                    if not existing_notification:
                        print(f"[PRICE ALERT] No existing notification found, creating new one...")
                        try:
                            # Create notification record first
                            notification = PriceNotification(
                                user_id=wishlist_item.user_id,
                                wishlist_item_id=wishlist_item.id,
                                store=store,
                                current_price=price_data.price,
                                target_price=wishlist_item.target_price,
                                product_url=price_data.product_url
                            )
                            db.add(notification)
                            db.commit()
                            print(f"[PRICE ALERT] ✅ Created notification record for item {wishlist_item.id}, store {store}, price ₹{price_data.price:,.2f}")
                            
                            # Get user email before starting thread
                            user = db.query(User).filter(User.id == wishlist_item.user_id).first()
                            user_email = user.email if user else None
                            
                            # Send email notification asynchronously (don't block)
                            if user_email:
                                print(f"[PRICE ALERT] User email found: {user_email}, starting email thread...")
                                try:
                                    import threading
                                    thread = threading.Thread(
                                        target=self.send_price_alert_email,
                                        args=(wishlist_item, price_data, user_email),
                                        daemon=True
                                    )
                                    thread.start()
                                    print(f"[PRICE ALERT] ✅ Started email thread for '{wishlist_item.product_name}' to {user_email}")
                                except Exception as email_thread_error:
                                    print(f"[PRICE ALERT] ❌ Error starting email thread: {str(email_thread_error)}")
                                    import traceback
                                    traceback.print_exc()
                            else:
                                print(f"[PRICE ALERT] ⚠️  No email found for user {wishlist_item.user_id}, skipping email notification")
                        except Exception as e:
                            db.rollback()
                            print(f"[PRICE ALERT] ❌ Error creating notification: {str(e)}")
                            import traceback
                            traceback.print_exc()
                    else:
                        print(f"[PRICE ALERT] ⚠️  Notification already exists for this price, skipping duplicate")
        finally:
            if should_close:
                db.close()
    
    def send_price_alert_email(self, wishlist_item: WishlistItem, price_data: PriceHistory, user_email: str):
        """Send email notification for price alert (runs in background thread)"""
        try:
            if not user_email:
                print(f"[EMAIL] Skipping email - no email provided for user {wishlist_item.user_id}")
                return
            
            # Email configuration (you'll need to set these in environment variables)
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_username = os.getenv('SMTP_USERNAME', '')
            smtp_password = os.getenv('SMTP_PASSWORD', '')
            
            if not smtp_username or not smtp_password:
                print(f"[EMAIL] ❌ SMTP NOT CONFIGURED - Emails will not be sent")
                print(f"[EMAIL] ============================================================")
                print(f"[EMAIL] To enable email notifications, set these environment variables:")
                print(f"[EMAIL]   SMTP_SERVER=smtp.gmail.com")
                print(f"[EMAIL]   SMTP_PORT=587")
                print(f"[EMAIL]   SMTP_USERNAME=your.email@gmail.com")
                print(f"[EMAIL]   SMTP_PASSWORD=your-app-password")
                print(f"[EMAIL]")
                print(f"[EMAIL] Gmail Setup Instructions:")
                print(f"[EMAIL]   1. Enable 2-Factor Authentication on your Google account")
                print(f"[EMAIL]   2. Go to: https://myaccount.google.com/apppasswords")
                print(f"[EMAIL]   3. Generate an App Password for 'Mail'")
                print(f"[EMAIL]   4. Use that 16-character password as SMTP_PASSWORD")
                print(f"[EMAIL] ============================================================")
                return
            
            print(f"[EMAIL] Attempting to send price alert to {user_email} for {wishlist_item.product_name}")
            
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
                        <p style="margin: 10px 0 0 0;"><strong>You saved:</strong> <span style="color: #10b981; font-size: 1.1em; font-weight: bold;">₹{savings:,.2f}</span>!</p>
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
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            text = msg.as_string()
            server.sendmail(smtp_username, user_email, text)
            server.quit()
            
            print(f"[EMAIL] ✅ Price alert email successfully sent to {user_email}")
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"[EMAIL] ❌ SMTP Authentication Error: {str(e)}")
            print(f"[EMAIL] Check your SMTP_USERNAME and SMTP_PASSWORD. For Gmail, use an App Password.")
        except smtplib.SMTPException as e:
            print(f"[EMAIL] ❌ SMTP Error: {str(e)}")
        except Exception as e:
            print(f"[EMAIL] ❌ Error sending email: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def update_all_prices(self) -> Dict:
        """Update prices for all active wishlist items"""
        db = self._get_db()
        try:
            active_items = db.query(WishlistItem).filter(
                WishlistItem.is_active == True
            ).all()
            
            updated_count = 0
            for item in active_items:
                result = self.update_prices_for_item(item.id)
                if result['success']:
                    updated_count += 1
            
            return {
                "success": True,
                "message": f"Updated prices for {updated_count} wishlist items"
            }
            
        except Exception as e:
            import traceback
            print(f"[WishlistService] Error updating all prices: {traceback.format_exc()}")
            return {"success": False, "message": f"Error updating all prices: {str(e)}"}
        finally:
            db.close()

# Global instance
wishlist_service = WishlistService()






