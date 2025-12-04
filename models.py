"""
SQLAlchemy models for ERP system
Defines database schema for products, sales, users, and financial records
"""

from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from config import DATABASE_URL

Base = declarative_base()


class Product(Base):
    """Product model for inventory management"""
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100))
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship with sales
    sales = relationship('Sale', back_populates='product', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', stock={self.stock})>"


class Sale(Base):
    """Sales transaction model"""
    __tablename__ = 'sales'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    customer_name = Column(String(200))
    quantity = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)
    sale_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship with product
    product = relationship('Product', back_populates='sales')

    def __repr__(self):
        return f"<Sale(id={self.id}, product_id={self.product_id}, quantity={self.quantity})>"


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(256))
    role = Column(String(50))  # admin, manager, cashier
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class FinancialRecord(Base):
    """Financial records model for income and expenses tracking"""
    __tablename__ = 'financial_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_type = Column(String(50))  # income or expense
    amount = Column(Float)
    category = Column(String(100))
    description = Column(Text)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<FinancialRecord(id={self.id}, type='{self.transaction_type}', amount={self.amount})>"


# Database initialization functions
def get_engine():
    """Create and return database engine"""
    # For SQLite, we need to allow multi-threaded access for Streamlit
    return create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )


def init_db():
    """Initialize database by creating all tables"""
    engine = get_engine()
    Base.metadata.create_all(engine)
    print("Database tables created successfully!")
    return engine


def SessionLocal():
    """Create and return a new database session"""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == "__main__":
    # Create tables if running this file directly
    init_db()
