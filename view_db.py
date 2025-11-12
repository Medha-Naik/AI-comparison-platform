"""
Simple database viewer for AI Shopping Assistant
Run this with: python view_db.py
"""
import sys
import os

# Try using SQLAlchemy models if available
try:
    from models import SessionLocal, User, WishlistItem, PriceHistory, PriceNotification
    from sqlalchemy import func
    USE_MODELS = True
except ImportError:
    # Fallback to raw SQLite if models not available
    import sqlite3
    USE_MODELS = False

def view_database():
    db = SessionLocal()
    
    print("=" * 80)
    print("AI SHOPPING ASSISTANT DATABASE")
    print("=" * 80)
    
    # Users
    print("\n📊 USERS")
    print("-" * 80)
    users = db.query(User).all()
    if users:
        for user in users:
            print(f"ID: {user.id} | Email: {user.email} | Name: {user.name}")
            print(f"   Created: {user.created_at} | Active: {user.is_active}")
            print(f"   Wishlist Items: {len(user.wishlist_items)} | Notifications: {len(user.notifications)}")
            print()
    else:
        print("No users found.")
    
    # Wishlist Items
    print("\n🛍️  WISHLIST ITEMS")
    print("-" * 80)
    wishlist_items = db.query(WishlistItem).all()
    if wishlist_items:
        for item in wishlist_items:
            user = db.query(User).filter(User.id == item.user_id).first()
            print(f"ID: {item.id} | Product: {item.product_name}")
            print(f"   User: {user.email if user else 'Unknown'}")
            print(f"   Category: {item.product_category} | Target Price: ₹{item.target_price}")
            print(f"   Created: {item.created_at} | Active: {item.is_active}")
            print(f"   Price Records: {len(item.price_history)}")
            print()
    else:
        print("No wishlist items found.")
    
    # Price History
    print("\n💰 PRICE HISTORY")
    print("-" * 80)
    price_history = db.query(PriceHistory).order_by(PriceHistory.recorded_at.desc()).limit(20).all()
    if price_history:
        for record in price_history:
            item = db.query(WishlistItem).filter(WishlistItem.id == record.wishlist_item_id).first()
            print(f"ID: {record.id} | Product: {item.product_name if item else 'Unknown'}")
            print(f"   Store: {record.store} | Price: {record.price_display}")
            print(f"   Recorded: {record.recorded_at}")
            if record.product_url:
                print(f"   URL: {record.product_url[:60]}...")
            print()
    else:
        print("No price history found.")
    
    # Price Notifications
    print("\n🔔 PRICE NOTIFICATIONS")
    print("-" * 80)
    notifications = db.query(PriceNotification).order_by(PriceNotification.sent_at.desc()).all()
    if notifications:
        for notif in notifications:
            user = db.query(User).filter(User.id == notif.user_id).first()
            item = db.query(WishlistItem).filter(WishlistItem.id == notif.wishlist_item_id).first()
            print(f"ID: {notif.id} | User: {user.email if user else 'Unknown'}")
            print(f"   Product: {item.product_name if item else 'Unknown'}")
            print(f"   Store: {notif.store} | Current: ₹{notif.current_price} | Target: ₹{notif.target_price}")
            print(f"   Sent: {notif.sent_at} | Read: {notif.is_read}")
            print()
    else:
        print("No notifications found.")
    
    # Statistics
    print("\n📈 STATISTICS")
    print("-" * 80)
    user_count = db.query(func.count(User.id)).scalar()
    wishlist_count = db.query(func.count(WishlistItem.id)).scalar()
    price_records = db.query(func.count(PriceHistory.id)).scalar()
    notification_count = db.query(func.count(PriceNotification.id)).scalar()
    
    print(f"Total Users: {user_count}")
    print(f"Total Wishlist Items: {wishlist_count}")
    print(f"Total Price Records: {price_records}")
    print(f"Total Notifications: {notification_count}")
    
    db.close()

if __name__ == "__main__":
    view_database()