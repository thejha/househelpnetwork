import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extensions import db
from app import app
from sqlalchemy import text

def check_associations():
    with app.app_context():
        try:
            conn = db.engine.connect()
            result = conn.execute(text("SELECT COUNT(*) FROM owner_helper_associations"))
            count = result.scalar()
            print(f"Found {count} owner-helper associations")
            
            # Check if any helpers exist
            result = conn.execute(text("SELECT COUNT(*) FROM helper_profiles"))
            helper_count = result.scalar()
            print(f"Found {helper_count} helper profiles")
            
            # List some sample helper profiles
            if helper_count > 0:
                result = conn.execute(text("SELECT id, name, helper_id, created_by FROM helper_profiles LIMIT 3"))
                print("\nSample helper profiles:")
                for row in result:
                    print(f"ID: {row[0]}, Name: {row[1]}, Helper ID: {row[2]}, Created by: {row[3]}")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_associations() 