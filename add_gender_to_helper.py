from extensions import db
from app import app
from sqlalchemy import text

def upgrade():
    # Add gender column to helper_profiles table
    with db.engine.connect() as conn:
        conn.execute(text('ALTER TABLE helper_profiles ADD COLUMN gender VARCHAR(10)'))
        conn.commit()

def downgrade():
    # Remove gender column from helper_profiles table
    with db.engine.connect() as conn:
        conn.execute(text('ALTER TABLE helper_profiles DROP COLUMN gender'))
        conn.commit()

if __name__ == '__main__':
    with app.app_context():
        upgrade()
        print("Successfully added gender column to helper_profiles table") 