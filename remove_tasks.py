from flask import Flask
from extensions import db
from models import TaskList

# Create a minimal Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost:5432/household_help'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def remove_tasks():
    with app.app_context():
        # List of task names to remove (exact names)
        tasks_to_remove = [
            "Reheating food",
            "Preparing meals",
            "Cleaning",
            "Cleaning vessels",
            "Laundry",
            "Childcare", 
            "Elderly Care",
            "Errands",
            "Event Help"
        ]
        
        # First, print existing tasks for reference
        print("Current tasks in database before removal:")
        all_tasks = TaskList.query.all()
        print(f"Total tasks: {len(all_tasks)}")
        
        # Group by category for easier viewing
        tasks_by_category = {}
        for task in all_tasks:
            category = task.category or "Uncategorized"
            if category not in tasks_by_category:
                tasks_by_category[category] = []
            tasks_by_category[category].append(task)
        
        for category, tasks in tasks_by_category.items():
            print(f"\nCategory: {category} ({len(tasks)} tasks)")
            for task in tasks:
                print(f"  ID: {task.id} | Name: {task.name} | Main Task: {task.is_main_task}")
        
        print("\nRemoving tasks...")
        
        # First approach: Remove by exact names
        removed_count = 0
        for task_name in tasks_to_remove:
            tasks = TaskList.query.filter_by(name=task_name).all()
            for task in tasks:
                print(f"Removing task (exact match): ID {task.id} | {task.name} | {task.category}")
                db.session.delete(task)
                removed_count += 1
        
        # Second approach: Remove main category tasks and their sub-tasks
        for category_name in tasks_to_remove:
            # Find main tasks with this category
            main_tasks = TaskList.query.filter_by(category=category_name).all()
            for task in main_tasks:
                if task.name != category_name:  # Avoid duplicate deletions
                    print(f"Removing task (category match): ID {task.id} | {task.name} | {task.category}")
                    db.session.delete(task)
                    removed_count += 1
        
        # Commit changes
        db.session.commit()
        print(f"\nRemoved {removed_count} tasks from database")
        
        # Verify tasks were removed
        remaining_tasks = TaskList.query.filter(TaskList.name.in_(tasks_to_remove)).all()
        if remaining_tasks:
            print("\nWarning: Some tasks still remain with the same names:")
            for task in remaining_tasks:
                print(f"  ID: {task.id} | Name: {task.name} | Category: {task.category}")
        else:
            print("\nAll specified tasks were successfully removed!")
        
        # Print total count after removal
        final_count = TaskList.query.count()
        print(f"\nFinal task count: {final_count} (removed {len(all_tasks) - final_count} tasks)")

if __name__ == '__main__':
    remove_tasks() 