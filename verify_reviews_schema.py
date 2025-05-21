import os
import sys
from flask import Flask
from config import config
from extensions import db
from sqlalchemy import inspect
from models import Review

def create_app(config_name='development'):
    """Factory function to create and configure the Flask app."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    db.init_app(app)
    return app

def verify_schema():
    """Verify the reviews table schema matches the model"""
    app = create_app()
    
    with app.app_context():
        # Get the inspector
        inspector = inspect(db.engine)
        
        # Get the actual columns in the reviews table
        table_columns = {column['name']: column for column in inspector.get_columns('reviews')}
        print("Database Table Columns:")
        for col_name, col_info in table_columns.items():
            print(f"  {col_name}: {col_info['type']}")
        
        # Get the columns from the model
        model_columns = {column.name: column for column in Review.__table__.columns}
        print("\nModel Columns:")
        for col_name, col_obj in model_columns.items():
            print(f"  {col_name}: {col_obj.type}")
        
        # Check for missing columns in the table
        missing_in_table = set(model_columns.keys()) - set(table_columns.keys())
        if missing_in_table:
            print(f"\nColumns in model but missing in table: {missing_in_table}")
        
        # Check for extra columns in the table
        extra_in_table = set(table_columns.keys()) - set(model_columns.keys())
        if extra_in_table:
            print(f"\nColumns in table but missing in model: {extra_in_table}")
        
        if not missing_in_table and not extra_in_table:
            print("\nThe table schema matches the model perfectly!")
        
if __name__ == "__main__":
    verify_schema() 