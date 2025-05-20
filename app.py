import os
import logging
from flask import Flask, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from config import config
from extensions import db, login_manager, bcrypt, csrf

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_app(config_name='default'):
    """Factory function to create and configure the Flask app."""
    # Initialize Flask application
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Configure the app
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Ensure upload folders exist
    upload_folder = app.config['UPLOAD_FOLDER']
    os.makedirs(os.path.join(app.root_path, upload_folder, 'helper_photos'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, upload_folder, 'helper_documents'), exist_ok=True)
    
    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    
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
        cursor = get_db().cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM owner_profiles 
            WHERE aadhaar_id = %s
        """, (aadhaar_id,))
        
        count = cursor.fetchone()[0]
        return jsonify({
            'available': count == 0,
            'message': 'Aadhaar number is already registered' if count > 0 else 'Aadhaar number is available'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
