#!/usr/bin/env python3
import os
import sys
from flask import Flask
from sqlalchemy import create_engine, text
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

def add_category_column():
    with app.app_context():
        engine = db.engine
        
        # Check if column already exists
        inspector = db.inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('task_list')]
        
        if 'category' in columns:
            print("The 'category' column already exists in task_list table.")
            return
        
        try:
            # Add the category column to PostgreSQL
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE task_list ADD COLUMN category VARCHAR(50)"))
            
            print("Successfully added 'category' column to task_list table.")
            
            # Update the categories based on parent tasks
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

if __name__ == '__main__':
    add_category_column()
    print("Migration completed successfully!") 