"""
Database connection and utilities.
"""

import os
import psycopg2
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_connection(max_retries=5, retry_delay=2):
    """
    Get a database connection with retry logic.

    Args:
        max_retries: Maximum number of connection attempts
        retry_delay: Delay between retries in seconds

    Returns:
        Database connection object

    Raises:
        Exception if connection fails after all retries
    """
    db_config = {
        'host': os.environ.get('DB_HOST', 'postgres'),
        'port': os.environ.get('DB_PORT', '5432'),
        'database': os.environ.get('DB_NAME', 'rss_monitor'),
        'user': os.environ.get('DB_USER', 'rss_user'),
        'password': os.environ.get('DB_PASSWORD', 'rss_password'),
    }

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to connect to database (attempt {attempt + 1}/{max_retries})")
            conn = psycopg2.connect(**db_config)
            logger.info("Successfully connected to database")
            return conn
        except psycopg2.OperationalError as e:
            logger.warning(f"Database connection failed: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("All connection attempts failed")
                raise

    raise Exception("Failed to connect to database")


def close_db_connection(conn):
    """
    Close a database connection.

    Args:
        conn: Database connection object
    """
    if conn:
        conn.close()
        logger.info("Database connection closed")
