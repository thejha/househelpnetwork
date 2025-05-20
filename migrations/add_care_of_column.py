import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extensions import db
from app import app
from sqlalchemy import Column, String, text, inspect

def upgrade():
    """
    Add care_of column to helper_profiles table
    """
    with app.app_context():
        conn = db.engine.connect()
        
        # Check if the column already exists
        inspector = inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('helper_profiles')]
        
        if 'care_of' not in columns:
            # Add the care_of column
            conn.execute(text("ALTER TABLE helper_profiles ADD COLUMN care_of VARCHAR(100)"))
            print("Added care_of column to helper_profiles table")
        else:
            print("care_of column already exists in helper_profiles table")
        
        conn.close()
        
if __name__ == "__main__":
    upgrade() 