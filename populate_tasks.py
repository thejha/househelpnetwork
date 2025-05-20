import os
import sys
from flask import Flask
from extensions import db
from models import TaskList

# Create a minimal Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Update this with your actual database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def populate_maid_tasks():
    with app.app_context():
        # Check if tasks already exist
        existing_tasks = TaskList.query.filter_by(helper_type='maid').count()
        if existing_tasks > 0:
            print(f"Found {existing_tasks} existing maid tasks. Skipping.")
            return

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
        
        # Commit all changes
        db.session.commit()
        print("Successfully populated maid and driver tasks!")

if __name__ == '__main__':
    populate_maid_tasks() 