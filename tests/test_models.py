"""
Unit tests for database models
Tests basic model creation and relationships
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Product, Sale, User, FinancialRecord
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


def test_create_product(test_session):
    """Test creating a product"""
    product = Product(
        name="Test Product",
        category="Electronics",
        price=99.99,
        stock=50
    )

    test_session.add(product)
    test_session.commit()

    # Verify product was created
    assert product.id is not None
    assert product.name == "Test Product"
    assert product.category == "Electronics"
    assert product.price == 99.99
    assert product.stock == 50
    assert isinstance(product.created_at, datetime)


def test_create_sale(test_session):
    """Test creating a sale"""
    # First create a product
    product = Product(
        name="Test Product",
        category="Electronics",
        price=50.0,
        stock=100
    )
    test_session.add(product)
    test_session.commit()

    # Create a sale
    sale = Sale(
        product_id=product.id,
        customer_name="John Doe",
        quantity=5,
        total_price=250.0
    )

    test_session.add(sale)
    test_session.commit()

    # Verify sale was created
    assert sale.id is not None
    assert sale.product_id == product.id
    assert sale.customer_name == "John Doe"
    assert sale.quantity == 5
    assert sale.total_price == 250.0
    assert isinstance(sale.sale_date, datetime)


def test_product_relationship(test_session):
    """Test product-sales relationship"""
    # Create a product
    product = Product(
        name="Test Product",
        category="Electronics",
        price=100.0,
        stock=50
    )
    test_session.add(product)
    test_session.commit()

    # Create multiple sales for the product
    sale1 = Sale(
        product_id=product.id,
        customer_name="Customer 1",
        quantity=2,
        total_price=200.0
    )

    sale2 = Sale(
        product_id=product.id,
        customer_name="Customer 2",
        quantity=3,
        total_price=300.0
    )

    test_session.add(sale1)
    test_session.add(sale2)
    test_session.commit()

    # Verify relationship
    assert len(product.sales) == 2
    assert product.sales[0].customer_name in ["Customer 1", "Customer 2"]
    assert product.sales[1].customer_name in ["Customer 1", "Customer 2"]


def test_create_user(test_session):
    """Test creating a user"""
    user = User(
        username="testuser",
        password_hash=hash_password("password123"),
        role="admin"
    )

    test_session.add(user)
    test_session.commit()

    # Verify user was created
    assert user.id is not None
    assert user.username == "testuser"
    assert user.role == "admin"
    assert isinstance(user.created_at, datetime)
    assert user.password_hash is not None


def test_create_financial_record(test_session):
    """Test creating a financial record"""
    record = FinancialRecord(
        transaction_type="income",
        amount=500.0,
        category="Sales",
        description="Test sale"
    )

    test_session.add(record)
    test_session.commit()

    # Verify record was created
    assert record.id is not None
    assert record.transaction_type == "income"
    assert record.amount == 500.0
    assert record.category == "Sales"
    assert record.description == "Test sale"
    assert isinstance(record.date, datetime)


def test_product_default_stock(test_session):
    """Test product default stock value"""
    product = Product(
        name="Test Product",
        category="Test",
        price=10.0
        # stock not specified, should default to 0
    )

    test_session.add(product)
    test_session.commit()

    assert product.stock == 0


def test_unique_username_constraint(test_session):
    """Test that username must be unique"""
    user1 = User(
        username="testuser",
        password_hash=hash_password("password1"),
        role="admin"
    )
    test_session.add(user1)
    test_session.commit()

    # Try to create another user with same username
    user2 = User(
        username="testuser",
        password_hash=hash_password("password2"),
        role="manager"
    )
    test_session.add(user2)

    with pytest.raises(Exception):  # Should raise IntegrityError
        test_session.commit()
