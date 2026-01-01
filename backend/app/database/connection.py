import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from app.config import get_settings
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

# Connection pool
connection_pool = None

def init_db_pool():
    """Initialize database connection pool"""
    global connection_pool
    try:
        connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=settings.DB_POOL_SIZE,
            dsn=settings.DATABASE_URL
        )
        logger.info("Database connection pool initialized")
    except Exception as e:
        logger.error(f"Error initializing database pool: {e}")
        raise

def close_db_pool():
    """Close database connection pool"""
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
        logger.info("Database connection pool closed")

@contextmanager
def get_db_connection():
    """Get database connection from pool"""
    conn = None
    try:
        conn = connection_pool.getconn()
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            connection_pool.putconn(conn)

def execute_query(sql: str, params: tuple = None):
    """Execute SQL query and return results"""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, params)
            if cursor.description:  # SELECT query
                return cursor.fetchall()
            return None  # INSERT/UPDATE/DELETE