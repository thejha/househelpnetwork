#!/usr/bin/env python3
"""
Data migration script to transfer data from PostgreSQL to MySQL.
This script connects to both databases, reads all data from PostgreSQL tables,
and inserts it into the corresponding MySQL tables.
"""
import os
import sys
import json
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

def get_postgres_table_columns(pg_conn, table_name):
    """Get the column names for a specific table in PostgreSQL."""
    cursor = pg_conn.cursor()
    cursor.execute(f"""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    columns = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return columns

def get_mysql_table_columns(mysql_conn, table_name):
    """Get the column names for a specific table in MySQL."""
    cursor = mysql_conn.cursor()
    cursor.execute(f"""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
    """, (app_config.MYSQL_DATABASE, table_name))
    columns = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return columns

def get_column_types(conn, table_name, is_postgres=True):
    """Get column types for a table."""
    cursor = conn.cursor()
    
    if is_postgres:
        # PostgreSQL query
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
    else:
        # MySQL query
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (app_config.MYSQL_DATABASE, table_name))
    
    column_types = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.close()
    return column_types

def migrate_table_data(pg_conn, mysql_conn, table_name, batch_size=1000):
    """Migrate data from PostgreSQL to MySQL for a specific table."""
    logger.info(f"Migrating data for table: {table_name}")
    
    try:
        # Get column names from both databases
        pg_columns = get_postgres_table_columns(pg_conn, table_name)
        mysql_columns = get_mysql_table_columns(mysql_conn, table_name)
        
        if not pg_columns:
            logger.warning(f"No columns found for table {table_name} in PostgreSQL")
            return
            
        if not mysql_columns:
            logger.warning(f"No columns found for table {table_name} in MySQL")
            return
        
        # Find common columns between PostgreSQL and MySQL
        common_columns = [col for col in pg_columns if col in mysql_columns]
        
        if not common_columns:
            logger.warning(f"No common columns found for table {table_name}")
            return
        
        # Log any columns that will be skipped
        skipped_columns = [col for col in pg_columns if col not in mysql_columns]
        if skipped_columns:
            logger.warning(f"Skipping columns in {table_name} that don't exist in MySQL: {', '.join(skipped_columns)}")
        
        # Get column types to identify JSON fields
        pg_column_types = get_column_types(pg_conn, table_name, is_postgres=True)
        mysql_column_types = get_column_types(mysql_conn, table_name, is_postgres=False)
        
        # Identify JSON columns
        json_columns = [col for col in common_columns 
                        if (pg_column_types.get(col) == 'json' or 
                            pg_column_types.get(col) == 'jsonb' or 
                            mysql_column_types.get(col) == 'json')]
        
        if json_columns:
            logger.info(f"JSON columns in {table_name}: {', '.join(json_columns)}")
        
        column_names = ", ".join(common_columns)
        pg_column_select = ", ".join(common_columns)
        placeholders = ", ".join(["%s"] * len(common_columns))
        
        # Fetch data from PostgreSQL
        pg_cursor = pg_conn.cursor()
        pg_cursor.execute(f"SELECT {pg_column_select} FROM {table_name}")
        
        mysql_cursor = mysql_conn.cursor()
        
        # Clear existing data in MySQL table
        mysql_cursor.execute(f"DELETE FROM {table_name}")
        mysql_conn.commit()
        
        # Process data in batches
        batch = []
        count = 0
        total_count = 0
        
        for row in pg_cursor:
            # Handle NULL values and other data type conversions if needed
            processed_row = []
            for i, val in enumerate(row):
                col_name = common_columns[i]
                
                if val is None:
                    processed_row.append(None)
                elif col_name in json_columns:
                    # Handle JSON data
                    if isinstance(val, dict) or isinstance(val, list):
                        # Already a Python object, convert to JSON string
                        processed_row.append(json.dumps(val))
                    elif isinstance(val, str):
                        # Already a string, check if it's valid JSON
                        try:
                            # Try to parse and re-serialize to ensure valid JSON
                            json_obj = json.loads(val)
                            processed_row.append(json.dumps(json_obj))
                        except json.JSONDecodeError:
                            # Not valid JSON, store as NULL
                            logger.warning(f"Invalid JSON in {table_name}.{col_name}: {val[:100]}...")
                            processed_row.append(None)
                    else:
                        # Unknown type, convert to string
                        processed_row.append(str(val))
                else:
                    processed_row.append(val)
            
            batch.append(processed_row)
            count += 1
            
            # Insert in batches
            if count >= batch_size:
                try:
                    # Generate insert query
                    insert_query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
                    mysql_cursor.executemany(insert_query, batch)
                    mysql_conn.commit()
                    total_count += count
                    logger.info(f"Inserted {count} rows into {table_name}, total: {total_count}")
                    batch = []
                    count = 0
                except Exception as e:
                    mysql_conn.rollback()
                    logger.error(f"Error inserting batch into {table_name}: {e}")
                    if "Duplicate entry" in str(e):
                        logger.warning("Skipping duplicate entries...")
                        continue
                    raise
        
        # Insert any remaining rows
        if batch:
            try:
                insert_query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
                mysql_cursor.executemany(insert_query, batch)
                mysql_conn.commit()
                total_count += count
                logger.info(f"Inserted final {count} rows into {table_name}, total: {total_count}")
            except Exception as e:
                mysql_conn.rollback()
                logger.error(f"Error inserting final batch into {table_name}: {e}")
                raise
        
        pg_cursor.close()
        mysql_cursor.close()
        
        logger.info(f"Successfully migrated {total_count} rows for table {table_name}")
        
    except Exception as e:
        logger.error(f"Error migrating data for table {table_name}: {e}")
        raise

def disable_foreign_keys(conn):
    """Disable foreign key checks in MySQL."""
    cursor = conn.cursor()
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    conn.commit()
    cursor.close()
    logger.info("Foreign key checks disabled")

def enable_foreign_keys(conn):
    """Enable foreign key checks in MySQL."""
    cursor = conn.cursor()
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()
    cursor.close()
    logger.info("Foreign key checks enabled")

def migrate_all_data():
    """Migrate all data from PostgreSQL to MySQL."""
    logger.info("Starting data migration from PostgreSQL to MySQL")
    
    pg_conn = get_postgres_connection()
    mysql_conn = get_mysql_connection()
    
    try:
        # Disable foreign key checks for the migration
        disable_foreign_keys(mysql_conn)
        
        # Get all tables
        tables = get_table_names(pg_conn)
        logger.info(f"Found {len(tables)} tables to migrate")
        
        # Define table order (parent tables first, then child tables)
        # This is a basic example; you might need to adjust based on your schema
        prioritized_tables = [
            'users',
            'languages',
            'task_list',
            'pincode_mapping',
            'core_competencies'
        ]
        
        # Process prioritized tables first
        for table_name in prioritized_tables:
            if table_name in tables:
                migrate_table_data(pg_conn, mysql_conn, table_name)
                tables.remove(table_name)
        
        # Process remaining tables
        for table_name in tables:
            # Skip SQLAlchemy-Alembic migration tables
            if table_name.startswith('alembic_'):
                logger.info(f"Skipping migration table: {table_name}")
                continue
            
            migrate_table_data(pg_conn, mysql_conn, table_name)
        
        # Re-enable foreign key checks
        enable_foreign_keys(mysql_conn)
        
        logger.info("Data migration completed successfully")
        
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        # Make sure foreign keys are re-enabled even if an error occurs
        try:
            enable_foreign_keys(mysql_conn)
        except:
            pass
        sys.exit(1)
    finally:
        pg_conn.close()
        mysql_conn.close()

if __name__ == "__main__":
    migrate_all_data() 