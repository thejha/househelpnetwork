from extensions import db
from app import app
from models import HelperProfile, User

def check_helper_data(helper_id):
    """
    Check if a helper with the given ID exists in the database and print its data.
    
    Args:
        helper_id (str): The helper_id to check
    """
    with app.app_context():
        # Check if helper exists
        helper = HelperProfile.query.filter_by(helper_id=helper_id).first()
        
        if helper:
            print(f"Helper {helper_id} found in the database:")
            print(f"  Name: {helper.name}")
            print(f"  ID: {helper.helper_id}")
            print(f"  Created by owner ID: {helper.created_by}")
            
            # Print all attributes
            print("\nAll attributes:")
            for key, value in helper.__dict__.items():
                if not key.startswith('_'):
                    print(f"  {key}: {value}")
        else:
            print(f"Helper {helper_id} not found in the database.")

if __name__ == "__main__":
    helper_id_to_check = "319527386586"
    check_helper_data(helper_id_to_check) 