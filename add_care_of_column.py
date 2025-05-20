"""
Database migration script to add care_of column to helper_profiles table
"""
from app import app
from extensions import db
from sqlalchemy import text

def add_care_of_column():
    """Add the care_of column to the helper_profiles table"""
    with app.app_context():
        print("Starting migration: Adding care_of column to helper_profiles table")
        
        # Use SQLAlchemy text function for raw SQL
        query = text("ALTER TABLE helper_profiles ADD COLUMN care_of VARCHAR(100);")
        
        try:
            db.session.execute(query)
            db.session.commit()
            print("Migration successful: care_of column added to helper_profiles table")
        except Exception as e:
            db.session.rollback()
            print(f"Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    add_care_of_column() 