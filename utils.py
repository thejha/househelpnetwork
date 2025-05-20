import os
import uuid
import requests
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app
import logging

logger = logging.getLogger(__name__)

def save_file(file, subfolder):
    """Save an uploaded file and return the file path."""
    if not file:
        return None
    
    # Create a secure filename
    filename = secure_filename(file.filename)
    # Generate a unique filename to avoid collisions
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    
    # Determine the upload folder path
    upload_folder = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'], subfolder)
    # Ensure the directory exists
    os.makedirs(upload_folder, exist_ok=True)
    
    # Create the full file path
    file_path = os.path.join(upload_folder, unique_filename)
    
    # Save the file
    try:
        file.save(file_path)
        # Return the URL path for the file
        return f"/uploads/{subfolder}/{unique_filename}"
    except Exception as e:
        current_app.logger.error(f"Error saving file: {e}")
        return None

def get_uploadcare_file_info(file_uuid):
    """Get file info from Uploadcare API."""
    if not file_uuid:
        return None
    
    api_url = f"https://api.uploadcare.com/files/{file_uuid}/"
    headers = {
        "Accept": "application/vnd.uploadcare-v0.7+json",
        "Authorization": f"Uploadcare.Simple {current_app.config['UPLOADCARE_PUBLIC_KEY']}:{current_app.config['UPLOADCARE_SECRET_KEY']}"
    }
    
    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            current_app.logger.error(f"Error getting file info from Uploadcare: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        current_app.logger.error(f"Exception getting file info from Uploadcare: {e}")
        return None

def process_uploadcare_url(cdn_url):
    """Extract file UUID from Uploadcare CDN URL."""
    if not cdn_url:
        return None
    
    # Extract UUID from URL
    # URL format: https://ucarecdn.com/UUID/
    # or https://ucarecdn.com/UUID/filename
    parts = cdn_url.strip('/').split('/')
    for part in parts:
        if '-' in part and len(part) > 30:  # Typical UUID format
            return part
    
    return None

def get_unique_id(prefix=''):
    """Generate a unique ID with an optional prefix."""
    unique_id = str(uuid.uuid4()).replace('-', '')[:10]
    if prefix:
        return f"{prefix}_{unique_id}"
    return unique_id

def send_notification(to_email, subject, message):
    """
    Send a notification email.
    In a real app, this would use a service like SendGrid, SMTP, etc.
    For now, just log the message.
    """
    # Log the notification for demonstration purposes
    current_app.logger.info(f"NOTIFICATION to {to_email}: {subject} - {message}")
    
    # In a real application, uncomment and implement actual email sending
    # try:
    #     # Send email using SMTP or a service like SendGrid
    #     # ...
    #     return True
    # except Exception as e:
    #     current_app.logger.error(f"Error sending notification: {e}")
    #     return False
    
    # Simulate success for now
    return True
