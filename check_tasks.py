from flask import Flask
from extensions import db
from models import TaskList

# Create a minimal Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def check_tasks():
    with app.app_context():
        # Count tasks by helper type
        maid_tasks = TaskList.query.filter_by(helper_type='maid').count()
        driver_tasks = TaskList.query.filter_by(helper_type='driver').count()
        
        print(f"Total maid tasks: {maid_tasks}")
        print(f"Total driver tasks: {driver_tasks}")
        
        # Show maid task categories
        maid_categories = TaskList.query.filter_by(helper_type='maid', is_main_task=True).all()
        print("\nMaid Task Categories:")
        for category in maid_categories:
            print(f"- {category.name}")
        
        # Show driver task categories
        driver_categories = TaskList.query.filter_by(helper_type='driver', is_main_task=True).all()
        print("\nDriver Task Categories:")
        for category in driver_categories:
            print(f"- {category.name}")

if __name__ == '__main__':
    check_tasks() 