"""
Main Streamlit application for ERP system
Handles authentication and displays main dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import func
from models import Product, Sale, User, FinancialRecord
from utils.auth import login, logout, is_authenticated
from utils.database import get_session
from config import APP_TITLE

# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)


def show_login_form():
    """Display login form"""
    st.title(f"🏪 {APP_TITLE}")
    st.subheader("Please log in to continue")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submit = st.form_submit_button("Login", use_container_width=True)

            if submit:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    with st.spinner("Authenticating..."):
                        success = login(username, password)
                        if success:
                            st.success(f"Welcome, {username}!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password")

        st.info("**Default credentials:**\n\nUsername: `admin`\n\nPassword: `admin123`")


def show_sidebar():
    """Display sidebar with user info and navigation"""
    with st.sidebar:
        st.title("🏪 ERP System")
        st.divider()

        # User info
        st.subheader("User Information")
        st.write(f"**Username:** {st.session_state.username}")
        st.write(f"**Role:** {st.session_state.role.title()}")

        st.divider()

        # Logout button
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()

        st.divider()
        st.caption("Navigate using the sidebar pages")


def get_dashboard_data():
    """Fetch data for dashboard KPIs"""
    try:
        with get_session() as session:
            # Total products
            total_products = session.query(func.count(Product.id)).scalar()

            # Total sales count
            total_sales = session.query(func.count(Sale.id)).scalar()

            # Total revenue
            total_revenue = session.query(func.sum(Sale.total_price)).scalar() or 0

            # Low stock products count
            low_stock_count = session.query(func.count(Product.id)).filter(
                Product.stock < 10
            ).scalar()

            # Sales by category
            sales_by_category = session.query(
                Product.category,
                func.sum(Sale.total_price).label('revenue')
            ).join(Sale).group_by(Product.category).all()

            return {
                'total_products': total_products,
                'total_sales': total_sales,
                'total_revenue': total_revenue,
                'low_stock_count': low_stock_count,
                'sales_by_category': sales_by_category
            }
    except Exception as e:
        st.error(f"Error fetching dashboard data: {str(e)}")
        return None


def show_dashboard():
    """Display main dashboard with KPIs and charts"""
    st.title("📊 Dashboard")
    st.write("Welcome to the Retail ERP System")

    # Fetch dashboard data
    with st.spinner("Loading dashboard data..."):
        data = get_dashboard_data()

    if not data:
        st.error("Failed to load dashboard data. Please check database connection.")
        return

    # KPI Cards
    st.subheader("Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Products",
            value=data['total_products'],
            delta=None
        )

    with col2:
        st.metric(
            label="Total Sales",
            value=data['total_sales'],
            delta=None
        )

    with col3:
        st.metric(
            label="Total Revenue",
            value=f"${data['total_revenue']:,.2f}",
            delta=None
        )

    with col4:
        st.metric(
            label="Low Stock Items",
            value=data['low_stock_count'],
            delta=None,
            delta_color="inverse"
        )

    st.divider()

    # Sales by Category Chart
    st.subheader("Revenue by Category")

    if data['sales_by_category']:
        # Prepare data for chart
        categories = [item[0] for item in data['sales_by_category']]
        revenues = [float(item[1]) for item in data['sales_by_category']]

        df = pd.DataFrame({
            'Category': categories,
            'Revenue': revenues
        })

        # Create bar chart
        fig = px.bar(
            df,
            x='Category',
            y='Revenue',
            title='Sales Revenue by Product Category',
            labels={'Revenue': 'Revenue ($)', 'Category': 'Product Category'},
            color='Revenue',
            color_continuous_scale='Blues'
        )

        fig.update_layout(
            xaxis_title="Product Category",
            yaxis_title="Revenue ($)",
            showlegend=False,
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No sales data available yet")

    st.divider()

    # Navigation guide
    st.subheader("Navigate")
    st.info("📌 Use the sidebar to navigate between different modules:")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("**📦 Inventory**")
        st.caption("Manage products and stock")

    with col2:
        st.markdown("**💰 Sales**")
        st.caption("Record and view sales")

    with col3:
        st.markdown("**📈 Finance**")
        st.caption("Track income & expenses")

    with col4:
        st.markdown("**📊 Reports**")
        st.caption("View analytics & insights")


def main():
    """Main application logic"""
    # Check authentication
    if not is_authenticated():
        show_login_form()
    else:
        show_sidebar()
        show_dashboard()


if __name__ == "__main__":
    main()
