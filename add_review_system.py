import os
import sys
from flask import Flask
from config import config
from extensions import db
from models import CoreValue, ReviewTaskRating, Review

def create_app(config_name='development'):
    """Factory function to create and configure the Flask app."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    db.init_app(app)
    return app

def migrate_database():
    """Update the database schema to include new review system models."""
    app = create_app()
    
    with app.app_context():
        # Check if tables exist first
        try:
            # Create the new tables
            db.create_all()
            print("Database schema updated successfully.")
            
            # Import the core values population function
            from populate_core_competencies import populate_core_values
            populate_core_values()
            
        except Exception as e:
            print(f"Error updating database schema: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    migrate_database() 