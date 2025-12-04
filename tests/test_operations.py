"""
Integration tests for business operations
Tests complex operations like sales processing and stock management
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Product, Sale, FinancialRecord


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


def create_sale_transaction(session, product_id, customer_name, quantity):
    """Helper function to simulate sale transaction"""
    # Get product
    product = session.query(Product).filter(Product.id == product_id).first()

    if not product:
        return False, "Product not found"

    if product.stock < quantity:
        return False, "Insufficient stock"

    # Calculate total
    total_price = product.price * quantity

    # Create sale
    sale = Sale(
        product_id=product_id,
        customer_name=customer_name,
        quantity=quantity,
        total_price=total_price
    )
    session.add(sale)

    # Update stock
    product.stock -= quantity

    # Create financial record
    financial_record = FinancialRecord(
        transaction_type='income',
        amount=total_price,
        category=product.category,
        description=f"Sale of {quantity} x {product.name}"
    )
    session.add(financial_record)

    session.commit()
    return True, "Sale successful"


def test_sale_updates_stock(test_session):
    """Test that creating a sale reduces product stock"""
    # Create a product
    product = Product(
        name="Test Product",
        category="Electronics",
        price=50.0,
        stock=100
    )
    test_session.add(product)
    test_session.commit()

    initial_stock = product.stock

    # Create a sale
    success, message = create_sale_transaction(
        test_session,
        product.id,
        "Test Customer",
        10
    )

    # Verify stock was reduced
    assert success is True
    assert product.stock == initial_stock - 10
    assert product.stock == 90


def test_sale_creates_financial_record(test_session):
    """Test that creating a sale creates a financial record"""
    # Create a product
    product = Product(
        name="Test Product",
        category="Electronics",
        price=50.0,
        stock=100
    )
    test_session.add(product)
    test_session.commit()

    # Count financial records before
    initial_count = test_session.query(FinancialRecord).count()

    # Create a sale
    success, message = create_sale_transaction(
        test_session,
        product.id,
        "Test Customer",
        10
    )

    # Verify financial record was created
    assert success is True
    final_count = test_session.query(FinancialRecord).count()
    assert final_count == initial_count + 1

    # Verify financial record details
    financial_record = test_session.query(FinancialRecord).first()
    assert financial_record.transaction_type == 'income'
    assert financial_record.amount == 500.0  # 50.0 * 10
    assert financial_record.category == "Electronics"


def test_low_stock_query(test_session):
    """Test querying products with low stock"""
    # Create products with various stock levels
    products = [
        Product(name="Low Stock 1", category="Test", price=10.0, stock=5),
        Product(name="Low Stock 2", category="Test", price=10.0, stock=8),
        Product(name="Normal Stock", category="Test", price=10.0, stock=50),
        Product(name="High Stock", category="Test", price=10.0, stock=200),
    ]

    for p in products:
        test_session.add(p)
    test_session.commit()

    # Query for low stock products (stock < 10)
    low_stock_threshold = 10
    low_stock_products = test_session.query(Product).filter(
        Product.stock < low_stock_threshold
    ).all()

    # Verify results
    assert len(low_stock_products) == 2
    assert all(p.stock < low_stock_threshold for p in low_stock_products)


def test_insufficient_stock_prevents_sale(test_session):
    """Test that sale is prevented when stock is insufficient"""
    # Create a product with limited stock
    product = Product(
        name="Test Product",
        category="Electronics",
        price=50.0,
        stock=5
    )
    test_session.add(product)
    test_session.commit()

    # Try to create a sale with more quantity than available
    success, message = create_sale_transaction(
        test_session,
        product.id,
        "Test Customer",
        10  # More than available stock
    )

    # Verify sale was prevented
    assert success is False
    assert "Insufficient stock" in message
    assert product.stock == 5  # Stock should remain unchanged


def test_multiple_sales_reduce_stock_correctly(test_session):
    """Test that multiple sales correctly reduce stock"""
    # Create a product
    product = Product(
        name="Test Product",
        category="Electronics",
        price=50.0,
        stock=100
    )
    test_session.add(product)
    test_session.commit()

    # Create multiple sales
    create_sale_transaction(test_session, product.id, "Customer 1", 10)
    create_sale_transaction(test_session, product.id, "Customer 2", 15)
    create_sale_transaction(test_session, product.id, "Customer 3", 20)

    # Verify stock is correctly reduced
    assert product.stock == 55  # 100 - 10 - 15 - 20


def test_financial_income_and_expense(test_session):
    """Test calculating total income and expenses"""
    # Create financial records
    income1 = FinancialRecord(
        transaction_type='income',
        amount=1000.0,
        category='Sales',
        description='Test income 1'
    )

    income2 = FinancialRecord(
        transaction_type='income',
        amount=500.0,
        category='Sales',
        description='Test income 2'
    )

    expense1 = FinancialRecord(
        transaction_type='expense',
        amount=200.0,
        category='Rent',
        description='Test expense 1'
    )

    expense2 = FinancialRecord(
        transaction_type='expense',
        amount=150.0,
        category='Utilities',
        description='Test expense 2'
    )

    test_session.add_all([income1, income2, expense1, expense2])
    test_session.commit()

    # Calculate totals
    from sqlalchemy import func

    total_income = test_session.query(
        func.sum(FinancialRecord.amount)
    ).filter(
        FinancialRecord.transaction_type == 'income'
    ).scalar()

    total_expenses = test_session.query(
        func.sum(FinancialRecord.amount)
    ).filter(
        FinancialRecord.transaction_type == 'expense'
    ).scalar()

    # Verify calculations
    assert total_income == 1500.0
    assert total_expenses == 350.0
    assert (total_income - total_expenses) == 1150.0  # Profit


def test_product_category_sales_aggregation(test_session):
    """Test aggregating sales by product category"""
    # Create products in different categories
    product1 = Product(name="Product 1", category="Electronics", price=100.0, stock=100)
    product2 = Product(name="Product 2", category="Electronics", price=150.0, stock=100)
    product3 = Product(name="Product 3", category="Clothing", price=50.0, stock=100)

    test_session.add_all([product1, product2, product3])
    test_session.commit()

    # Create sales
    create_sale_transaction(test_session, product1.id, "Customer 1", 2)  # 200
    create_sale_transaction(test_session, product2.id, "Customer 2", 1)  # 150
    create_sale_transaction(test_session, product3.id, "Customer 3", 5)  # 250

    # Aggregate by category
    from sqlalchemy import func

    category_sales = test_session.query(
        Product.category,
        func.sum(Sale.total_price).label('total')
    ).join(Sale).group_by(Product.category).all()

    # Verify aggregation
    electronics_total = next((c.total for c in category_sales if c.category == "Electronics"), 0)
    clothing_total = next((c.total for c in category_sales if c.category == "Clothing"), 0)

    assert electronics_total == 350.0  # 200 + 150
    assert clothing_total == 250.0
