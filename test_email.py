"""
Test email notifications with static mock data
Place in backend/ directory and run: python test_static_email.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

def test_add_with_high_target():
    """Add product with target ABOVE current mock prices (should NOT trigger)"""
    print("\n" + "="*60)
    print("1️⃣  TEST: Target price ABOVE mock prices (no alert expected)")
    print("="*60)
    
    from services.wishlist_service import wishlist_service
    
    test_email = os.getenv('SMTP_USERNAME', 'medhanaik1409@gmail.com')
    
    print(f"📧 Test user: {test_email}")
    print(f"🛍️  Product: iPhone 15")
    print(f"💰 Target: ₹70,000 (ABOVE current mock prices)")
    print(f"📊 Expected: No email (prices are ~59-62k)")
    
    result = wishlist_service.add_to_wishlist(
        user_email=test_email,
        product_name="iPhone 15",
        product_category="Smartphones",
        target_price=70000.0
    )
    
    print(f"\n✅ Result: {result}")

def test_add_with_low_target():
    """Add product with target BELOW current mock prices (should trigger email!)"""
    print("\n" + "="*60)
    print("2️⃣  TEST: Target price BELOW mock prices (ALERT EXPECTED!)")
    print("="*60)
    
    from services.wishlist_service import wishlist_service
    from models import get_db, WishlistItem
    
    test_email = os.getenv('SMTP_USERNAME', 'medhanaik1409@gmail.com')
    
    # First, remove existing iPhone 15 items to start fresh
    db = next(get_db())
    try:
        from models import User
        user = db.query(User).filter(User.email == test_email).first()
        if user:
            existing_items = db.query(WishlistItem).filter(
                WishlistItem.user_id == user.id,
                WishlistItem.product_name.like("%iPhone 15%"),
                WishlistItem.is_active == True
            ).all()
            for item in existing_items:
                item.is_active = False
            db.commit()
            print(f"🗑️  Cleaned up {len(existing_items)} existing iPhone items")
    finally:
        db.close()
    
    print(f"\n📧 Test user: {test_email}")
    print(f"🛍️  Product: iPhone 15")
    print(f"💰 Target: ₹65,000 (BELOW current mock prices)")
    print(f"📊 Mock prices: Flipkart ₹59,900, Croma ₹59,490, Amazon ₹61,999")
    print(f"✉️  Expected: EMAIL ALERT! (3-4 stores meet target)")
    
    result = wishlist_service.add_to_wishlist(
        user_email=test_email,
        product_name="iPhone 15",
        product_category="Smartphones",
        target_price=65000.0  # Above all mock prices, so ALL will trigger!
    )
    
    print(f"\n📋 Result: {result}")
    
    if result['success']:
        print(f"\n⏳ Waiting 3 seconds for email threads...")
        import time
        time.sleep(3)
        print(f"\n📬 CHECK YOUR EMAIL NOW!")
        print(f"   - Email: {test_email}")
        print(f"   - Subject: 🎉 Price Alert: iPhone 15...")
        print(f"   - Check spam folder too!")

def test_update_target_to_trigger():
    """Update target price to trigger alert on existing item"""
    print("\n" + "="*60)
    print("3️⃣  TEST: Update target price to trigger alert")
    print("="*60)
    
    from services.wishlist_service import wishlist_service
    from models import get_db, WishlistItem, User
    
    test_email = os.getenv('SMTP_USERNAME', 'medhanaik1409@gmail.com')
    
    # Get the most recent iPhone 15 item
    db = next(get_db())
    try:
        user = db.query(User).filter(User.email == test_email).first()
        if not user:
            print(f"❌ User not found")
            return
        
        item = db.query(WishlistItem).filter(
            WishlistItem.user_id == user.id,
            WishlistItem.product_name.like("%iPhone 15%"),
            WishlistItem.is_active == True
        ).first()
        
        if not item:
            print(f"❌ No iPhone 15 in wishlist. Run test 2 first.")
            return
        
        print(f"🆔 Wishlist Item ID: {item.id}")
        print(f"📱 Product: {item.product_name}")
        print(f"💰 Current target: ₹{item.target_price:,.2f}")
        print(f"💰 New target: ₹60,000 (to trigger Croma & Flipkart)")
        
    finally:
        db.close()
    
    result = wishlist_service.update_target_price(
        user_email=test_email,
        wishlist_item_id=item.id,
        target_price=60000.0
    )
    
    print(f"\n📋 Result: {result}")
    
    if result['success']:
        print(f"\n⏳ Waiting 3 seconds for email threads...")
        import time
        time.sleep(3)
        print(f"\n📬 CHECK YOUR EMAIL for new alerts!")

def check_notifications():
    """Check what's in the notifications table"""
    print("\n" + "="*60)
    print("4️⃣  NOTIFICATION DATABASE CHECK")
    print("="*60)
    
    from models import get_db, PriceNotification, User, WishlistItem
    
    db = next(get_db())
    try:
        notifications = db.query(PriceNotification).order_by(
            PriceNotification.sent_at.desc()
        ).limit(10).all()
        
        print(f"📧 Total notifications: {db.query(PriceNotification).count()}")
        print(f"📋 Showing last {len(notifications)} notifications:\n")
        
        for notif in notifications:
            user = db.query(User).filter(User.id == notif.user_id).first()
            item = db.query(WishlistItem).filter(WishlistItem.id == notif.wishlist_item_id).first()
            
            print(f"   🔔 ID {notif.id}")
            print(f"      User: {user.email if user else 'Unknown'}")
            print(f"      Product: {item.product_name if item else 'Unknown'}")
            print(f"      Store: {notif.store}")
            print(f"      Price: ₹{notif.current_price:,.2f} (Target: ₹{notif.target_price:,.2f})")
            print(f"      Sent: {notif.sent_at}")
            print()
    finally:
        db.close()

def main():
    print("\n🧪 AI SHOPPING ASSISTANT - STATIC MOCK DATA EMAIL TEST")
    print("="*60)
    
    # Show mock data info
    try:
        from data.mock_data import load_products
        products = load_products()
        if 'iphone 15' in products:
            print(f"\n📊 Mock data for 'iPhone 15':")
            for offer in products['iphone 15']:
                print(f"   - {offer['store']}: ₹{offer['price']:,}")
    except:
        pass
    
    print("\n" + "="*60)
    print("Choose a test:")
    print("1. Add with HIGH target (no alert)")
    print("2. Add with LOW target (TRIGGERS EMAIL!) ⭐")
    print("3. Update target price (may trigger)")
    print("4. Check notification database")
    print("5. Run all tests")
    print("="*60)
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1":
        test_add_with_high_target()
    elif choice == "2":
        test_add_with_low_target()
    elif choice == "3":
        test_update_target_to_trigger()
    elif choice == "4":
        check_notifications()
    elif choice == "5":
        test_add_with_high_target()
        test_add_with_low_target()
        test_update_target_to_trigger()
        check_notifications()
    else:
        print("Invalid choice!")
    
    print("\n" + "="*60)
    print("✅ Test complete!")
    print("="*60)

if __name__ == "__main__":
    main()