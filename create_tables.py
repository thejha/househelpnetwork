from flask import Flask
from extensions import db
import models  # Import all models to ensure they're registered

# Create a minimal Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Update this with your actual database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

if __name__ == '__main__':
    with app.app_context():
        print("Creating all database tables...")
        db.create_all()
        print("Tables created successfully!") 