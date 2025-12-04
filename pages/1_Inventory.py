"""
Inventory Management Page
Allows viewing, adding, editing, and deleting products
"""

import streamlit as st
import pandas as pd
from sqlalchemy import or_
from models import Product
from utils.auth import require_auth, check_role
from utils.database import get_session
from config import LOW_STOCK_THRESHOLD

# Page configuration
st.set_page_config(
    page_title="Inventory Management",
    page_icon="📦",
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


def get_all_products(search_term=None, category_filter=None):
    """Fetch all products with optional filtering"""
    try:
        with get_session() as session:
            query = session.query(Product)

            # Apply search filter
            if search_term:
                query = query.filter(
                    or_(
                        Product.name.ilike(f'%{search_term}%'),
                        Product.category.ilike(f'%{search_term}%')
                    )
                )

            # Apply category filter
            if category_filter and category_filter != "All":
                query = query.filter(Product.category == category_filter)

            products = query.order_by(Product.id.desc()).all()

            # Convert to list of dicts
            return [{
                'ID': p.id,
                'Name': p.name,
                'Category': p.category,
                'Price': f"${p.price:.2f}",
                'Stock': p.stock,
                'Created': p.created_at.strftime('%Y-%m-%d')
            } for p in products]
    except Exception as e:
        st.error(f"Error fetching products: {str(e)}")
        return []


def get_categories():
    """Get unique product categories"""
    try:
        with get_session() as session:
            categories = session.query(Product.category).distinct().all()
            return ["All"] + [cat[0] for cat in categories if cat[0]]
    except Exception as e:
        return ["All"]


def add_product(name, category, price, stock):
    """Add new product to database"""
    try:
        with get_session() as session:
            product = Product(
                name=name,
                category=category,
                price=price,
                stock=stock
            )
            session.add(product)
        return True, "Product added successfully!"
    except Exception as e:
        return False, f"Error adding product: {str(e)}"


def update_product(product_id, name, category, price, stock):
    """Update existing product"""
    try:
        with get_session() as session:
            product = session.query(Product).filter(Product.id == product_id).first()
            if product:
                product.name = name
                product.category = category
                product.price = price
                product.stock = stock
                return True, "Product updated successfully!"
            return False, "Product not found"
    except Exception as e:
        return False, f"Error updating product: {str(e)}"


def delete_product(product_id):
    """Delete product from database"""
    try:
        with get_session() as session:
            product = session.query(Product).filter(Product.id == product_id).first()
            if product:
                session.delete(product)
                return True, "Product deleted successfully!"
            return False, "Product not found"
    except Exception as e:
        return False, f"Error deleting product: {str(e)}"


def get_low_stock_products():
    """Get products with low stock"""
    try:
        with get_session() as session:
            products = session.query(Product).filter(
                Product.stock < LOW_STOCK_THRESHOLD
            ).all()
            return [{
                'ID': p.id,
                'Name': p.name,
                'Category': p.category,
                'Stock': p.stock
            } for p in products]
    except Exception as e:
        return []


# Main page
st.title("📦 Inventory Management")

# Low stock alert
low_stock = get_low_stock_products()
if low_stock:
    st.warning(f"⚠️ {len(low_stock)} product(s) have low stock (below {LOW_STOCK_THRESHOLD} units)")
    with st.expander("View Low Stock Products"):
        df_low = pd.DataFrame(low_stock)
        st.dataframe(df_low, use_container_width=True, hide_index=True)

st.divider()

# Add new product section (Admin and Manager only)
if st.session_state.role in ['admin', 'manager']:
    st.subheader("➕ Add New Product")

    with st.form("add_product_form"):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            new_name = st.text_input("Product Name*", placeholder="Enter product name")

        with col2:
            new_category = st.text_input("Category*", placeholder="e.g., Electronics")

        with col3:
            new_price = st.number_input("Price ($)*", min_value=0.01, value=10.0, step=0.01)

        with col4:
            new_stock = st.number_input("Stock*", min_value=0, value=0, step=1)

        submit_add = st.form_submit_button("Add Product", use_container_width=True)

        if submit_add:
            if not new_name or not new_category:
                st.error("Please fill in all required fields (marked with *)")
            elif new_price <= 0:
                st.error("Price must be greater than 0")
            else:
                with st.spinner("Adding product..."):
                    success, message = add_product(new_name, new_category, new_price, new_stock)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
else:
    st.info("ℹ️ Only Admins and Managers can add products to inventory.")

st.divider()

# Search and filter section
st.subheader("🔍 Search & Filter Products")

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    search_term = st.text_input("Search by name or category", placeholder="Type to search...")

with col2:
    categories = get_categories()
    category_filter = st.selectbox("Filter by category", categories)

with col3:
    st.write("")  # Spacing
    st.write("")  # Spacing
    if st.button("Clear Filters", use_container_width=True):
        st.rerun()

st.divider()

# Products table
st.subheader("📋 All Products")

with st.spinner("Loading products..."):
    products = get_all_products(search_term if search_term else None, category_filter)

if products:
    df = pd.DataFrame(products)
    st.dataframe(df, use_container_width=True, hide_index=True, height=400)

    st.caption(f"Total products: {len(products)}")

    st.divider()

    # Edit/Delete section (Admin only)
    if st.session_state.role == 'admin':
        st.subheader("✏️ Edit or Delete Product")

        col1, col2 = st.columns(2)

        with col1:
            product_ids = [p['ID'] for p in products]
            selected_id = st.selectbox("Select Product ID", product_ids)

            if selected_id:
                selected_product = next((p for p in products if p['ID'] == selected_id), None)
                if selected_product:
                    with st.form("edit_product_form"):
                        edit_name = st.text_input("Product Name", value=selected_product['Name'])
                        edit_category = st.text_input("Category", value=selected_product['Category'])
                        # Remove $ sign and convert to float
                        price_value = float(selected_product['Price'].replace('$', ''))
                        edit_price = st.number_input("Price ($)", min_value=0.01, value=price_value, step=0.01)
                        edit_stock = st.number_input("Stock", min_value=0, value=selected_product['Stock'], step=1)

                        submit_edit = st.form_submit_button("Update Product", use_container_width=True)

                        if submit_edit:
                            if not edit_name or not edit_category:
                                st.error("Name and category are required")
                            else:
                                with st.spinner("Updating product..."):
                                    success, message = update_product(
                                        selected_id, edit_name, edit_category, edit_price, edit_stock
                                    )
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)

        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            st.write("**Delete Product**")
            st.warning(f"⚠️ You are about to delete product ID: {selected_id}")

            if st.button("🗑️ Delete Product", type="secondary", use_container_width=True):
                with st.spinner("Deleting product..."):
                    success, message = delete_product(selected_id)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    else:
        st.info("ℹ️ Only Admins can edit or delete products.")

else:
    st.info("No products found. Add your first product above!")
