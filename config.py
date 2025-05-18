import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """Base configuration class."""
    # Secret key for session management
    SECRET_KEY = os.environ.get("SESSION_SECRET", "househelpnetwork_secret_key")
    
    # Database settings
    POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "rmivuxg")
    POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.environ.get("POSTGRES_DB", "househelpnetwork")
    
    # Build PostgreSQL connection string
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", 
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    
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
    UPLOADCARE_PUBLIC_KEY = os.environ.get("UPLOADCARE_PUBLIC_KEY", "key_live_5FG3zMrDHspKWq5ifOBYBi5J3rcadaGK")
    UPLOADCARE_SECRET_KEY = os.environ.get("UPLOADCARE_SECRET_KEY", "secret_live_qRHK9amHpJhX3Txja8Aw1pIqMBPA2pTy")


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


# Configuration dictionary to select the appropriate configuration
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 