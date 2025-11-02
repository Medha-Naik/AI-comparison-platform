"""
Price tracking scheduler - runs periodically to update wishlist prices
"""
import schedule
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.wishlist_service import wishlist_service
from models import create_tables

def update_all_wishlist_prices():
    """Update prices for all wishlist items"""
    print(f"[Scheduler] Starting price update at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        result = wishlist_service.update_all_prices()
        if result['success']:
            print(f"[Scheduler]  {result['message']}")
        else:
            print(f"[Scheduler]  {result['message']}")
    except Exception as e:
        print(f"[Scheduler] Error: {str(e)}")

def main():
    """Main scheduler function"""
    print("🕐 Starting Price Tracking Scheduler")
    print("="*50)
    
    # Create database tables
    create_tables()
    
    # Schedule price updates every 6 hours
    schedule.every(6).hours.do(update_all_wishlist_prices)
    
    # Also run once immediately
    update_all_wishlist_prices()
    
    print("📅 Scheduler configured:")
    print("   - Price updates every 6 hours")
    print("   - Press Ctrl+C to stop")
    print("="*50)
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n Scheduler stopped by user")

if __name__ == "__main__":
    main()






