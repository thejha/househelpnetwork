import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """Base configuration class."""
    # Secret key for session management
    SECRET_KEY = "househelpnetwork_secret_key"
    
    # Database settings
    MYSQL_USER = "root"
    MYSQL_PASSWORD = "rmivuxg"
    MYSQL_HOST = "localhost"
    MYSQL_PORT = "3306"
    MYSQL_DATABASE = "househelpnetwork"
    
    # Build MySQL connection string
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    
    # Flask-SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    UPLOAD_FOLDER = "static/uploads"
    
    # Uploadcare API keys
    UPLOADCARE_PUBLIC_KEY = "key_live_5FG3zMrDHspKWq5ifOBYBi5J3rcadaGK"
    UPLOADCARE_SECRET_KEY = "secret_live_qRHK9amHpJhX3Txja8Aw1pIqMBPA2pTy"


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    # Production MySQL settings can be overridden here if needed
    MYSQL_HOST = "production-db-server"
    # Update the database URI with production settings
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{Config.MYSQL_USER}:{Config.MYSQL_PASSWORD}@{MYSQL_HOST}:{Config.MYSQL_PORT}/{Config.MYSQL_DATABASE}"


# Configuration dictionary to select the appropriate configuration
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 