"""
Script to add contract termination columns to the contracts table:
- termination_reason
- is_terminated
"""
import os
import sys
import psycopg2
from config import Config

def add_termination_columns():
    # Get database configuration
    postgres_user = Config.POSTGRES_USER
    postgres_password = Config.POSTGRES_PASSWORD
    postgres_host = Config.POSTGRES_HOST
    postgres_port = Config.POSTGRES_PORT
    postgres_db = Config.POSTGRES_DB
    
    # Define new columns and their types
    new_columns = {
        'termination_reason': 'TEXT',
        'is_terminated': 'BOOLEAN DEFAULT FALSE'
    }
    
    # Connect to PostgreSQL database
    try:
        print(f"Connecting to PostgreSQL database at {postgres_host}:{postgres_port}...")
        conn = psycopg2.connect(
            user=postgres_user,
            password=postgres_password,
            host=postgres_host,
            port=postgres_port,
            database=postgres_db
        )
        cursor = conn.cursor()
        
        # Get existing columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='contracts'
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # Add each new column
        for column_name, data_type in new_columns.items():
            if column_name not in existing_columns:
                print(f"Adding column {column_name}...")
                cursor.execute(f"""
                    ALTER TABLE contracts 
                    ADD COLUMN {column_name} {data_type}
                """)
                conn.commit()
                print(f"Column {column_name} added successfully.")
            else:
                print(f"Column {column_name} already exists.")
        
        cursor.close()
        conn.close()
        
        print("Database update completed successfully.")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    add_termination_columns() 