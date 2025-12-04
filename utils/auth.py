"""
Authentication utilities for ERP system
Provides password hashing and user authentication functions
"""

import hashlib
import streamlit as st
from models import User
from utils.database import get_session


def hash_password(password):
    """
    Hash password using SHA256

    Args:
        password: Plain text password

    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, password_hash):
    """
    Verify password against hash

    Args:
        password: Plain text password to verify
        password_hash: Stored password hash

    Returns:
        True if password matches, False otherwise
    """
    return hash_password(password) == password_hash


def login(username, password):
    """
    Authenticate user and set session state

    Args:
        username: User's username
        password: User's password

    Returns:
        True if successful, False otherwise
    """
    try:
        with get_session() as session:
            user = session.query(User).filter(User.username == username).first()

            if user and verify_password(password, user.password_hash):
                # Extract user data while session is still open
                user_id = user.id
                user_name = user.username
                user_role = user.role

                # Set session state after extracting data
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.session_state.username = user_name
                st.session_state.role = user_role
                return True
            return False
    except Exception as e:
        print(f"Login error: {str(e)}")
        return False


def logout():
    """Clear session state and log out user"""
    for key in ['logged_in', 'user_id', 'username', 'role']:
        if key in st.session_state:
            del st.session_state[key]


def is_authenticated():
    """
    Check if user is authenticated

    Returns:
        True if user is logged in, False otherwise
    """
    return st.session_state.get('logged_in', False)


def require_auth():
    """
    Require authentication for page access
    Redirects to login if not authenticated
    """
    if not is_authenticated():
        st.warning("Please log in to access this page")
        st.stop()


def check_role(required_role):
    """
    Check if user has required role

    Args:
        required_role: Role required for access (admin, manager, cashier)

    Returns:
        True if user has required role, False otherwise
    """
    if not is_authenticated():
        return False

    user_role = st.session_state.get('role', '')

    # Admin has access to everything
    if user_role == 'admin':
        return True

    return user_role == required_role
