"""
Database setup and seed script for HouseHelpNetwork
This script will:
1. Create all database tables
2. Seed languages
3. Seed pincode mappings
"""
import os
import sys
import mysql.connector
from app import app, db
from models import Language, PincodeMapping, User, HelperProfile, HelperDocument
import seed_languages
import seed_pincodes
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database():
    # Get database configuration from environment variables or use defaults
    mysql_user = os.environ.get("MYSQL_USER", "root")
    mysql_password = os.environ.get("MYSQL_PASSWORD", "rmivuxg")
    mysql_host = os.environ.get("MYSQL_HOST", "localhost")
    mysql_port = os.environ.get("MYSQL_PORT", "3306")
    mysql_database = os.environ.get("MYSQL_DATABASE", "househelpnetwork")
    
    # Connect to MySQL server
    try:
        print(f"Connecting to MySQL server at {mysql_host}:{mysql_port}...")
        conn = mysql.connector.connect(
            user=mysql_user,
            password=mysql_password,
            host=mysql_host,
            port=mysql_port
        )
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SHOW DATABASES LIKE '{mysql_database}'")
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Creating database '{mysql_database}'...")
            cursor.execute(f"CREATE DATABASE {mysql_database}")
            print(f"Database '{mysql_database}' created successfully.")
        else:
            print(f"Database '{mysql_database}' already exists.")
        
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
        logger.info("Tables recreated successfully, including new Aadhaar address fields.")

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