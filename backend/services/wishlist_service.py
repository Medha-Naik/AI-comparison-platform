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
        self.db = next(get_db())
    
    def add_to_wishlist(self, user_email: str, product_name: str, 
                       product_category: str = None, target_price: float = None) -> Dict:
        """Add a product to user's wishlist"""
        try:
            # Get or create user
            user = self.db.query(User).filter(User.email == user_email).first()
            if not user:
                user = User(email=user_email)
                self.db.add(user)
                self.db.commit()
                self.db.refresh(user)
            
            # Check if product already exists in wishlist
            existing_item = self.db.query(WishlistItem).filter(
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
            
            self.db.add(wishlist_item)
            self.db.commit()
            self.db.refresh(wishlist_item)
            
            # Immediately fetch current prices
            self.update_prices_for_item(wishlist_item.id)
            
            return {
                "success": True,
                "message": "Product added to wishlist",
                "wishlist_item_id": wishlist_item.id
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "message": f"Error adding to wishlist: {str(e)}"
            }
    
    def remove_from_wishlist(self, user_email: str, wishlist_item_id: int) -> Dict:
        """Remove a product from user's wishlist"""
        try:
            user = self.db.query(User).filter(User.email == user_email).first()
            if not user:
                return {"success": False, "message": "User not found"}
            
            wishlist_item = self.db.query(WishlistItem).filter(
                WishlistItem.id == wishlist_item_id,
                WishlistItem.user_id == user.id
            ).first()
            
            if not wishlist_item:
                return {"success": False, "message": "Wishlist item not found"}
            
            # Soft delete
            wishlist_item.is_active = False
            self.db.commit()
            
            return {"success": True, "message": "Product removed from wishlist"}
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "message": f"Error removing from wishlist: {str(e)}"}
    
    def get_wishlist(self, user_email: str) -> List[Dict]:
        """Get user's wishlist with current prices"""
        try:
            user = self.db.query(User).filter(User.email == user_email).first()
            if not user:
                return []
            
            wishlist_items = self.db.query(WishlistItem).filter(
                WishlistItem.user_id == user.id,
                WishlistItem.is_active == True
            ).all()
            
            result = []
            for item in wishlist_items:
                # Get latest prices for each store
                latest_prices = self.db.query(PriceHistory).filter(
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
            return []
    
    def update_target_price(self, user_email: str, wishlist_item_id: int, target_price: float) -> Dict:
        """Update target price for a wishlist item"""
        try:
            user = self.db.query(User).filter(User.email == user_email).first()
            if not user:
                return {"success": False, "message": "User not found"}
            
            wishlist_item = self.db.query(WishlistItem).filter(
                WishlistItem.id == wishlist_item_id,
                WishlistItem.user_id == user.id
            ).first()
            
            if not wishlist_item:
                return {"success": False, "message": "Wishlist item not found"}
            
            wishlist_item.target_price = target_price
            self.db.commit()
            
            return {"success": True, "message": "Target price updated"}
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "message": f"Error updating target price: {str(e)}"}
    
    def update_prices_for_item(self, wishlist_item_id: int) -> Dict:
        """Update prices for a specific wishlist item"""
        try:
            wishlist_item = self.db.query(WishlistItem).filter(
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
                self.db.add(price_history)
            
            self.db.commit()
            
            # Check for target price alerts
            self.check_target_price_alerts(wishlist_item)
            
            return {"success": True, "message": "Prices updated successfully"}
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "message": f"Error updating prices: {str(e)}"}
    
    def check_target_price_alerts(self, wishlist_item: WishlistItem):
        """Check if any current price meets the target price"""
        if not wishlist_item.target_price:
            return
        
        # Get latest prices for this item
        latest_prices = self.db.query(PriceHistory).filter(
            PriceHistory.wishlist_item_id == wishlist_item.id
        ).order_by(PriceHistory.recorded_at.desc()).all()
        
        # Group by store and get latest price for each
        store_prices = {}
        for price in latest_prices:
            if price.store not in store_prices:
                store_prices[price.store] = price
        
        # Check if any price is at or below target
        for store, price_data in store_prices.items():
            if price_data.price <= wishlist_item.target_price:
                # Check if we already sent a notification for this price
                existing_notification = self.db.query(PriceNotification).filter(
                    PriceNotification.wishlist_item_id == wishlist_item.id,
                    PriceNotification.store == store,
                    PriceNotification.current_price == price_data.price
                ).first()
                
                if not existing_notification:
                    # Create notification
                    notification = PriceNotification(
                        user_id=wishlist_item.user_id,
                        wishlist_item_id=wishlist_item.id,
                        store=store,
                        current_price=price_data.price,
                        target_price=wishlist_item.target_price,
                        product_url=price_data.product_url
                    )
                    self.db.add(notification)
                    self.db.commit()
                    
                    # Send email notification
                    self.send_price_alert_email(wishlist_item, price_data)
    
    def send_price_alert_email(self, wishlist_item: WishlistItem, price_data: PriceHistory):
        """Send email notification for price alert"""
        try:
            user = self.db.query(User).filter(User.id == wishlist_item.user_id).first()
            if not user or not user.email:
                return
            
            # Email configuration (you'll need to set these in environment variables)
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_username = os.getenv('SMTP_USERNAME', '')
            smtp_password = os.getenv('SMTP_PASSWORD', '')
            
            if not smtp_username or not smtp_password:
                print(f"Email notification skipped - SMTP not configured")
                return
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = user.email
            msg['Subject'] = f"🎉 Price Alert: {wishlist_item.product_name} is now {price_data.price_display}!"
            
            # Email body
            body = f"""
            <h2>🎉 Great News! Your Target Price Has Been Reached!</h2>
            
            <p><strong>Product:</strong> {wishlist_item.product_name}</p>
            <p><strong>Store:</strong> {price_data.store.title()}</p>
            <p><strong>Current Price:</strong> {price_data.price_display}</p>
            <p><strong>Your Target Price:</strong> ₹{wishlist_item.target_price:,.2f}</p>
            
            <p>You saved <strong>₹{wishlist_item.target_price - price_data.price:,.2f}</strong>!</p>
            
            <p><a href="{price_data.product_url}" style="background-color: #2b59c3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Buy Now</a></p>
            
            <p>Happy Shopping! 🛍️</p>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            text = msg.as_string()
            server.sendmail(smtp_username, user.email, text)
            server.quit()
            
            print(f"Price alert email sent to {user.email}")
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
    
    def update_all_prices(self) -> Dict:
        """Update prices for all active wishlist items"""
        try:
            active_items = self.db.query(WishlistItem).filter(
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
            return {"success": False, "message": f"Error updating all prices: {str(e)}"}

# Global instance
wishlist_service = WishlistService()






