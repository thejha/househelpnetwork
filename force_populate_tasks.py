#!/usr/bin/env python3
import os
import sys
from flask import Flask
from sqlalchemy import create_engine, text
from config import Config
from extensions import db
from models import TaskList

# Create a minimal Flask app
app = Flask(__name__)

# Use the PostgreSQL URL from the config
database_uri = Config.SQLALCHEMY_DATABASE_URI
print(f"Using database: {database_uri}")

app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def force_populate_maid_tasks():
    with app.app_context():
        # Check current count
        task_count = TaskList.query.count()
        print(f"Current task count: {task_count}")
        
        # Clear existing tasks if any
        if task_count > 0:
            print("Deleting existing tasks...")
            TaskList.query.delete()
            db.session.commit()
            print("All existing tasks deleted.")

        # Define maid tasks by category
        maid_tasks = {
            "🧹 Cleaning": [
                "Sweeping and mopping floors",
                "Dusting furniture and surfaces",
                "Cleaning bathrooms (toilets, sinks, mirrors, tiles)",
                "Cleaning kitchens (counters, sinks, tiles)",
                "Cleaning fans, lights, and switchboards",
                "Cleaning windows and grills",
                "Taking out the trash",
                "Organizing cluttered spaces"
            ],
            "🍽️ Cooking": [
                "Preparing full meals (breakfast, lunch, dinner)",
                "Cutting and chopping vegetables",
                "Making tea/coffee/snacks",
                "Cooking for guests during gatherings",
                "Reheating food and serving"
            ],
            "🧼 Dishwashing": [
                "Washing utensils (by hand or using a dishwasher)",
                "Cleaning cooking vessels (including greasy ones)"
            ],
            "👕 Laundry": [
                "Washing clothes (by hand or using a washing machine)",
                "Drying clothes (hanging on a line or using a dryer)",
                "Ironing clothes",
                "Folding and organizing clothes",
                "Occasional dry cleaning pickups/drops (if instructed)"
            ],
            "🛏️ Home Organization": [
                "Making beds",
                "Changing bed linens",
                "Organizing wardrobes",
                "Restocking supplies (like toilet paper, soap, etc.)"
            ],
            "👶 Childcare": [
                "Feeding the child",
                "Bathing and dressing the child",
                "Diaper changing",
                "Putting the child to sleep",
                "Playing or supervising play",
                "Picking up/dropping off at school or classes"
            ],
            "🧓 Elderly Care": [
                "Assisting with mobility",
                "Helping with medication reminders",
                "Preparing special meals",
                "Providing company/conversation"
            ],
            "🛒 Other Errands": [
                "Grocery shopping",
                "Paying utility bills",
                "Receiving and managing deliveries",
                "Pet care (feeding, walking dogs, cleaning litter)"
            ],
            "🎉 Event-Related Help": [
                "Cleaning before/after parties",
                "Assisting with food preparation or serving",
                "Setting up for events (decorations, etc.)"
            ]
        }

        print("Creating maid tasks...")
        task_counter = 0
        # Create tasks in database
        for category, tasks in maid_tasks.items():
            # First create a main task for the category
            main_task = TaskList(
                name=category,
                category=category,
                helper_type='maid',
                is_main_task=True
            )
            db.session.add(main_task)
            db.session.flush()  # To get the ID
            task_counter += 1
            
            # Now add the subtasks
            for task_name in tasks:
                subtask = TaskList(
                    name=task_name,
                    category=category,
                    helper_type='maid',
                    is_main_task=False,
                    parent_id=main_task.id
                )
                db.session.add(subtask)
                task_counter += 1
        
        # Add some driver tasks
        driver_tasks = {
            "🚗 Driving": [
                "School/office drop and pickup",
                "Shopping mall visits",
                "Airport/railway station transfers",
                "Outstation trips",
                "Weekend outings"
            ],
            "🔧 Vehicle Maintenance": [
                "Regular cleaning of vehicle",
                "Scheduling maintenance services",
                "Refueling the vehicle",
                "Checking tire pressure and fluids"
            ],
            "🛍️ Errands": [
                "Grocery pickup",
                "Package delivery",
                "Bill payments"
            ]
        }
        
        print("Creating driver tasks...")
        for category, tasks in driver_tasks.items():
            # First create a main task for the category
            main_task = TaskList(
                name=category,
                category=category,
                helper_type='driver',
                is_main_task=True
            )
            db.session.add(main_task)
            db.session.flush()  # To get the ID
            task_counter += 1
            
            # Now add the subtasks
            for task_name in tasks:
                subtask = TaskList(
                    name=task_name,
                    category=category,
                    helper_type='driver',
                    is_main_task=False,
                    parent_id=main_task.id
                )
                db.session.add(subtask)
                task_counter += 1
        
        # Commit all changes
        db.session.commit()
        print(f"Successfully populated {task_counter} tasks!")
        
        # Verify the count
        final_count = TaskList.query.count()
        print(f"Verified task count: {final_count}")

if __name__ == '__main__':
    force_populate_maid_tasks() 