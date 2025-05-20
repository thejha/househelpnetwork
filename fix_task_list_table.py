#!/usr/bin/env python3
import os
import sys
from flask import Flask
from sqlalchemy import create_engine, text, inspect
from config import Config

# Create a minimal Flask app
app = Flask(__name__)

# Use the PostgreSQL URL from the config
database_uri = Config.SQLALCHEMY_DATABASE_URI
print(f"Using database: {database_uri}")

# Create direct engine connection to execute raw SQL
engine = create_engine(database_uri)

def fix_task_list_table():
    try:
        # Use SQLAlchemy engine directly to avoid model loading issues
        with engine.connect() as conn:
            # Check table structure
            inspector = inspect(engine)
            if 'task_list' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('task_list')]
                print(f"Current columns in task_list: {columns}")
                
                # Add missing columns
                missing_columns = []
                if 'helper_type' not in columns:
                    missing_columns.append(("helper_type", "VARCHAR(20) NOT NULL DEFAULT 'maid'"))
                if 'is_main_task' not in columns:
                    missing_columns.append(("is_main_task", "BOOLEAN DEFAULT FALSE"))
                if 'parent_id' not in columns:
                    missing_columns.append(("parent_id", "INTEGER"))
                if 'category' not in columns:
                    missing_columns.append(("category", "VARCHAR(50)"))
                
                # Add each missing column
                for col_name, col_type in missing_columns:
                    print(f"Adding missing column: {col_name}")
                    conn.execute(text(f"ALTER TABLE task_list ADD COLUMN {col_name} {col_type}"))
                
                if missing_columns:
                    conn.commit()
                    print("Successfully added missing columns.")
                else:
                    print("No missing columns to add.")
                
                # Now check again
                columns = [col['name'] for col in inspector.get_columns('task_list')]
                print(f"Updated columns in task_list: {columns}")
                
                # Check if there's any data 
                result = conn.execute(text("SELECT COUNT(*) FROM task_list")).scalar()
                print(f"Number of records in task_list: {result}")
                
                if result == 0:
                    print("Table is empty. You should run populate_tasks.py to add tasks.")
                else:
                    # Sample some data
                    sample = conn.execute(text("SELECT * FROM task_list LIMIT 5")).fetchall()
                    print("\nSample records:")
                    for row in sample:
                        print(row)
                        
            else:
                print("task_list table does not exist. Will create it.")
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
                conn.commit()
                print("Successfully created task_list table.")
                
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    fix_task_list_table()
    print("\nTask list table fix completed!") 