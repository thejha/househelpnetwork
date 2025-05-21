import os
import logging
import re
from flask import Flask, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
import mysql.connector
from config import config
from extensions import db, login_manager, bcrypt, csrf

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_db(config_name='default'):
    """Get a MySQL database connection using settings from config."""
    # Get the appropriate configuration
    app_config = config[config_name]
    
    conn = mysql.connector.connect(
        user=app_config.MYSQL_USER,
        password=app_config.MYSQL_PASSWORD,
        host=app_config.MYSQL_HOST,
        port=app_config.MYSQL_PORT,
        database=app_config.MYSQL_DATABASE
    )
    return conn

def slugify(value):
    """
    Convert a string to a URL-friendly slug.
    """
    # Convert to lowercase and replace spaces with hyphens
    value = value.lower().strip()
    value = re.sub(r'[^\w\s-]', '', value)
    value = re.sub(r'[\s_-]+', '-', value)
    return value

def create_app(config_name='default'):
    """Factory function to create and configure the Flask app."""
    # Initialize Flask application
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Configure the app
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Enhance session security and persistence
    app.config['SESSION_COOKIE_SECURE'] = app.config.get('SESSION_COOKIE_SECURE', False)  # Set to True in production
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = app.config.get('PERMANENT_SESSION_LIFETIME', 3600)  # 1 hour default
    app.config['SESSION_TYPE'] = 'filesystem'  # More reliable than the default
    
    # Ensure upload folders exist
    upload_folder = app.config['UPLOAD_FOLDER']
    os.makedirs(os.path.join(app.root_path, upload_folder, 'helper_photos'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, upload_folder, 'helper_documents'), exist_ok=True)
    
    # Add custom filters to Jinja environment
    app.jinja_env.filters['slugify'] = slugify
    
    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    
    # Configure session handling
    from flask_session import Session
    Session(app)
    
    with app.app_context():
        # Import models and create tables
        from models import User  # This will load all models
        db.create_all()
        
        # Register routes
        from routes import register_routes
        register_routes(app)
    
    return app

# Create the application instance using environment variable or default to development
app = create_app(os.getenv('FLASK_ENV', 'development'))

@app.route('/api/check-aadhaar', methods=['POST'])
def check_aadhaar():
    data = request.get_json()
    aadhaar_id = data.get('aadhaar_id')
    
    if not aadhaar_id:
        return jsonify({'error': 'Aadhaar ID is required'}), 400
        
    try:
        # Use the same configuration as the Flask app
        conn = get_db(os.getenv('FLASK_ENV', 'development'))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM owner_profiles 
            WHERE aadhaar_id = %s
        """, (aadhaar_id,))
        
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        return jsonify({
            'available': count == 0,
            'message': 'Aadhaar number is already registered' if count > 0 else 'Aadhaar number is available'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
