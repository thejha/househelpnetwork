"""
Script to verify the database structure
This script will list all columns in the owner_profiles table
"""
import os
import sys
import psycopg2
from config import Config

def verify_db_structure():
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
        
        # Get all columns from the owner_profiles table
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name='owner_profiles'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        print("\nColumns in owner_profiles table:")
        print("--------------------------------")
        for col in columns:
            print(f"{col[0]} ({col[1]})")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    verify_db_structure() 