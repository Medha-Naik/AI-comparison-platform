"""
Database models for the AI Shopping Assistant
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
from werkzeug.security import generate_password_hash, check_password_hash

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///shopping_assistant.db')
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    """User model for wishlist and notifications"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    wishlist_items = relationship("WishlistItem", back_populates="user")
    notifications = relationship("PriceNotification", back_populates="user")

    # Password helpers
    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

class WishlistItem(Base):
    """Wishlist items - products user wants to track"""
    __tablename__ = "wishlist_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_name = Column(String, nullable=False)  # e.g., "iPhone 15"
    product_category = Column(String, nullable=True)  # e.g., "Smartphones"
    target_price = Column(Float, nullable=True)  # User's target price
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="wishlist_items")
    price_history = relationship("PriceHistory", back_populates="wishlist_item")
    notifications = relationship("PriceNotification", back_populates="wishlist_item")

class PriceHistory(Base):
    """Price history for wishlist items across all platforms"""
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    wishlist_item_id = Column(Integer, ForeignKey("wishlist_items.id"), nullable=False)
    store = Column(String, nullable=False)  # e.g., "flipkart", "amazon"
    price = Column(Float, nullable=False)
    price_display = Column(String, nullable=False)  # e.g., "₹79,999"
    product_url = Column(String, nullable=True)
    product_title = Column(String, nullable=True)
    product_image = Column(String, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    wishlist_item = relationship("WishlistItem", back_populates="price_history")

class PriceNotification(Base):
    """Price notifications sent to users"""
    __tablename__ = "price_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    wishlist_item_id = Column(Integer, ForeignKey("wishlist_items.id"), nullable=False)
    store = Column(String, nullable=False)
    current_price = Column(Float, nullable=False)
    target_price = Column(Float, nullable=False)
    product_url = Column(String, nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    wishlist_item = relationship("WishlistItem", back_populates="notifications")

# Create all tables
def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database
if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully!")

