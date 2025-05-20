import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extensions import db
from app import app
from sqlalchemy import text

def check_tables():
    """
    Check the owner_helper_associations and helper_verification_logs tables
    """
    with app.app_context():
        conn = db.engine.connect()
        
        try:
            # Check owner_helper_associations table
            print("\n=== Owner-Helper Associations ===")
            result = conn.execute(text("""
                SELECT a.id, a.owner_id, u.name as owner_name, a.helper_profile_id, 
                       h.name as helper_name, h.helper_id, a.is_primary_owner
                FROM owner_helper_associations a
                JOIN users u ON a.owner_id = u.id
                JOIN helper_profiles h ON a.helper_profile_id = h.id
            """))
            
            rows = result.fetchall()
            if rows:
                for row in rows:
                    print(f"ID: {row[0]}")
                    print(f"Owner: {row[2]} (ID: {row[1]})")
                    print(f"Helper: {row[4]} (ID: {row[5]})")
                    print(f"Primary Owner: {'Yes' if row[6] else 'No'}")
                    print("---")
            else:
                print("No associations found")
            
            # Check helper_profiles table structure
            print("\n=== Helper Profiles Structure ===")
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'helper_profiles'"))
            columns = [row[0] for row in result.fetchall()]
            print(f"Columns: {', '.join(columns)}")
            
            # Check if care_of column exists and is accessible
            try:
                result = conn.execute(text("""
                    SELECT id, name, helper_id, care_of
                    FROM helper_profiles
                    LIMIT 3
                """))
                print("\n=== Sample Helper Data with care_of ===")
                rows = result.fetchall()
                if rows:
                    for row in rows:
                        print(f"ID: {row[0]}")
                        print(f"Name: {row[1]}")
                        print(f"Helper ID: {row[2]}")
                        print(f"Care of: {row[3] or 'None'}")
                        print("---")
                else:
                    print("No helper profiles found")
            except Exception as e:
                print(f"Error accessing care_of column: {str(e)}")
            
        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            conn.close()

if __name__ == "__main__":
    check_tables() 