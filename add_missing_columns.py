"""
Script to add the missing aadhaar_photo column to owner_profiles table
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
        
        # Check if the aadhaar_photo column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='owner_profiles' AND column_name='aadhaar_photo'
        """)
        column_exists = cursor.fetchone()
        
        if not column_exists:
            print("The aadhaar_photo column does not exist. Adding it now...")
            # Add the aadhaar_photo column
            cursor.execute("""
                ALTER TABLE owner_profiles 
                ADD COLUMN aadhaar_photo TEXT
            """)
            conn.commit()
            print("Column aadhaar_photo added successfully.")
        else:
            print("The aadhaar_photo column already exists.")
        
        cursor.close()
        conn.close()
        
        print("Database update completed successfully.")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    add_missing_columns() 