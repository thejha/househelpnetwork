#!/usr/bin/env python3
import os
import sys
from flask import Flask
from sqlalchemy import create_engine, text, inspect
from extensions import db
from models import TaskList
from config import Config

# Create a minimal Flask app
app = Flask(__name__)

# Use the PostgreSQL URL from the config
database_uri = Config.SQLALCHEMY_DATABASE_URI
print(f"Using database: {database_uri}")

app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def check_and_create_task_list():
    with app.app_context():
        engine = db.engine
        inspector = inspect(engine)
        
        # List all tables in the database
        tables = inspector.get_table_names()
        print(f"Tables in database: {tables}")
        
        # Check if task_list table exists
        if 'task_list' not in tables:
            print("task_list table does not exist. Creating it now...")
            
            try:
                # Create the task_list table
                with engine.begin() as conn:
                    conn.execute(text("""
                    CREATE TABLE task_list (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50) NOT NULL,
                        category VARCHAR(50),
                        helper_type VARCHAR(20) NOT NULL DEFAULT 'maid',
                        is_main_task BOOLEAN DEFAULT FALSE,
                        parent_id INTEGER
                    )
                    """))
                
                print("Successfully created task_list table.")
                
                # Now populate with default tasks
                from populate_tasks import populate_maid_tasks
                populate_maid_tasks()
                
                print("Task list table has been created and populated successfully!")
                
            except Exception as e:
                print(f"An error occurred while creating the table: {str(e)}")
                sys.exit(1)
        else:
            print("task_list table already exists.")
            
            # Check if category column exists
            columns = [col['name'] for col in inspector.get_columns('task_list')]
            print(f"Columns in task_list: {columns}")
            
            if 'category' not in columns:
                print("Adding category column to task_list table...")
                try:
                    with engine.begin() as conn:
                        conn.execute(text("ALTER TABLE task_list ADD COLUMN category VARCHAR(50)"))
                    
                    print("Successfully added category column.")
                    
                    # Update categories based on main tasks
                    task_list = TaskList.query.all()
                    for task in task_list:
                        if task.is_main_task:
                            # For main tasks, use the name as the category
                            task.category = task.name
                        else:
                            # For subtasks, find the parent task and use its name as category
                            if task.parent_id:
                                parent_task = TaskList.query.filter_by(id=task.parent_id).first()
                                if parent_task:
                                    task.category = parent_task.name
                    
                    # Commit the changes
                    db.session.commit()
                    print("Successfully updated category values for existing tasks.")
                except Exception as e:
                    print(f"An error occurred: {str(e)}")
                    sys.exit(1)
            else:
                print("Category column already exists.")

if __name__ == '__main__':
    check_and_create_task_list()
    print("Database check completed!") 