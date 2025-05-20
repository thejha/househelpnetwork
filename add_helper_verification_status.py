"""
Script to add verification_status column to helper_profiles table
"""
import os
import sys
import psycopg2
from config import Config

def add_verification_status_column():
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
        
        # Create a cursor
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='helper_profiles' AND column_name='verification_status';
        """)
        column_exists = cursor.fetchone()
        
        if column_exists:
            print("Column 'verification_status' already exists in the helper_profiles table.")
        else:
            # Add the new column
            cursor.execute("""
                ALTER TABLE helper_profiles
                ADD COLUMN verification_status VARCHAR(20) DEFAULT 'Unverified';
            """)
            
            # Set default value for existing records
            cursor.execute("""
                UPDATE helper_profiles
                SET verification_status = 'Unverified'
                WHERE verification_status IS NULL;
            """)
            
            conn.commit()
            print("Column 'verification_status' added successfully to helper_profiles table.")
        
        # Update gender column to allow NULL values
        cursor.execute("""
            ALTER TABLE helper_profiles 
            ALTER COLUMN gender DROP NOT NULL;
        """)
        
        # Update state column to allow NULL values
        cursor.execute("""
            ALTER TABLE helper_profiles 
            ALTER COLUMN state DROP NOT NULL;
        """)
        
        conn.commit()
        print("Gender and state columns updated to allow NULL values.")
        
        # Close connection
        cursor.close()
        conn.close()
        
        print("Database connection closed.")
        return True
        
    except (Exception, psycopg2.Error) as error:
        print(f"Error: {error}")
        return False

if __name__ == "__main__":
    add_verification_status_column() 