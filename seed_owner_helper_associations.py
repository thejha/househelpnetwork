import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extensions import db
from app import app
from sqlalchemy import text

def seed_owner_helper_associations():
    """
    Seed the owner_helper_associations table with existing relationships using raw SQL
    """
    with app.app_context():
        conn = db.engine.connect()
        
        try:
            # Get all helpers using raw SQL
            result = conn.execute(text("SELECT id, helper_id, created_by FROM helper_profiles"))
            
            for row in result:
                helper_id = row[0]  # Database ID
                helper_aadhaar_id = row[1]  # Aadhaar ID
                owner_id = row[2]  # Created by owner ID
                
                # Check if an association already exists
                check_result = conn.execute(
                    text("SELECT id FROM owner_helper_associations WHERE owner_id = :owner_id AND helper_profile_id = :helper_id"),
                    {"owner_id": owner_id, "helper_id": helper_id}
                )
                
                association_exists = check_result.fetchone() is not None
                
                if not association_exists:
                    # Create a new association with the creator as primary owner
                    conn.execute(
                        text("""
                            INSERT INTO owner_helper_associations 
                            (owner_id, helper_profile_id, is_primary_owner, added_at)
                            VALUES (:owner_id, :helper_id, TRUE, CURRENT_TIMESTAMP)
                        """),
                        {"owner_id": owner_id, "helper_id": helper_id}
                    )
                    print(f"Added association for helper {helper_aadhaar_id} with owner ID {owner_id}")
            
            conn.commit()
            print("Completed seeding owner-helper associations")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            conn.rollback()
        finally:
            conn.close()

if __name__ == "__main__":
    seed_owner_helper_associations() 