"""
Database utility functions for ERP system
Provides helper functions for database operations
"""

from models import SessionLocal
from contextlib import contextmanager


@contextmanager
def get_session():
    """
    Context manager for database sessions
    Automatically handles session cleanup

    Usage:
        with get_session() as session:
            # perform database operations
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def execute_query(query_func, *args, **kwargs):
    """
    Execute a database query with error handling

    Args:
        query_func: Function that takes a session and performs database operations
        *args, **kwargs: Arguments to pass to query_func

    Returns:
        Result of query_func or None if error occurs
    """
    try:
        with get_session() as session:
            result = query_func(session, *args, **kwargs)
            return result
    except Exception as e:
        print(f"Database error: {str(e)}")
        return None


def safe_execute(func):
    """
    Decorator for safe database operations
    Wraps function with error handling
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error in {func.__name__}: {str(e)}")
            return None
    return wrapper
