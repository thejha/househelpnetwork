#!/usr/bin/env python3
import os
import sys
from sqlalchemy import create_engine, text
from config import Config

# Use the PostgreSQL URL from the config
database_uri = Config.SQLALCHEMY_DATABASE_URI
print(f"Using database: {database_uri}")

# Create direct engine connection to execute raw SQL
engine = create_engine(database_uri)

def verify_task_list():
    try:
        with engine.connect() as conn:
            # Check table info
            print("Table information from PostgreSQL's information_schema:")
            result = conn.execute(text("""
                SELECT column_name, data_type, character_maximum_length, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'task_list'
                ORDER BY ordinal_position
            """)).fetchall()
            
            for row in result:
                print(f"Column: {row[0]}, Type: {row[1]}", end="")
                if row[2]:
                    print(f"({row[2]})", end="")
                print(f", Nullable: {row[3]}")
            
            # Check task count
            count = conn.execute(text("SELECT COUNT(*) FROM task_list")).scalar()
            print(f"\nNumber of tasks in task_list: {count}")
            
            # Use explicit column names in select to avoid errors
            sample = conn.execute(text("""
                SELECT id, name, 
                       category, 
                       COALESCE(helper_type, 'maid') as helper_type, 
                       COALESCE(is_main_task, false) as is_main_task, 
                       parent_id
                FROM task_list 
                LIMIT 10
            """)).fetchall()
            
            print("\nSample tasks:")
            for row in sample:
                print(f"ID: {row[0]}, Name: {row[1]}, Category: {row[2]}, Helper Type: {row[3]}, Is Main: {row[4]}, Parent ID: {row[5]}")
                
            # Check if any tasks have null for critical columns
            null_helper_type = conn.execute(text("SELECT COUNT(*) FROM task_list WHERE helper_type IS NULL")).scalar()
            null_is_main_task = conn.execute(text("SELECT COUNT(*) FROM task_list WHERE is_main_task IS NULL")).scalar()
            
            print(f"\nTasks with NULL helper_type: {null_helper_type}")
            print(f"Tasks with NULL is_main_task: {null_is_main_task}")
            
            if null_helper_type > 0 or null_is_main_task > 0:
                print("\nFIXING NULL VALUES...")
                conn.execute(text("UPDATE task_list SET helper_type = 'maid' WHERE helper_type IS NULL"))
                conn.execute(text("UPDATE task_list SET is_main_task = FALSE WHERE is_main_task IS NULL"))
                conn.commit()
                print("Fixed NULL values.")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    verify_task_list()
    print("\nTask list verification completed!") 