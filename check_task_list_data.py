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

def check_and_populate_task_list():
    with app.app_context():
        # Count tasks in the table
        task_count = TaskList.query.count()
        print(f"Number of tasks in task_list table: {task_count}")
        
        if task_count == 0:
            print("Task list table is empty. Populating with default tasks...")
            try:
                # Import and run the populate tasks function
                from populate_tasks import populate_maid_tasks
                populate_maid_tasks()
                
                # Verify that tasks were added
                new_count = TaskList.query.count()
                print(f"Tasks added. New count: {new_count}")
                
            except Exception as e:
                print(f"Error populating tasks: {str(e)}")
                sys.exit(1)
        else:
            print("Task list table already has data.")
            
            # Sample some tasks to verify data integrity
            sample_tasks = TaskList.query.limit(5).all()
            print("\nSample tasks:")
            for task in sample_tasks:
                print(f"ID: {task.id}, Name: {task.name}, Category: {task.category}, Type: {task.helper_type}, Is Main: {task.is_main_task}")
            
            # Check if categories are set correctly
            null_category_count = TaskList.query.filter(TaskList.category == None).count()
            if null_category_count > 0:
                print(f"\nFound {null_category_count} tasks with NULL category. Updating...")
                
                # Update task categories
                tasks = TaskList.query.all()
                for task in tasks:
                    if task.category is None:
                        if task.is_main_task:
                            # For main tasks, use the name as the category
                            task.category = task.name
                        else:
                            # For subtasks, find the parent task and use its name as category
                            if task.parent_id:
                                parent_task = TaskList.query.filter_by(id=task.parent_id).first()
                                if parent_task and parent_task.category:
                                    task.category = parent_task.category
                
                # Commit changes
                db.session.commit()
                print("Categories updated successfully.")
            else:
                print("\nAll tasks have categories set correctly.")

if __name__ == '__main__':
    check_and_populate_task_list()
    print("\nTask list check completed!") 