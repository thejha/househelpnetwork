from flask import Flask
from flask_migrate import Migrate
from extensions import db
import models  # Import all models to ensure they're registered

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Update with your database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        print("Creating migration for database updates...")
        # In practice, you would run:
        # flask db migrate -m "Add task categories and contract work hours"
        # flask db upgrade
        print("To apply these migrations, run:")
        print("flask db init")
        print("flask db migrate -m \"Add task categories and contract work hours\"")
        print("flask db upgrade")
        print("\nThen run the populate_tasks.py script to add the task data.") 