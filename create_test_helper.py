import os
import sys
import datetime

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extensions import db
from app import app
from sqlalchemy import text
from models import User, OwnerHelperAssociation

def create_test_helper():
    """
    Create a test helper profile in the database using raw SQL to avoid the care_of column
    """
    with app.app_context():
        try:
            # First, check if any users exist
            user = User.query.first()
            if not user:
                print("Error: No users found in the database. Create a user first.")
                return
            
            # Create a test helper profile using raw SQL
            conn = db.engine.connect()
            
            # Insert the helper profile without specifying the care_of column
            result = conn.execute(text("""
                INSERT INTO helper_profiles 
                (helper_id, helper_type, name, phone_number, languages, gender, 
                verification_status, created_by, created_at)
                VALUES 
                (:helper_id, :helper_type, :name, :phone_number, :languages, :gender, 
                :verification_status, :created_by, :created_at)
                RETURNING id
            """), {
                "helper_id": "123456789012",
                "helper_type": "maid",
                "name": "Test Helper",
                "phone_number": "9876543210",
                "languages": "Hindi, English",
                "gender": "F",
                "verification_status": "Unverified",
                "created_by": user.id,
                "created_at": datetime.datetime.utcnow()
            })
            
            helper_id = result.scalar()
            print(f"Created test helper with ID: {helper_id}")
            
            # Create owner-helper association
            conn.execute(text("""
                INSERT INTO owner_helper_associations 
                (owner_id, helper_profile_id, is_primary_owner, added_at)
                VALUES 
                (:owner_id, :helper_id, TRUE, :added_at)
            """), {
                "owner_id": user.id,
                "helper_id": helper_id,
                "added_at": datetime.datetime.utcnow()
            })
            
            print(f"Created owner-helper association between user {user.id} and helper {helper_id}")
            conn.commit()
            
        except Exception as e:
            db.session.rollback()
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    create_test_helper() 