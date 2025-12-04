"""
Reports and Analytics Page
Provides various reports and visualizations for business insights
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from sqlalchemy import func, extract
from models import Product, Sale
from utils.auth import require_auth
from utils.database import get_session
from config import LOW_STOCK_THRESHOLD

# Page configuration
st.set_page_config(
    page_title="Reports & Analytics",
    page_icon="📊",
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


def get_sales_trend():
    """Get sales trend over time (daily)"""
    try:
        with get_session() as session:
            sales_by_date = session.query(
                func.date(Sale.sale_date).label('date'),
                func.count(Sale.id).label('count'),
                func.sum(Sale.total_price).label('revenue')
            ).group_by(
                func.date(Sale.sale_date)
            ).order_by('date').all()

            return [{
                'Date': str(s.date),
                'Sales Count': s.count,
                'Revenue': float(s.revenue)
            } for s in sales_by_date]

    except Exception as e:
        st.error(f"Error fetching sales trend: {str(e)}")
        return []


def get_top_products(limit=10):
    """Get top selling products by revenue"""
    try:
        with get_session() as session:
            top_products = session.query(
                Product.name,
                Product.category,
                func.sum(Sale.quantity).label('total_quantity'),
                func.sum(Sale.total_price).label('total_revenue')
            ).join(Sale).group_by(
                Product.id, Product.name, Product.category
            ).order_by(
                func.sum(Sale.total_price).desc()
            ).limit(limit).all()

            return [{
                'Product': p.name,
                'Category': p.category,
                'Quantity Sold': p.total_quantity,
                'Revenue': float(p.total_revenue)
            } for p in top_products]

    except Exception as e:
        st.error(f"Error fetching top products: {str(e)}")
        return []


def get_revenue_by_category():
    """Get total revenue by product category"""
    try:
        with get_session() as session:
            category_revenue = session.query(
                Product.category,
                func.sum(Sale.total_price).label('revenue')
            ).join(Sale).group_by(Product.category).all()

            return [{
                'Category': c.category,
                'Revenue': float(c.revenue)
            } for c in category_revenue]

    except Exception as e:
        st.error(f"Error fetching category revenue: {str(e)}")
        return []


def get_monthly_revenue():
    """Get revenue breakdown by month"""
    try:
        with get_session() as session:
            monthly_revenue = session.query(
                extract('year', Sale.sale_date).label('year'),
                extract('month', Sale.sale_date).label('month'),
                func.count(Sale.id).label('sales_count'),
                func.sum(Sale.total_price).label('revenue')
            ).group_by(
                extract('year', Sale.sale_date),
                extract('month', Sale.sale_date)
            ).order_by('year', 'month').all()

            return [{
                'Year': int(m.year),
                'Month': int(m.month),
                'Month-Year': f"{int(m.year)}-{int(m.month):02d}",
                'Sales Count': m.sales_count,
                'Revenue': float(m.revenue)
            } for m in monthly_revenue]

    except Exception as e:
        st.error(f"Error fetching monthly revenue: {str(e)}")
        return []


def get_low_stock_products():
    """Get products with low stock"""
    try:
        with get_session() as session:
            products = session.query(Product).filter(
                Product.stock < LOW_STOCK_THRESHOLD
            ).order_by(Product.stock).all()

            return [{
                'ID': p.id,
                'Product': p.name,
                'Category': p.category,
                'Current Stock': p.stock,
                'Price': f"${p.price:.2f}"
            } for p in products]

    except Exception as e:
        st.error(f"Error fetching low stock products: {str(e)}")
        return []


# Main page
st.title("📊 Reports & Analytics")
st.write("Comprehensive business insights and analytics")

st.divider()

# Sales Trend Chart
st.subheader("📈 Sales Trend Over Time")

with st.spinner("Loading sales trend data..."):
    sales_trend = get_sales_trend()

if sales_trend:
    df_trend = pd.DataFrame(sales_trend)

    # Create dual-axis chart
    fig = go.Figure()

    # Add sales count trace
    fig.add_trace(go.Scatter(
        x=df_trend['Date'],
        y=df_trend['Sales Count'],
        name='Sales Count',
        mode='lines+markers',
        line=dict(color='#3498db', width=2),
        yaxis='y'
    ))

    # Add revenue trace
    fig.add_trace(go.Scatter(
        x=df_trend['Date'],
        y=df_trend['Revenue'],
        name='Revenue ($)',
        mode='lines+markers',
        line=dict(color='#2ecc71', width=2),
        yaxis='y2'
    ))

    fig.update_layout(
        title='Daily Sales Count and Revenue',
        xaxis=dict(title='Date'),
        yaxis=dict(title='Sales Count', side='left'),
        yaxis2=dict(title='Revenue ($)', overlaying='y', side='right'),
        hovermode='x unified',
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No sales data available for trend analysis")

st.divider()

# Top Products
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏆 Top 10 Products by Revenue")

    with st.spinner("Loading top products..."):
        top_products = get_top_products(limit=10)

    if top_products:
        df_top = pd.DataFrame(top_products)

        # Bar chart
        fig = px.bar(
            df_top,
            x='Product',
            y='Revenue',
            color='Revenue',
            title='Top 10 Best Selling Products',
            labels={'Revenue': 'Revenue ($)'},
            color_continuous_scale='Greens'
        )

        fig.update_layout(
            xaxis_title="Product",
            yaxis_title="Revenue ($)",
            showlegend=False,
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No product data available")

with col2:
    st.subheader("🥧 Revenue by Category")

    with st.spinner("Loading category revenue..."):
        category_revenue = get_revenue_by_category()

    if category_revenue:
        df_category = pd.DataFrame(category_revenue)

        # Pie chart
        fig = px.pie(
            df_category,
            values='Revenue',
            names='Category',
            title='Revenue Distribution by Category',
            hole=0.4
        )

        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No category data available")

st.divider()

# Monthly Revenue Table
st.subheader("📅 Monthly Revenue Summary")

with st.spinner("Loading monthly revenue..."):
    monthly_revenue = get_monthly_revenue()

if monthly_revenue:
    df_monthly = pd.DataFrame(monthly_revenue)

    # Format revenue as currency
    df_monthly['Revenue'] = df_monthly['Revenue'].apply(lambda x: f"${x:,.2f}")

    # Select columns to display
    display_df = df_monthly[['Month-Year', 'Sales Count', 'Revenue']]
    display_df.columns = ['Month', 'Total Sales', 'Total Revenue']

    st.dataframe(display_df, use_container_width=True, hide_index=True, height=300)

    # Calculate totals
    total_sales = df_monthly['Sales Count'].sum()
    # Parse revenue back to float for total
    total_revenue = sum(float(r.replace('$', '').replace(',', '')) for r in df_monthly['Revenue'])

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Sales (All Time)", f"{total_sales:,}")
    with col2:
        st.metric("Total Revenue (All Time)", f"${total_revenue:,.2f}")

else:
    st.info("No monthly revenue data available")

st.divider()

# Low Stock Products Alert
st.subheader("⚠️ Low Stock Products")

with st.spinner("Loading low stock products..."):
    low_stock = get_low_stock_products()

if low_stock:
    st.warning(f"Found {len(low_stock)} product(s) with stock below {LOW_STOCK_THRESHOLD} units")

    df_low = pd.DataFrame(low_stock)
    st.dataframe(df_low, use_container_width=True, hide_index=True)

    st.info("💡 **Recommendation:** Restock these products to avoid inventory shortages")
else:
    st.success("✅ All products have adequate stock levels")

st.divider()

# Export data section (placeholder)
st.subheader("📥 Export Reports")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Export Sales Report", use_container_width=True):
        if sales_trend:
            df = pd.DataFrame(sales_trend)
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"sales_report_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

with col2:
    if st.button("Export Top Products", use_container_width=True):
        if top_products:
            df = pd.DataFrame(top_products)
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"top_products_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

with col3:
    if st.button("Export Low Stock", use_container_width=True):
        if low_stock:
            df = pd.DataFrame(low_stock)
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"low_stock_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
