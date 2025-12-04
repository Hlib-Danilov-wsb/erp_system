"""
Sales Management Page
Allows recording new sales and viewing sales history
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from models import Product, Sale, FinancialRecord
from utils.auth import require_auth
from utils.database import get_session

# Page configuration
st.set_page_config(
    page_title="Sales Management",
    page_icon="💰",
    layout="wide"
)

# Require authentication
require_auth()

# Sidebar
with st.sidebar:
    st.title("🏪 ERP System")
    st.divider()
    st.subheader("User Information")
    st.write(f"**Username:** {st.session_state.username}")
    st.write(f"**Role:** {st.session_state.role.title()}")


def get_available_products():
    """Get all products with stock > 0"""
    try:
        with get_session() as session:
            products = session.query(Product).filter(Product.stock > 0).all()
            # Extract data while session is still open
            product_dict = {}
            for p in products:
                key = f"{p.id} - {p.name} (Stock: {p.stock})"
                product_dict[key] = {
                    'id': p.id,
                    'name': p.name,
                    'price': p.price,
                    'stock': p.stock
                }
            return product_dict
    except Exception as e:
        st.error(f"Error fetching products: {str(e)}")
        return {}


def create_sale(product_id, customer_name, quantity):
    """
    Create a new sale transaction
    Updates product stock and creates financial record
    """
    try:
        with get_session() as session:
            # Get product
            product = session.query(Product).filter(Product.id == product_id).first()

            if not product:
                return False, "Product not found"

            # Check stock availability
            if product.stock < quantity:
                return False, f"Insufficient stock. Available: {product.stock}"

            # Calculate total price
            total_price = product.price * quantity

            # Create sale record
            sale = Sale(
                product_id=product_id,
                customer_name=customer_name,
                quantity=quantity,
                total_price=total_price,
                sale_date=datetime.utcnow()
            )
            session.add(sale)

            # Update product stock
            product.stock -= quantity

            # Create financial record (income)
            financial_record = FinancialRecord(
                transaction_type='income',
                amount=total_price,
                category=product.category,
                description=f"Sale of {quantity} x {product.name} to {customer_name}",
                date=datetime.utcnow()
            )
            session.add(financial_record)

            return True, f"Sale recorded successfully! Total: ${total_price:.2f}"

    except Exception as e:
        return False, f"Error creating sale: {str(e)}"


def get_recent_sales(days=30, start_date=None, end_date=None):
    """Get recent sales with optional date filtering"""
    try:
        with get_session() as session:
            query = session.query(Sale, Product.name).join(Product)

            # Apply date filters
            if start_date and end_date:
                query = query.filter(Sale.sale_date.between(start_date, end_date))
            else:
                # Default: last N days
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                query = query.filter(Sale.sale_date >= cutoff_date)

            sales = query.order_by(Sale.sale_date.desc()).all()

            return [{
                'Sale ID': s.Sale.id,
                'Product': s.name,
                'Customer': s.Sale.customer_name,
                'Quantity': s.Sale.quantity,
                'Total Price': f"${s.Sale.total_price:.2f}",
                'Date': s.Sale.sale_date.strftime('%Y-%m-%d %H:%M')
            } for s in sales]

    except Exception as e:
        st.error(f"Error fetching sales: {str(e)}")
        return []


def get_sales_summary():
    """Get sales summary statistics"""
    try:
        with get_session() as session:
            # Today's sales
            today = datetime.utcnow().date()
            today_start = datetime.combine(today, datetime.min.time())

            today_sales = session.query(Sale).filter(
                Sale.sale_date >= today_start
            ).all()

            today_count = len(today_sales)
            today_revenue = sum(s.total_price for s in today_sales)

            # This month's sales
            month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_sales = session.query(Sale).filter(
                Sale.sale_date >= month_start
            ).all()

            month_count = len(month_sales)
            month_revenue = sum(s.total_price for s in month_sales)

            return {
                'today_count': today_count,
                'today_revenue': today_revenue,
                'month_count': month_count,
                'month_revenue': month_revenue
            }

    except Exception as e:
        return {
            'today_count': 0,
            'today_revenue': 0,
            'month_count': 0,
            'month_revenue': 0
        }


# Main page
st.title("💰 Sales Management")

# Sales summary KPIs
summary = get_sales_summary()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Today's Sales", summary['today_count'])

with col2:
    st.metric("Today's Revenue", f"${summary['today_revenue']:.2f}")

with col3:
    st.metric("This Month's Sales", summary['month_count'])

with col4:
    st.metric("This Month's Revenue", f"${summary['month_revenue']:.2f}")

st.divider()

# Create new sale section
st.subheader("🛒 Record New Sale")

products_dict = get_available_products()

if not products_dict:
    st.warning("No products available for sale. Please add products to inventory first.")
else:
    with st.form("new_sale_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            selected_product = st.selectbox(
                "Select Product*",
                options=list(products_dict.keys()),
                help="Products with available stock"
            )

        with col2:
            customer_name = st.text_input(
                "Customer Name*",
                placeholder="Enter customer name"
            )

        with col3:
            if selected_product:
                product = products_dict[selected_product]
                max_quantity = product['stock']
                quantity = st.number_input(
                    f"Quantity* (Max: {max_quantity})",
                    min_value=1,
                    max_value=max_quantity,
                    value=1,
                    step=1
                )
            else:
                quantity = st.number_input("Quantity*", min_value=1, value=1, step=1)

        # Show price preview
        if selected_product:
            product = products_dict[selected_product]
            total_preview = product['price'] * quantity
            st.info(f"💵 Total Price: ${total_preview:.2f} (${product['price']:.2f} x {quantity})")

        submit_sale = st.form_submit_button("Record Sale", use_container_width=True)

        if submit_sale:
            if not customer_name:
                st.error("Please enter customer name")
            elif not selected_product:
                st.error("Please select a product")
            else:
                product = products_dict[selected_product]
                with st.spinner("Recording sale..."):
                    success, message = create_sale(product['id'], customer_name, quantity)
                    if success:
                        st.success(message)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(message)

st.divider()

# Sales history section
st.subheader("📋 Sales History")

# Date filter
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    filter_option = st.selectbox(
        "Time Period",
        ["Last 7 days", "Last 30 days", "Last 90 days", "Custom Range"]
    )

start_date = None
end_date = None

if filter_option == "Custom Range":
    with col2:
        start_date = st.date_input("Start Date", value=datetime.utcnow() - timedelta(days=30))
        start_date = datetime.combine(start_date, datetime.min.time())

    with col3:
        end_date = st.date_input("End Date", value=datetime.utcnow())
        end_date = datetime.combine(end_date, datetime.max.time())

# Fetch sales based on filter
if filter_option == "Last 7 days":
    days = 7
elif filter_option == "Last 30 days":
    days = 30
elif filter_option == "Last 90 days":
    days = 90
else:
    days = None

with st.spinner("Loading sales history..."):
    if days:
        sales = get_recent_sales(days=days)
    else:
        sales = get_recent_sales(start_date=start_date, end_date=end_date)

if sales:
    df = pd.DataFrame(sales)
    st.dataframe(df, use_container_width=True, hide_index=True, height=400)
    st.caption(f"Total sales records: {len(sales)}")

    # Calculate total revenue for displayed sales
    total_revenue = sum(float(s['Total Price'].replace('$', '')) for s in sales)
    st.info(f"📊 Total Revenue for selected period: ${total_revenue:,.2f}")

else:
    st.info("No sales found for the selected period")
