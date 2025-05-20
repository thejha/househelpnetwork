from flask import Flask
from extensions import db
from models import TaskList

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost:5432/household_help'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def remove_tasks():
    with app.app_context():
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
        
        print("Removing tasks...")
        
        for task_name in tasks_to_remove:
            # 1. Remove exact matches
            tasks = TaskList.query.filter_by(name=task_name).all()
            for task in tasks:
                print(f"Removing: {task.name}")
                db.session.delete(task)
                
            # 2. Remove as categories
            category_tasks = TaskList.query.filter_by(category=task_name).all()
            for task in category_tasks:
                print(f"Removing from category '{task_name}': {task.name}")
                db.session.delete(task)
        
        # Commit changes
        db.session.commit()
        print("Tasks removed successfully")

if __name__ == '__main__':
    remove_tasks() 