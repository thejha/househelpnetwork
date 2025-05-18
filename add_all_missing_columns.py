"""
Script to add all missing columns to owner_profiles table
This script will not delete existing data.
"""
import os
import sys
import psycopg2
from config import Config

def add_missing_columns():
    # Get database configuration
    postgres_user = Config.POSTGRES_USER
    postgres_password = Config.POSTGRES_PASSWORD
    postgres_host = Config.POSTGRES_HOST
    postgres_port = Config.POSTGRES_PORT
    postgres_db = Config.POSTGRES_DB
    
    # Define missing columns and their types
    missing_columns = {
        'address_house': 'VARCHAR(100)',
        'address_landmark': 'VARCHAR(100)',
        'address_vtc': 'VARCHAR(100)',
        'address_district': 'VARCHAR(50)',
        'address_state': 'VARCHAR(50)',
        'address_pincode': 'VARCHAR(10)',
        'address_country': 'VARCHAR(50)',
        'address_post_office': 'VARCHAR(100)',
        'address_street': 'VARCHAR(100)',
        'address_subdistrict': 'VARCHAR(100)'
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
            WHERE table_name='owner_profiles'
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # Add each missing column
        for column_name, data_type in missing_columns.items():
            if column_name not in existing_columns:
                print(f"Adding column {column_name}...")
                cursor.execute(f"""
                    ALTER TABLE owner_profiles 
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
    add_missing_columns() 