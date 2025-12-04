"""
Seed data script for ERP system
Generates and inserts sample data for products, sales, users, and financial records
"""

import random
from datetime import datetime, timedelta
from faker import Faker
from models import Product, Sale, User, FinancialRecord, init_db, SessionLocal
from utils.auth import hash_password

fake = Faker('en_US')  # Use English locale to avoid special characters

# Categories for products
CATEGORIES = ['Electronics', 'Clothing', 'Food', 'Tools', 'Books', 'Sports']

# Expense categories
EXPENSE_CATEGORIES = ['Rent', 'Utilities', 'Salaries', 'Marketing', 'Supplies', 'Maintenance']


def create_products(session, count=100):
    """Generate and insert random products"""
    print(f"Creating {count} products...")
    products = []

    for i in range(count):
        product = Product(
            name=fake.catch_phrase(),
            category=random.choice(CATEGORIES),
            price=round(random.uniform(5.0, 1000.0), 2),
            stock=random.randint(0, 500)
        )
        products.append(product)
        session.add(product)

        if (i + 1) % 20 == 0:
            print(f"  Created {i + 1}/{count} products")

    session.commit()
    print(f"[OK] Successfully created {count} products\n")
    return products


def create_users(session):
    """Create default users with different roles"""
    print("Creating users...")
    users_data = [
        ('admin', 'admin123', 'admin'),
        ('manager1', 'manager123', 'manager'),
        ('manager2', 'manager123', 'manager'),
        ('cashier1', 'cashier123', 'cashier'),
        ('cashier2', 'cashier123', 'cashier'),
        ('cashier3', 'cashier123', 'cashier'),
        ('john_doe', 'password123', 'manager'),
        ('jane_smith', 'password123', 'cashier'),
        ('bob_wilson', 'password123', 'cashier'),
        ('alice_johnson', 'password123', 'manager'),
    ]

    users = []
    for username, password, role in users_data:
        user = User(
            username=username,
            password_hash=hash_password(password),
            role=role
        )
        users.append(user)
        session.add(user)
        print(f"  Created user: {username} (role: {role})")

    session.commit()
    print(f"[OK] Successfully created {len(users)} users\n")
    return users


def create_sales(session, products, count=500):
    """Generate random sales transactions for the last 12 months"""
    print(f"Creating {count} sales transactions...")
    sales = []
    financial_records = []

    # Date range: last 12 months
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=365)

    for i in range(count):
        # Select random product
        product = random.choice(products)

        # Random quantity (1-10)
        quantity = random.randint(1, 10)

        # Check if we have enough stock (for realistic data)
        if product.stock < quantity:
            # Restock the product
            product.stock += random.randint(50, 200)

        # Calculate total price
        total_price = round(product.price * quantity, 2)

        # Random date within last 12 months
        random_date = start_date + timedelta(
            seconds=random.randint(0, int((end_date - start_date).total_seconds()))
        )

        # Create sale
        sale = Sale(
            product_id=product.id,
            customer_name=fake.name(),
            quantity=quantity,
            total_price=total_price,
            sale_date=random_date
        )
        sales.append(sale)
        session.add(sale)

        # Update product stock
        product.stock -= quantity

        # Create corresponding financial record (income)
        financial_record = FinancialRecord(
            transaction_type='income',
            amount=total_price,
            category=product.category,
            description=f"Sale of {quantity} x {product.name}",
            date=random_date
        )
        financial_records.append(financial_record)
        session.add(financial_record)

        if (i + 1) % 100 == 0:
            print(f"  Created {i + 1}/{count} sales")
            session.commit()  # Commit periodically

    session.commit()
    print(f"[OK] Successfully created {count} sales transactions\n")
    return sales, financial_records


def create_expenses(session, count=50):
    """Generate random expense records"""
    print(f"Creating {count} expense records...")
    expenses = []

    # Date range: last 12 months
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=365)

    for i in range(count):
        random_date = start_date + timedelta(
            seconds=random.randint(0, int((end_date - start_date).total_seconds()))
        )

        expense = FinancialRecord(
            transaction_type='expense',
            amount=round(random.uniform(100.0, 5000.0), 2),
            category=random.choice(EXPENSE_CATEGORIES),
            description=fake.sentence(),
            date=random_date
        )
        expenses.append(expense)
        session.add(expense)

        if (i + 1) % 10 == 0:
            print(f"  Created {i + 1}/{count} expenses")

    session.commit()
    print(f"[OK] Successfully created {count} expense records\n")
    return expenses


def main():
    """Main function to seed all data"""
    print("=" * 60)
    print("ERP SYSTEM - DATABASE SEEDING")
    print("=" * 60)
    print()

    # Initialize database
    print("Initializing database...")
    init_db()
    print()

    # Create session
    session = SessionLocal()

    try:
        # Create users
        users = create_users(session)

        # Create products
        products = create_products(session, count=100)

        # Create sales (this also creates income financial records)
        sales, income_records = create_sales(session, products, count=500)

        # Create expenses
        expenses = create_expenses(session, count=50)

        # Summary
        print("=" * 60)
        print("SEEDING SUMMARY")
        print("=" * 60)
        print(f"Users created:              {len(users)}")
        print(f"Products created:           {len(products)}")
        print(f"Sales created:              {len(sales)}")
        print(f"Financial records (income): {len(income_records)}")
        print(f"Financial records (expense): {len(expenses)}")
        print(f"Total financial records:    {len(income_records) + len(expenses)}")
        print("=" * 60)
        print()
        print("[OK] Database seeding completed successfully!")
        print()
        print("Login credentials:")
        print("  Username: admin")
        print("  Password: admin123")

    except Exception as e:
        print(f"Error during seeding: {str(e)}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    main()
