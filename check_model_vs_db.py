"""
Script to compare SQLAlchemy model columns with actual database columns
This script will identify any discrepancies between the two
"""
import os
import sys
import psycopg2
from sqlalchemy import inspect
from app import app, db
from models import OwnerProfile
from config import Config

def get_model_columns():
    """Get all columns from the SQLAlchemy model"""
    with app.app_context():
        inspector = inspect(OwnerProfile)
        return [column.key for column in inspector.mapper.column_attrs]

def get_db_columns():
    """Get all columns from the database"""
    # Get database configuration
    postgres_user = Config.POSTGRES_USER
    postgres_password = Config.POSTGRES_PASSWORD
    postgres_host = Config.POSTGRES_HOST
    postgres_port = Config.POSTGRES_PORT
    postgres_db = Config.POSTGRES_DB
    
    # Connect to PostgreSQL database
    try:
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
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_name='owner_profiles'
        """)
        columns = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return columns
        
    except Exception as e:
        print(f"Error: {e}")
        return []

def compare_columns():
    """Compare model columns with database columns"""
    model_columns = get_model_columns()
    db_columns = get_db_columns()
    
    print("\nColumns in SQLAlchemy model:")
    print("----------------------------")
    for col in model_columns:
        print(col)
    
    print("\nColumns in database:")
    print("--------------------")
    for col in db_columns:
        print(col)
    
    print("\nMissing columns in database:")
    print("---------------------------")
    missing = [col for col in model_columns if col not in db_columns]
    if missing:
        for col in missing:
            print(col)
    else:
        print("None - All model columns exist in the database")
    
    print("\nExtra columns in database:")
    print("-------------------------")
    extra = [col for col in db_columns if col not in model_columns]
    if extra:
        for col in extra:
            print(col)
    else:
        print("None - No extra columns in the database")

if __name__ == "__main__":
    compare_columns() 