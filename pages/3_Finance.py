"""
Finance Management Page
Tracks income and expenses, displays financial summary
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timezone
from sqlalchemy import func, extract
from models import FinancialRecord
from utils.auth import require_auth
from utils.database import get_session

# Page configuration
st.set_page_config(
    page_title="Finance Management",
    page_icon="📈",
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


def add_expense(amount, category, description):
    """Add a manual expense record"""
    try:
        with get_session() as session:
            expense = FinancialRecord(
                transaction_type='expense',
                amount=amount,
                category=category,
                description=description,
                date=datetime.now(timezone.utc)
            )
            session.add(expense)
        return True, "Expense added successfully!"
    except Exception as e:
        return False, f"Error adding expense: {str(e)}"


def get_financial_summary():
    """Calculate total income, expenses, and profit"""
    try:
        with get_session() as session:
            # Total income
            total_income = session.query(
                func.sum(FinancialRecord.amount)
            ).filter(
                FinancialRecord.transaction_type == 'income'
            ).scalar() or 0

            # Total expenses
            total_expenses = session.query(
                func.sum(FinancialRecord.amount)
            ).filter(
                FinancialRecord.transaction_type == 'expense'
            ).scalar() or 0

            # Profit
            profit = total_income - total_expenses

            return {
                'income': float(total_income),
                'expenses': float(total_expenses),
                'profit': float(profit)
            }
    except Exception as e:
        st.error(f"Error calculating financial summary: {str(e)}")
        return {'income': 0, 'expenses': 0, 'profit': 0}


def get_financial_records(record_type=None, limit=100):
    """Get financial records with optional filtering"""
    try:
        with get_session() as session:
            query = session.query(FinancialRecord)

            if record_type and record_type != "All":
                query = query.filter(FinancialRecord.transaction_type == record_type.lower())

            records = query.order_by(FinancialRecord.date.desc()).limit(limit).all()

            return [{
                'ID': r.id,
                'Type': r.transaction_type.title(),
                'Amount': f"${r.amount:.2f}",
                'Category': r.category,
                'Description': r.description[:50] + '...' if len(r.description) > 50 else r.description,
                'Date': r.date.strftime('%Y-%m-%d %H:%M')
            } for r in records]

    except Exception as e:
        st.error(f"Error fetching financial records: {str(e)}")
        return []


def get_monthly_comparison():
    """Get income vs expenses by month"""
    try:
        with get_session() as session:
            # Query for monthly income and expenses
            records = session.query(
                extract('year', FinancialRecord.date).label('year'),
                extract('month', FinancialRecord.date).label('month'),
                FinancialRecord.transaction_type,
                func.sum(FinancialRecord.amount).label('total')
            ).group_by(
                extract('year', FinancialRecord.date),
                extract('month', FinancialRecord.date),
                FinancialRecord.transaction_type
            ).order_by('year', 'month').all()

            # Organize data
            data = {}
            for year, month, trans_type, total in records:
                key = f"{int(year)}-{int(month):02d}"
                if key not in data:
                    data[key] = {'income': 0, 'expense': 0}
                data[key][trans_type] = float(total)

            return data

    except Exception as e:
        st.error(f"Error fetching monthly comparison: {str(e)}")
        return {}


# Main page
st.title("📈 Finance Management")

# Financial summary KPIs
summary = get_financial_summary()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total Income",
        f"${summary['income']:,.2f}",
        delta=None
    )

with col2:
    st.metric(
        "Total Expenses",
        f"${summary['expenses']:,.2f}",
        delta=None
    )

with col3:
    profit_color = "normal" if summary['profit'] >= 0 else "inverse"
    st.metric(
        "Net Profit",
        f"${summary['profit']:,.2f}",
        delta=None
    )

st.divider()

# Add expense section
st.subheader("➕ Add New Expense")

with st.form("add_expense_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        expense_amount = st.number_input(
            "Amount ($)*",
            min_value=0.01,
            value=100.0,
            step=0.01
        )

    with col2:
        expense_category = st.selectbox(
            "Category*",
            ["Rent", "Utilities", "Salaries", "Marketing", "Supplies", "Maintenance", "Other"]
        )

    with col3:
        st.write("")  # Spacing

    expense_description = st.text_area(
        "Description*",
        placeholder="Enter expense details...",
        height=100
    )

    submit_expense = st.form_submit_button("Add Expense", use_container_width=True)

    if submit_expense:
        if not expense_description:
            st.error("Please provide a description for the expense")
        elif expense_amount <= 0:
            st.error("Amount must be greater than 0")
        else:
            with st.spinner("Adding expense..."):
                success, message = add_expense(expense_amount, expense_category, expense_description)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

st.divider()

# Income vs Expenses Chart
st.subheader("📊 Income vs Expenses by Month")

monthly_data = get_monthly_comparison()

if monthly_data:
    # Prepare data for chart
    months = list(monthly_data.keys())
    income_values = [monthly_data[m]['income'] for m in months]
    expense_values = [monthly_data[m]['expense'] for m in months]

    chart_data = pd.DataFrame({
        'Month': months * 2,
        'Amount': income_values + expense_values,
        'Type': ['Income'] * len(months) + ['Expenses'] * len(months)
    })

    fig = px.bar(
        chart_data,
        x='Month',
        y='Amount',
        color='Type',
        barmode='group',
        title='Monthly Income vs Expenses',
        labels={'Amount': 'Amount ($)', 'Month': 'Month'},
        color_discrete_map={'Income': '#2ecc71', 'Expenses': '#e74c3c'}
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Amount ($)",
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No financial data available for chart")

st.divider()

# Financial records table
st.subheader("📋 Financial Records")

col1, col2 = st.columns([1, 3])

with col1:
    record_filter = st.selectbox(
        "Filter by Type",
        ["All", "Income", "Expense"]
    )

with st.spinner("Loading financial records..."):
    records = get_financial_records(record_type=record_filter, limit=100)

if records:
    df = pd.DataFrame(records)

    # Color code by type
    def highlight_type(row):
        if row['Type'] == 'Income':
            return ['background-color: #d4edda'] * len(row)
        elif row['Type'] == 'Expense':
            return ['background-color: #f8d7da'] * len(row)
        return [''] * len(row)

    st.dataframe(df, use_container_width=True, hide_index=True, height=400)
    st.caption(f"Showing last {len(records)} records")

    # Summary for displayed records
    income_count = sum(1 for r in records if r['Type'] == 'Income')
    expense_count = sum(1 for r in records if r['Type'] == 'Expense')

    col1, col2 = st.columns(2)
    with col1:
        st.info(f"Income records: {income_count}")
    with col2:
        st.info(f"Expense records: {expense_count}")

else:
    st.info("No financial records found")
