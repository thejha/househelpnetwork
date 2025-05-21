#!/usr/bin/env python3
"""
Compare table structures between PostgreSQL and MySQL databases.
"""
import os
import sys
import logging
import psycopg2
import mysql.connector
from config import config
from app import app

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get configuration based on environment or default to development
config_name = os.environ.get('FLASK_ENV', 'development')
app_config = config[config_name]

# PostgreSQL connection details (for source database)
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "rmivuxg"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"
POSTGRES_DB = "househelpnetwork"

def get_postgres_connection():
    """Connect to PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        sys.exit(1)

def get_mysql_connection():
    """Connect to MySQL database using config settings."""
    try:
        conn = mysql.connector.connect(
            user=app_config.MYSQL_USER,
            password=app_config.MYSQL_PASSWORD,
            host=app_config.MYSQL_HOST,
            port=app_config.MYSQL_PORT,
            database=app_config.MYSQL_DATABASE
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to MySQL: {e}")
        sys.exit(1)

def get_postgres_table_columns(pg_conn, table_name):
    """Get column details for a PostgreSQL table."""
    cursor = pg_conn.cursor()
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    columns = [(row[0], row[1], row[2]) for row in cursor.fetchall()]
    cursor.close()
    return columns

def get_mysql_table_columns(mysql_conn, table_name):
    """Get column details for a MySQL table."""
    cursor = mysql_conn.cursor()
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
    """, (app_config.MYSQL_DATABASE, table_name))
    columns = [(row[0], row[1], row[2]) for row in cursor.fetchall()]
    cursor.close()
    return columns

def compare_table(pg_conn, mysql_conn, table_name):
    """Compare table structure between PostgreSQL and MySQL."""
    logger.info(f"Comparing table structure for: {table_name}")
    
    pg_columns = get_postgres_table_columns(pg_conn, table_name)
    mysql_columns = get_mysql_table_columns(mysql_conn, table_name)
    
    pg_column_names = [col[0] for col in pg_columns]
    mysql_column_names = [col[0] for col in mysql_columns]
    
    # Find columns in PostgreSQL but not in MySQL
    missing_in_mysql = set(pg_column_names) - set(mysql_column_names)
    if missing_in_mysql:
        print(f"Columns in PostgreSQL but missing in MySQL for table {table_name}:")
        for col in missing_in_mysql:
            print(f"  - {col}")
    
    # Find columns in MySQL but not in PostgreSQL
    missing_in_pg = set(mysql_column_names) - set(pg_column_names)
    if missing_in_pg:
        print(f"Columns in MySQL but missing in PostgreSQL for table {table_name}:")
        for col in missing_in_pg:
            print(f"  - {col}")
    
    if not missing_in_mysql and not missing_in_pg:
        print(f"Table {table_name} has identical column names in both databases.")

def get_table_names(pg_conn):
    """Get a list of all tables in the PostgreSQL database."""
    cursor = pg_conn.cursor()
    cursor.execute("""
        SELECT tablename FROM pg_catalog.pg_tables 
        WHERE schemaname = 'public'
    """)
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables

def main():
    """Main function to compare database schemas."""
    pg_conn = get_postgres_connection()
    mysql_conn = get_mysql_connection()
    
    try:
        # Get all tables from PostgreSQL
        tables = get_table_names(pg_conn)
        
        # Check if specific table was specified
        if len(sys.argv) > 1:
            table_name = sys.argv[1]
            if table_name in tables:
                compare_table(pg_conn, mysql_conn, table_name)
            else:
                print(f"Table {table_name} not found in PostgreSQL database.")
        else:
            # Compare all tables
            print(f"Comparing {len(tables)} tables between PostgreSQL and MySQL:")
            for table_name in tables:
                # Skip SQLAlchemy-Alembic migration tables
                if table_name.startswith('alembic_'):
                    continue
                compare_table(pg_conn, mysql_conn, table_name)
    except Exception as e:
        logger.error(f"Error comparing schemas: {e}")
    finally:
        pg_conn.close()
        mysql_conn.close()

if __name__ == "__main__":
    main() 