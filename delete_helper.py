from extensions import db
from app import app
from models import HelperProfile, HelperDocument, Contract, Review, IncidentReport, OwnerToOwnerConnect
from sqlalchemy import text

def delete_helper(helper_id):
    """
    Delete a specific helper and all associated data from the database.
    
    Args:
        helper_id (str): The helper_id to delete
    """
    with app.app_context():
        # Find the helper
        helper = HelperProfile.query.filter_by(helper_id=helper_id).first()
        
        if not helper:
            print(f"Helper with ID {helper_id} not found.")
            return
        
        print(f"Found helper: {helper.name} (ID: {helper.helper_id})")
        helper_profile_id = helper.id
        
        try:
            # Delete associated OwnerToOwnerConnect records
            connects = OwnerToOwnerConnect.query.filter_by(helper_profile_id=helper_profile_id).all()
            for connect in connects:
                print(f"Deleting connect request: {connect.form_id}")
                db.session.delete(connect)
            
            # Delete associated reviews
            reviews = Review.query.filter_by(helper_profile_id=helper_profile_id).all()
            for review in reviews:
                print(f"Deleting review: {review.review_id}")
                db.session.delete(review)
            
            # Delete associated incident reports
            incidents = IncidentReport.query.filter_by(helper_profile_id=helper_profile_id).all()
            for incident in incidents:
                print(f"Deleting incident report: {incident.report_id}")
                db.session.delete(incident)
            
            # Delete associated contracts
            contracts = Contract.query.filter_by(helper_profile_id=helper_profile_id).all()
            for contract in contracts:
                print(f"Deleting contract: {contract.contract_id}")
                db.session.delete(contract)
            
            # Delete associated documents
            documents = HelperDocument.query.filter_by(helper_profile_id=helper_profile_id).all()
            for document in documents:
                print(f"Deleting document: {document.id}")
                db.session.delete(document)
            
            # Finally, delete the helper
            print(f"Deleting helper profile: {helper.name} (ID: {helper.helper_id})")
            db.session.delete(helper)
            
            # Commit the changes
            db.session.commit()
            print(f"Successfully deleted helper {helper_id} and all associated data.")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting helper: {str(e)}")

if __name__ == "__main__":
    helper_id_to_delete = "319527386586"
    delete_helper(helper_id_to_delete) 