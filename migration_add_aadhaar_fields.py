"""
Migration script to add Aadhaar verification fields to owner_profiles table.
Run this script after updating the models.py file.
"""
import sys
import logging
from app import app, db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_aadhaar_fields():
    """Add Aadhaar verification fields to owner_profiles table"""
    with app.app_context():
        try:
            # Connect to database
            connection = db.engine.connect()
            
            # Check if aadhaar_id column exists
            check_column_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'owner_profiles' AND column_name = 'aadhaar_id';
            """
            result = connection.execute(check_column_sql)
            column_exists = result.fetchone() is not None
            
            if not column_exists:
                logger.info("Adding aadhaar_id column to owner_profiles table")
                connection.execute("ALTER TABLE owner_profiles ADD COLUMN aadhaar_id VARCHAR(12);")
            else:
                logger.info("aadhaar_id column already exists")
            
            # Check if aadhaar_verified column exists
            check_column_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'owner_profiles' AND column_name = 'aadhaar_verified';
            """
            result = connection.execute(check_column_sql)
            column_exists = result.fetchone() is not None
            
            if not column_exists:
                logger.info("Adding aadhaar_verified column to owner_profiles table")
                connection.execute("ALTER TABLE owner_profiles ADD COLUMN aadhaar_verified BOOLEAN DEFAULT FALSE;")
            else:
                logger.info("aadhaar_verified column already exists")
            
            # Check if aadhaar_verified_at column exists
            check_column_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'owner_profiles' AND column_name = 'aadhaar_verified_at';
            """
            result = connection.execute(check_column_sql)
            column_exists = result.fetchone() is not None
            
            if not column_exists:
                logger.info("Adding aadhaar_verified_at column to owner_profiles table")
                connection.execute("ALTER TABLE owner_profiles ADD COLUMN aadhaar_verified_at TIMESTAMP;")
            else:
                logger.info("aadhaar_verified_at column already exists")
            
            connection.close()
            logger.info("Database migration completed successfully!")
            return True
        
        except Exception as e:
            logger.error(f"Error updating database schema: {str(e)}")
            return False

if __name__ == "__main__":
    print("Running migration script to add Aadhaar verification fields...")
    success = add_aadhaar_fields()
    
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed. Check logs for details.")
        sys.exit(1) 