from extensions import db
from app import app
from models import HelperProfile
from sqlalchemy import text

def update_helper(helper_id, new_name, gender="female"):
    """
    Update a helper's name and gender in the database.
    
    Args:
        helper_id (str): The helper_id to update
        new_name (str): The correct name for the helper
        gender (str): The correct gender for the helper
    """
    with app.app_context():
        # Find the helper
        helper = HelperProfile.query.filter_by(helper_id=helper_id).first()
        
        if not helper:
            print(f"Helper with ID {helper_id} not found.")
            return
        
        print(f"Found helper: {helper.name} (ID: {helper.helper_id})")
        
        try:
            old_name = helper.name
            old_gender = helper.gender if helper.gender else "not specified"
            
            # Update the helper's name and gender
            helper.name = new_name
            helper.gender = gender
            
            # Commit the changes
            db.session.commit()
            print(f"Successfully updated helper {helper_id}:")
            print(f"Name changed from '{old_name}' to '{new_name}'")
            print(f"Gender changed from '{old_gender}' to '{gender}'")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error updating helper: {str(e)}")

if __name__ == "__main__":
    helper_id_to_update = "319527386586"
    new_name = "Megha Jha"
    update_helper(helper_id_to_update, new_name) 