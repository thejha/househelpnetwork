import os
import sys
from flask import Flask
from config import config
from extensions import db
from models import CoreValue

def create_app(config_name='development'):
    """Factory function to create and configure the Flask app."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    db.init_app(app)
    return app

def populate_core_values():
    """Populate the core values table with predefined values."""
    app = create_app()
    
    with app.app_context():
        # Check if we already have core values
        existing_count = CoreValue.query.count()
        if existing_count > 0:
            print(f"Found {existing_count} existing core values. Skipping population.")
            sys.exit(0)
        
        # Define the core values with descriptions
        core_values = [
            {
                'name': 'Punctuality',
                'description': 'Arrives on time and follows the agreed schedule consistently'
            },
            {
                'name': 'Attitude',
                'description': 'Demonstrates a positive, respectful, and cooperative attitude'
            },
            {
                'name': 'Hygiene',
                'description': 'Maintains proper personal hygiene and cleanliness standards'
            },
            {
                'name': 'Reliability',
                'description': 'Can be depended upon to fulfill duties and obligations consistently'
            },
            {
                'name': 'Communication',
                'description': 'Effectively communicates and responds appropriately to requests and instructions'
            }
        ]
        
        # Add core values to the database
        for value in core_values:
            core_value = CoreValue(name=value['name'], description=value['description'])
            db.session.add(core_value)
        
        # Commit the changes
        db.session.commit()
        print(f"Successfully added {len(core_values)} core values.")

if __name__ == '__main__':
    populate_core_values() 