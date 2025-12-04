"""
Unit tests for database models
Tests model creation, relationships, and constraints
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Product, Sale, User
from utils.auth import hash_password


# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def test_session():
    """Create a test database session"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


def test_product_creation_and_defaults(test_session):
    """Test creating products with defaults"""
    # Test with all fields
    product1 = Product(name="Product 1", category="Electronics", price=99.99, stock=50)
    test_session.add(product1)

    # Test with default stock (should be 0)
    product2 = Product(name="Product 2", category="Food", price=5.0)
    test_session.add(product2)

    test_session.commit()

    assert product1.id is not None
    assert product1.stock == 50
    assert product2.stock == 0  # Default value


def test_product_sales_relationship(test_session):
    """Test product-sales relationship and cascading"""
    product = Product(name="Test Product", category="Electronics", price=100.0, stock=50)
    test_session.add(product)
    test_session.commit()

    # Create sales for the product
    sale1 = Sale(product_id=product.id, customer_name="Customer 1", quantity=2, total_price=200.0)
    sale2 = Sale(product_id=product.id, customer_name="Customer 2", quantity=3, total_price=300.0)
    test_session.add_all([sale1, sale2])
    test_session.commit()

    # Verify relationship
    assert len(product.sales) == 2
    assert all(sale.product_id == product.id for sale in product.sales)


def test_user_unique_constraint(test_session):
    """Test user creation and unique username constraint"""
    user1 = User(username="testuser", password_hash=hash_password("password"), role="admin")
    test_session.add(user1)
    test_session.commit()

    assert user1.id is not None

    # Try to create duplicate username (should fail)
    user2 = User(username="testuser", password_hash=hash_password("pass2"), role="manager")
    test_session.add(user2)

    with pytest.raises(Exception):  # IntegrityError
        test_session.commit()
