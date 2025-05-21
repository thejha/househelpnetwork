import os
import sys
from flask import Flask
from config import config
from extensions import db
from sqlalchemy import text, inspect

def create_app(config_name='development'):
    """Factory function to create and configure the Flask app."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    db.init_app(app)
    return app

def update_database():
    """Add tasks_average column to the reviews table."""
    app = create_app()
    
    with app.app_context():
        connection = db.engine.connect()
        inspector = inspect(db.engine)
        
        try:
            # Check if the column already exists
            columns = [column['name'] for column in inspector.get_columns('reviews')]
            if 'tasks_average' in columns:
                print("Column 'tasks_average' already exists in the 'reviews' table.")
            else:
                # Add the tasks_average column with a default value of 3
                # Using different syntax for different database types
                engine_name = db.engine.name
                
                if engine_name == 'postgresql':
                    connection.execute(text("ALTER TABLE reviews ADD COLUMN tasks_average FLOAT DEFAULT 3.0 NOT NULL"))
                    print("Added 'tasks_average' column to the 'reviews' table in PostgreSQL.")
                elif engine_name == 'sqlite':
                    connection.execute(text("ALTER TABLE reviews ADD COLUMN tasks_average FLOAT DEFAULT 3.0 NOT NULL"))
                    print("Added 'tasks_average' column to the 'reviews' table in SQLite.")
                elif engine_name == 'mysql':
                    connection.execute(text("ALTER TABLE reviews ADD COLUMN tasks_average FLOAT DEFAULT 3.0 NOT NULL"))
                    print("Added 'tasks_average' column to the 'reviews' table in MySQL.")
                else:
                    print(f"Unsupported database engine: {engine_name}")
                
            connection.commit()
            print("Database update completed successfully.")
                
        except Exception as e:
            print(f"Error updating database: {str(e)}")
        finally:
            connection.close()

if __name__ == "__main__":
    update_database() 