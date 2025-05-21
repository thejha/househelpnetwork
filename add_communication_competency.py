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

def add_communication_value():
    """Add Communication as a core value if it doesn't already exist."""
    app = create_app()
    
    with app.app_context():
        # Check if Communication already exists
        communication = CoreValue.query.filter_by(name='Communication').first()
        
        if communication:
            print("Communication core value already exists.")
            return
        
        # Add Communication core value
        new_value = CoreValue(
            name='Communication',
            description='Effectively communicates and responds appropriately to requests and instructions'
        )
        db.session.add(new_value)
        
        # Commit the changes
        db.session.commit()
        print("Successfully added Communication as a core value.")

if __name__ == '__main__':
    add_communication_value() 