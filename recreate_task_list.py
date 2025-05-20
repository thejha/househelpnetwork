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

def recreate_task_list():
    try:
        with engine.connect() as conn:
            # Drop the existing table if it exists
            conn.execute(text("DROP TABLE IF EXISTS task_list CASCADE"))
            conn.commit()
            print("Dropped task_list table if it existed.")
            
            # Create the table with all required columns
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
            print("Created new task_list table with all columns.")
            
            # Define maid tasks by category - simplified names
            maid_tasks = {
                "Cleaning": [
                    "Sweeping floors",
                    "Dusting furniture",
                    "Cleaning bathrooms",
                    "Cleaning kitchens",
                    "Cleaning fans and lights",
                    "Cleaning windows",
                    "Taking out trash",
                    "Organizing spaces"
                ],
                "Cooking": [
                    "Preparing meals",
                    "Cutting vegetables",
                    "Making tea/coffee",
                    "Cooking for guests",
                    "Reheating food"
                ],
                "Dishwashing": [
                    "Washing utensils",
                    "Cleaning vessels"
                ],
                "Laundry": [
                    "Washing clothes",
                    "Drying clothes",
                    "Ironing clothes",
                    "Folding clothes",
                    "Dry cleaning pickups"
                ],
                "Home Organization": [
                    "Making beds",
                    "Changing linens",
                    "Organizing wardrobes",
                    "Restocking supplies"
                ],
                "Childcare": [
                    "Feeding children",
                    "Bathing children",
                    "Diaper changing",
                    "Putting to sleep",
                    "Supervising play",
                    "School drop/pickup"
                ],
                "Elderly Care": [
                    "Mobility assistance",
                    "Medication reminders",
                    "Preparing special meals",
                    "Providing companionship"
                ],
                "Errands": [
                    "Grocery shopping",
                    "Paying bills",
                    "Managing deliveries",
                    "Pet care"
                ],
                "Event Help": [
                    "Pre/post event cleaning",
                    "Food preparation",
                    "Setting up events"
                ]
            }

            print("Populating maid tasks...")
            task_counter = 0
            
            # Insert maid tasks using raw SQL
            for category, tasks in maid_tasks.items():
                # Insert main task
                main_task_query = text("""
                INSERT INTO task_list (name, category, helper_type, is_main_task)
                VALUES (:name, :category, 'maid', TRUE)
                RETURNING id
                """)
                
                result = conn.execute(main_task_query, 
                                     {"name": category, "category": category})
                main_task_id = result.scalar()
                task_counter += 1
                
                # Insert subtasks
                for task_name in tasks:
                    subtask_query = text("""
                    INSERT INTO task_list (name, category, helper_type, is_main_task, parent_id)
                    VALUES (:name, :category, 'maid', FALSE, :parent_id)
                    """)
                    
                    conn.execute(subtask_query, 
                                {"name": task_name, "category": category, "parent_id": main_task_id})
                    task_counter += 1
            
            # Define driver tasks by category - simplified names
            driver_tasks = {
                "Driving": [
                    "School/office rides",
                    "Shopping trips",
                    "Airport transfers",
                    "Outstation trips",
                    "Weekend outings"
                ],
                "Vehicle Maintenance": [
                    "Cleaning vehicle",
                    "Scheduling services",
                    "Refueling",
                    "Tire and fluid checks"
                ],
                "Errands": [
                    "Grocery pickup",
                    "Package delivery",
                    "Bill payments"
                ]
            }
            
            print("Populating driver tasks...")
            # Insert driver tasks using raw SQL
            for category, tasks in driver_tasks.items():
                # Insert main task
                main_task_query = text("""
                INSERT INTO task_list (name, category, helper_type, is_main_task)
                VALUES (:name, :category, 'driver', TRUE)
                RETURNING id
                """)
                
                result = conn.execute(main_task_query, 
                                     {"name": category, "category": category})
                main_task_id = result.scalar()
                task_counter += 1
                
                # Insert subtasks
                for task_name in tasks:
                    subtask_query = text("""
                    INSERT INTO task_list (name, category, helper_type, is_main_task, parent_id)
                    VALUES (:name, :category, 'driver', FALSE, :parent_id)
                    """)
                    
                    conn.execute(subtask_query, 
                                {"name": task_name, "category": category, "parent_id": main_task_id})
                    task_counter += 1
            
            conn.commit()
            print(f"Successfully populated {task_counter} tasks!")
            
            # Verify the task count
            result = conn.execute(text("SELECT COUNT(*) FROM task_list")).scalar()
            print(f"Verified task count: {result}")
            
            # Show sample tasks
            sample = conn.execute(text("""
                SELECT id, name, category, helper_type, is_main_task, parent_id 
                FROM task_list 
                LIMIT 10
            """)).fetchall()
            
            print("\nSample tasks:")
            for row in sample:
                print(f"ID: {row[0]}, Name: {row[1]}, Category: {row[2]}, " +
                      f"Helper Type: {row[3]}, Is Main: {row[4]}, Parent ID: {row[5]}")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    recreate_task_list()
    print("\nTask list recreation and population completed!") 