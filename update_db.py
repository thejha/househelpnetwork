"""
Database update script for HouseHelpNetwork
This script will recreate all tables based on the SQLAlchemy models.
WARNING: This will delete all data in the database!
"""
from app import app, db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_tables():
    """Drop and recreate all database tables."""
    with app.app_context():
        logger.info("Dropping all tables...")
        db.drop_all()
        logger.info("Creating all tables...")
        db.create_all()
        logger.info("Tables recreated successfully, including new Aadhaar address fields.")

if __name__ == "__main__":
    print("This will DELETE ALL DATA in the database and recreate tables.")
    response = input("Are you sure you want to continue? (y/N): ")
    if response.lower() == 'y':
        recreate_tables()
        print("Database tables have been recreated successfully.")
    else:
        print("Operation cancelled.") 