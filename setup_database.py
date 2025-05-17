"""
Database setup and seed script for HouseHelpNetwork
This script will:
1. Create all database tables
2. Seed languages
3. Seed pincode mappings
"""
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from app import app, db
from models import Language, PincodeMapping, User, HelperProfile, HelperDocument
import seed_languages
import seed_pincodes
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database():
    # Get database configuration from environment variables or use defaults
    postgres_user = os.environ.get("POSTGRES_USER", "postgres")
    postgres_password = os.environ.get("POSTGRES_PASSWORD", "postgres")
    postgres_host = os.environ.get("POSTGRES_HOST", "localhost")
    postgres_port = os.environ.get("POSTGRES_PORT", "5432")
    postgres_db = os.environ.get("POSTGRES_DB", "househelpnetwork")
    
    # Connect to PostgreSQL server
    try:
        print(f"Connecting to PostgreSQL server at {postgres_host}:{postgres_port}...")
        conn = psycopg2.connect(
            user=postgres_user,
            password=postgres_password,
            host=postgres_host,
            port=postgres_port
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{postgres_db}'")
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Creating database '{postgres_db}'...")
            cursor.execute(f"CREATE DATABASE {postgres_db}")
            print(f"Database '{postgres_db}' created successfully.")
        else:
            print(f"Database '{postgres_db}' already exists.")
        
        cursor.close()
        conn.close()
        
        print("Database setup completed successfully.")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def recreate_tables():
    """Drop and recreate all database tables."""
    with app.app_context():
        logger.info("Dropping all tables...")
        db.drop_all()
        logger.info("Creating all tables...")
        db.create_all()

def setup_database():
    with app.app_context():
        # Create all tables if they don't exist
        logger.info("Creating database tables if they don't exist...")
        db.create_all()
        
        # Now seed data
        logger.info("Seeding languages...")
        seed_languages.seed_languages()
        
        logger.info("Seeding pincodes...")
        seed_pincodes.seed_pincodes()
        
        logger.info("Database setup complete!")

if __name__ == "__main__":
    print("Setting up database for HouseHelpNetwork...")
    success = create_database()
    if success:
        print("Database setup completed.")
        
        # Now that the database exists, create all tables
        try:
            print("Creating database tables...")
            from app import app, db
            with app.app_context():
                db.create_all()
                print("Tables created successfully.")
        except Exception as e:
            print(f"Error creating tables: {e}")
            sys.exit(1)
    else:
        print("Database setup failed.")
        sys.exit(1)