# Retail ERP System

A comprehensive Enterprise Resource Planning (ERP) system built for retail and warehouse businesses. This system provides inventory management, sales tracking, financial management, and business analytics.

## Features

- **Inventory Management**: Track products, manage stock levels, and receive low-stock alerts
- **Sales Management**: Record sales transactions, view sales history, and track customer purchases
- **Financial Management**: Monitor income and expenses, track profitability
- **Reports & Analytics**: Comprehensive business insights with interactive charts and visualizations
- **User Authentication**: Role-based access control (Admin, Manager, Cashier)
- **Responsive UI**: Built with Streamlit for a modern, user-friendly interface

## Technology Stack

- **Backend**: Python 3.10+
- **Database**: SQLite 3
- **ORM**: SQLAlchemy
- **Frontend**: Streamlit
- **Visualizations**: Plotly
- **Data Generation**: Faker
- **Testing**: pytest

## Project Structure

```
erp-system/
├── erp_system.db              # SQLite database file (created on first run)
├── requirements.txt           # Python dependencies
├── config.py                  # Application configuration
├── models.py                  # SQLAlchemy database models
├── seed_data.py              # Data seeding script
├── app.py                    # Main Streamlit application
├── pages/                     # Streamlit pages
│   ├── 1_Inventory.py         # Inventory management
│   ├── 2_Sales.py             # Sales management
│   ├── 3_Finance.py           # Financial management
│   └── 4_Reports.py           # Reports and analytics
├── utils/                     # Utility modules
│   ├── database.py            # Database helpers
│   └── auth.py                # Authentication utilities
├── tests/                     # Test suite
│   ├── test_models.py         # Model tests
│   └── test_operations.py     # Integration tests
└── README.md                  # This file
```

## Database Schema

### Products Table
- `id`: Primary key
- `name`: Product name
- `category`: Product category
- `price`: Unit price
- `stock`: Current stock level
- `created_at`: Creation timestamp

### Sales Table
- `id`: Primary key
- `product_id`: Foreign key to products
- `customer_name`: Customer name
- `quantity`: Quantity sold
- `total_price`: Total sale amount
- `sale_date`: Sale timestamp

### Users Table
- `id`: Primary key
- `username`: Unique username
- `password_hash`: Hashed password
- `role`: User role (admin/manager/cashier)
- `created_at`: Creation timestamp

### Financial Records Table
- `id`: Primary key
- `transaction_type`: Income or expense
- `amount`: Transaction amount
- `category`: Transaction category
- `description`: Transaction details
- `date`: Transaction timestamp

## Installation & Setup

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Seed the Database

```bash
python seed_data.py
```

This will:
- Create the SQLite database file (`erp_system.db`)
- Create all database tables
- Generate 100 sample products
- Create 500 sales transactions (last 12 months)
- Add 10 users with different roles
- Generate 100+ financial records

### Step 3: Run the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

## Default Login Credentials

**Administrator Account:**
- Username: `admin`
- Password: `admin123`

**Other Test Accounts:**
- Manager: `manager1` / `manager123`
- Cashier: `cashier1` / `cashier123`

## Role-Based Access Control

The ERP system implements role-based permissions to control what each user can do:

### 👑 Admin (Full Access)
**Permissions:**
- ✅ **Dashboard**: View all KPIs and charts
- ✅ **Inventory**: Add, edit, and delete products
- ✅ **Sales**: Record sales and view history
- ✅ **Finance**: Add expenses, view all financial records (Admin only)
- ✅ **Reports**: View all analytics and export data

### 👔 Manager (Inventory Management)
**Permissions:**
- ✅ **Dashboard**: View all KPIs and charts
- ✅ **Inventory**: Add new products (cannot edit/delete)
- ✅ **Sales**: View sales history only (cannot record sales)
- ❌ **Finance**: No access
- ✅ **Reports**: View all analytics and export data

### 💼 Cashier (Sales Operations)
**Permissions:**
- ✅ **Dashboard**: View all KPIs and charts
- ✅ **Inventory**: View products only (cannot add/edit/delete)
- ✅ **Sales**: Record sales and view history
- ❌ **Finance**: No access
- ✅ **Reports**: View sales-related analytics

  | Feature              | Admin  | Manager | Cashier |
  |----------------------|--------|---------|---------|
  | Dashboard            | ✅ Full | ✅ Full  | ✅ Full  |
  | Add Products         | ✅      | ✅       | ❌       |
  | Edit/Delete Products | ✅      | ❌       | ❌       |
  | Record Sales         | ✅      | ❌       | ✅       |
  | View Sales           | ✅      | ✅       | ✅       |
  | Finance Access       | ✅      | ❌       | ❌       |
  | Reports              | ✅      | ✅       | ✅       |

## Usage Guide

### Dashboard
- View key performance indicators (KPIs)
- See total products, sales, and revenue
- Visualize revenue by category
- Quick access to all modules

### Inventory Management
- View all products with search and filter
- Add new products
- Edit existing products
- Delete products
- Low stock alerts (< 10 units)

### Sales Management
- Record new sales transactions
- Automatic stock updates
- View sales history with date filters
- Today's and monthly sales summary

### Finance Management
- Add manual expenses
- View income and expense records
- Monthly income vs expenses comparison
- Calculate net profit

### Reports & Analytics
- Sales trend over time
- Top 10 products by revenue
- Revenue distribution by category
- Monthly revenue summary
- Low stock products report
- Export reports to CSV

## Testing

The system includes 6 focused tests covering core functionality:

**Model Tests** (`test_models.py`):
- Product creation with default values
- Product-sales relationship and data integrity
- User authentication with unique username constraints

**Operations Tests** (`test_operations.py`):
- Sales transactions update stock and create financial records
- Low stock detection queries
- Income/expense calculations and profit tracking

Run all tests:
```bash
pytest
```

Run with detailed output:
```bash
pytest -v
```

## Security Features

- Password hashing using SHA256
- SQL injection protection via SQLAlchemy ORM
- Session-based authentication
- Role-based access control
- Input validation

## Configuration

Edit `config.py` to customize:
- Database connection string
- Application title
- Low stock threshold
- Default admin credentials

## Troubleshooting

### Database Issues

If you encounter database errors:
1. Delete the existing database: `del erp_system.db` (Windows) or `rm erp_system.db` (Mac/Linux)
2. Re-run the seed script: `python seed_data.py`

### Module Not Found Errors

Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### SQLite Database Locked

If you see "database is locked" errors:
1. Close all connections to the database
2. Restart the Streamlit application

## Development

### Adding New Features

1. **Database Changes**: Update models in `models.py`
2. **Business Logic**: Add functions in appropriate page files
3. **UI Components**: Use Streamlit components in page files
4. **Tests**: Add tests in the `tests/` directory

### Database Reset

To reset the database:
```bash
# Windows
del erp_system.db
python seed_data.py

# Mac/Linux
rm erp_system.db
python seed_data.py
```

## Future Enhancements

- Purchase order management
- Supplier management
- Barcode scanning
- Email notifications
- Multi-warehouse support
- Advanced reporting with PDF export
- Mobile-responsive design
- API endpoints for integrations

## License

This project is provided as-is for educational and commercial use.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the code comments
3. Examine the test files for usage examples

---

Built with ❤️ using Python, SQLite, SQLAlchemy, and Streamlit
