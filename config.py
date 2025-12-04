"""
Configuration file for ERP system
Contains database connection settings and other configuration parameters
"""

import os

# Get the directory where this config file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database configuration - Using SQLite with absolute path
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'erp_system.db')}"

# Application settings
APP_TITLE = "Retail ERP System"
LOW_STOCK_THRESHOLD = 10

# Default admin credentials
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
