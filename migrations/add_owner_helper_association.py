import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extensions import db
from app import app
from sqlalchemy import Column, String, text, inspect

def upgrade():
    """
    Add tables and columns needed for multi-owner helper relationships
    """
    with app.app_context():
        conn = db.engine.connect()
        
        # 1. First check if the owner_helper_associations table exists
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        # Check and create owner_helper_associations table
        if 'owner_helper_associations' not in existing_tables:
            print("Creating owner_helper_associations table...")
            conn.execute(text("""
                CREATE TABLE owner_helper_associations (
                    id SERIAL PRIMARY KEY,
                    owner_id INTEGER REFERENCES users(id) NOT NULL,
                    helper_profile_id INTEGER REFERENCES helper_profiles(id) NOT NULL,
                    is_primary_owner BOOLEAN DEFAULT FALSE,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(owner_id, helper_profile_id)
                )
            """))
            print("Table owner_helper_associations created successfully")
            
            # Migrate existing owner-helper relationships
            print("Migrating existing owner-helper relationships...")
            conn.execute(text("""
                INSERT INTO owner_helper_associations (owner_id, helper_profile_id, is_primary_owner)
                SELECT created_by, id, TRUE FROM helper_profiles
                ON CONFLICT DO NOTHING
            """))
            print("Existing relationships migrated successfully")
        else:
            print("Table owner_helper_associations already exists")
            
        # 2. Check and create helper_verification_logs table
        if 'helper_verification_logs' not in existing_tables:
            print("Creating helper_verification_logs table...")
            conn.execute(text("""
                CREATE TABLE helper_verification_logs (
                    id SERIAL PRIMARY KEY,
                    helper_profile_id INTEGER REFERENCES helper_profiles(id) NOT NULL,
                    verified_by INTEGER REFERENCES users(id) NOT NULL,
                    verification_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    verification_result VARCHAR(20) NOT NULL,
                    transaction_id VARCHAR(100),
                    verification_data JSONB
                )
            """))
            print("Table helper_verification_logs created successfully")
        else:
            print("Table helper_verification_logs already exists")
        
        conn.close()
        
if __name__ == "__main__":
    upgrade() 