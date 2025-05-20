from extensions import db
from app import app
from models import HelperProfile, User

def check_helper_deleted(helper_id):
    """
    Check if a helper with the given ID exists in the database.
    
    Args:
        helper_id (str): The helper_id to check
    """
    with app.app_context():
        # Check if helper exists
        helper = HelperProfile.query.filter_by(helper_id=helper_id).first()
        
        if helper:
            print(f"Helper {helper_id} still exists in the database:")
            print(f"  Name: {helper.name}")
            print(f"  ID: {helper.helper_id}")
            print(f"  Created by owner ID: {helper.created_by}")
            return False
        else:
            print(f"Helper {helper_id} has been successfully deleted.")
            return True

def check_owner_helpers(owner_id):
    """
    Check how many helpers are associated with a specific owner.
    
    Args:
        owner_id (int): The owner ID to check
    """
    with app.app_context():
        # Get the owner user
        owner = User.query.get(owner_id)
        
        if not owner:
            print(f"Owner with ID {owner_id} not found.")
            return
        
        # Count helpers created by this owner
        helpers = HelperProfile.query.filter_by(created_by=owner_id).all()
        
        print(f"Owner {owner.name} (ID: {owner_id}) has {len(helpers)} helpers:")
        
        if helpers:
            print("\nHelper details:")
            for helper in helpers:
                print(f"  - {helper.name} (ID: {helper.helper_id})")
        else:
            print("  No helpers found for this owner.")

if __name__ == "__main__":
    # Check if helper 319527386586 exists
    helper_id_to_check = "319527386586"
    is_deleted = check_helper_deleted(helper_id_to_check)
    
    if is_deleted:
        # Check all owners to find which ones have helpers
        with app.app_context():
            owners = User.query.filter_by(role='owner').all()
            for owner in owners:
                check_owner_helpers(owner.id)
    else:
        # If the helper still exists, check the associated owner
        with app.app_context():
            helper = HelperProfile.query.filter_by(helper_id=helper_id_to_check).first()
            if helper:
                check_owner_helpers(helper.created_by) 