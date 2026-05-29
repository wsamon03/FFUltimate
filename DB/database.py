"""
Database connection and utility functions for PostgreSQL.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logger = logging.getLogger(__name__)

def get_connection():
    """Create and return a PostgreSQL database connection."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "nfl_fantasy"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            port=os.getenv("DB_PORT", "5432")
        )
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        raise


def execute_query(query, params=None, fetch=False):
    """
    Execute a SQL query with optional parameters.

    Args:
        query: SQL query string
        params: Tuple of parameters for query
        fetch: If True, return fetched results

    Returns:
        Query result if fetch=True, otherwise None
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch:
                result = cur.fetchall()
                return result if result else []
            conn.commit()
            return None
    except psycopg2.Error as e:
        logger.error(f"Query execution error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def upsert_by_unique(query, unique_check_query, insert_query, update_query, params, unique_params):
    """
    Generic upsert operation for tables.

    Args:
        query: Description of operation (for logging)
        unique_check_query: SELECT query to check if record exists
        insert_query: INSERT query for new records
        update_query: UPDATE query for existing records
        params: Parameters for INSERT/UPDATE
        unique_params: Parameters for unique check query

    Returns:
        True if inserted, False if updated
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # Check if record exists
            cur.execute(unique_check_query, unique_params)
            exists = cur.fetchone() is not None

            if exists:
                cur.execute(update_query, params)
                logger.debug(f"Updated existing record: {query}")
                conn.commit()
                return False
            else:
                cur.execute(insert_query, params)
                logger.debug(f"Inserted new record: {query}")
                conn.commit()
                return True
    except psycopg2.Error as e:
        logger.error(f"Upsert error ({query}): {e}")
        if conn:
            conn.rollback()
        raise


def get_or_create_by_unique(select_query, insert_query, select_params, insert_params):
    """
    Select existing record or create new one.

    Args:
        select_query: SELECT query to find existing record
        insert_query: INSERT query with RETURNING clause
        select_params: Parameters for SELECT
        insert_params: Parameters for INSERT

    Returns:
        ID of existing or newly created record
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Try to find existing record
            cur.execute(select_query, select_params)
            result = cur.fetchone()

            if result:
                logger.debug(f"Found existing record with id: {result['id']}")
                return result['id']

            # Insert new record
            cur.execute(insert_query, insert_params)
            conn.commit()
            new_id = cur.fetchone()['id']
            logger.debug(f"Created new record with id: {new_id}")
            return new_id
    except psycopg2.Error as e:
        logger.error(f"Get or create error: {e}")
        if conn:
            conn.rollback()
        raise
