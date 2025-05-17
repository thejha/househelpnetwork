"""
Flask extensions initialization.
This file contains all the Flask extensions used in the application.
Centralizing them here helps avoid circular imports between app.py and models.py.
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect

# Define base model class for SQLAlchemy
class Base(DeclarativeBase):
    pass

# Initialize Flask extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()

# Configure login manager
login_manager.login_view = 'login'
login_manager.login_message_category = 'info' 