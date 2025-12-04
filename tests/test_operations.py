"""
Integration tests for business operations
Tests sales processing, stock management, and financial tracking
"""

import pytest
from sqlalchemy import create_engine, func
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
    """Simulate a complete sale transaction"""
    product = session.query(Product).filter(Product.id == product_id).first()

    if not product or product.stock < quantity:
        return False

    # Create sale and update stock
    total_price = product.price * quantity
    sale = Sale(product_id=product_id, customer_name=customer_name,
                quantity=quantity, total_price=total_price)
    session.add(sale)
    product.stock -= quantity

    # Create financial record
    financial_record = FinancialRecord(
        transaction_type='income', amount=total_price,
        category=product.category, description=f"Sale of {quantity} x {product.name}"
    )
    session.add(financial_record)

    session.commit()
    return True


def test_sale_updates_stock_and_creates_financial_record(test_session):
    """Test that sales correctly update stock and create financial records"""
    # Create product
    product = Product(name="Test Product", category="Electronics", price=50.0, stock=100)
    test_session.add(product)
    test_session.commit()

    initial_stock = product.stock
    initial_records = test_session.query(FinancialRecord).count()

    # Create sale
    success = create_sale_transaction(test_session, product.id, "Customer", 10)

    # Verify stock updated
    assert success is True
    assert product.stock == initial_stock - 10

    # Verify financial record created
    assert test_session.query(FinancialRecord).count() == initial_records + 1
    record = test_session.query(FinancialRecord).first()
    assert record.transaction_type == 'income'
    assert record.amount == 500.0  # 50.0 * 10


def test_low_stock_detection(test_session):
    """Test querying products with low stock"""
    # Create products with various stock levels
    products = [
        Product(name="Low 1", category="Test", price=10.0, stock=5),
        Product(name="Low 2", category="Test", price=10.0, stock=8),
        Product(name="Normal", category="Test", price=10.0, stock=50),
        Product(name="High", category="Test", price=10.0, stock=200),
    ]
    test_session.add_all(products)
    test_session.commit()

    # Query for low stock (< 10)
    low_stock = test_session.query(Product).filter(Product.stock < 10).all()

    assert len(low_stock) == 2
    assert all(p.stock < 10 for p in low_stock)


def test_financial_calculations(test_session):
    """Test income and expense calculations"""
    # Create financial records
    records = [
        FinancialRecord(transaction_type='income', amount=1000.0, category='Sales', description='Sale 1'),
        FinancialRecord(transaction_type='income', amount=500.0, category='Sales', description='Sale 2'),
        FinancialRecord(transaction_type='expense', amount=200.0, category='Rent', description='Rent'),
        FinancialRecord(transaction_type='expense', amount=150.0, category='Utilities', description='Utils'),
    ]
    test_session.add_all(records)
    test_session.commit()

    # Calculate totals
    total_income = test_session.query(func.sum(FinancialRecord.amount)).filter(
        FinancialRecord.transaction_type == 'income'
    ).scalar()

    total_expenses = test_session.query(func.sum(FinancialRecord.amount)).filter(
        FinancialRecord.transaction_type == 'expense'
    ).scalar()

    assert total_income == 1500.0
    assert total_expenses == 350.0
    assert (total_income - total_expenses) == 1150.0  # Profit
