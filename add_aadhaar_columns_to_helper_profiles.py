from extensions import db
from app import app
from sqlalchemy import text, inspect

def upgrade():
    """Add missing Aadhaar-related columns to helper_profiles table."""
    with app.app_context():
        inspector = inspect(db.engine)
        existing_columns = [column['name'] for column in inspector.get_columns('helper_profiles')]
        
        print(f"Existing columns: {existing_columns}")
        
        # Define Aadhaar-related columns to add
        columns_to_add = {
            'aadhaar_verified': 'BOOLEAN DEFAULT FALSE',
            'aadhaar_verified_at': 'TIMESTAMP',
            'aadhaar_dob': 'VARCHAR(20)',
            'aadhaar_address': 'TEXT',
            'aadhaar_photo': 'TEXT',
            'address_house': 'VARCHAR(100)',
            'address_landmark': 'VARCHAR(100)',
            'address_vtc': 'VARCHAR(100)',
            'address_district': 'VARCHAR(100)',
            'address_state': 'VARCHAR(100)',
            'address_pincode': 'VARCHAR(10)',
            'address_country': 'VARCHAR(100)',
            'address_post_office': 'VARCHAR(100)',
            'address_street': 'VARCHAR(100)',
            'address_subdistrict': 'VARCHAR(100)'
        }
        
        for column_name, column_type in columns_to_add.items():
            if column_name not in existing_columns:
                with db.engine.begin() as conn:
                    try:
                        conn.execute(text(f"ALTER TABLE helper_profiles ADD COLUMN {column_name} {column_type}"))
                        print(f"Added {column_name} column to helper_profiles")
                    except Exception as e:
                        print(f"Error adding {column_name} column: {str(e)}")
            else:
                print(f"{column_name} column already exists")

if __name__ == "__main__":
    upgrade()
    print("Migration completed successfully!") 