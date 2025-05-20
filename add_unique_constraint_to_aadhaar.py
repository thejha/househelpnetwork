"""
Script to add a unique constraint to the aadhaar_id field in the owner_profiles table
This ensures that two users cannot register with the same Aadhaar number
"""
import os
import sys
import psycopg2
from config import Config

def add_unique_to_aadhaar_id():
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
        
        # Check if column has a unique constraint
        cursor.execute("""
            SELECT 
                tc.constraint_name, 
                tc.table_name, 
                kcu.column_name
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
            WHERE 
                tc.constraint_type = 'UNIQUE' 
                AND tc.table_name = 'owner_profiles'
                AND kcu.column_name = 'aadhaar_id';
        """)
        constraint_exists = cursor.fetchone()
        
        if constraint_exists:
            print("Unique constraint for 'aadhaar_id' already exists in the owner_profiles table.")
        else:
            # Before adding a unique constraint, handle any duplicate records if any
            print("Checking for duplicate Aadhaar IDs...")
            cursor.execute("""
                SELECT aadhaar_id, COUNT(*) 
                FROM owner_profiles 
                WHERE aadhaar_id IS NOT NULL
                GROUP BY aadhaar_id 
                HAVING COUNT(*) > 1;
            """)
            
            duplicates = cursor.fetchall()
            if duplicates:
                print(f"Found {len(duplicates)} duplicate Aadhaar IDs! Please resolve these duplicates before adding a unique constraint.")
                for duplicate in duplicates:
                    print(f"Aadhaar ID: {duplicate[0]} appears {duplicate[1]} times")
                print("Operation aborted. Please resolve the duplicates before proceeding.")
                return False
            
            # Add the unique constraint
            print("No duplicates found. Adding unique constraint...")
            cursor.execute("""
                ALTER TABLE owner_profiles
                ADD CONSTRAINT owner_profiles_aadhaar_id_key UNIQUE (aadhaar_id);
            """)
            
            conn.commit()
            print("Unique constraint for 'aadhaar_id' added successfully to owner_profiles table.")
        
        # Close connection
        cursor.close()
        conn.close()
        
        print("Database connection closed.")
        return True
        
    except (Exception, psycopg2.Error) as error:
        print(f"Error: {error}")
        return False

if __name__ == "__main__":
    add_unique_to_aadhaar_id()
