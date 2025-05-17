"""
Seed script to populate the pincode_mapping table with data for major metro cities in India.
"""
import os
import sys
from app import app, db
from models import PincodeMapping
from flask import Flask

def seed_pincodes():
    """Create pincode mappings for major metro cities in India."""
    # Check if data already exists to avoid duplication
    if PincodeMapping.query.count() > 0:
        print("Pincode data already exists. Skipping seed operation.")
        return
    
    # List of pincode mappings for metro cities
    pincode_data = [
        # Mumbai
        {"pincode": "400001", "city": "Mumbai", "state": "Maharashtra", "society": "Fort Area"},
        {"pincode": "400051", "city": "Mumbai", "state": "Maharashtra", "society": "Bandra West"},
        {"pincode": "400076", "city": "Mumbai", "state": "Maharashtra", "society": "Powai Lake Residency"},
        {"pincode": "400053", "city": "Mumbai", "state": "Maharashtra", "society": "Juhu Beach Apartments"},
        {"pincode": "400025", "city": "Mumbai", "state": "Maharashtra", "society": "Prabhadevi Heights"},
        {"pincode": "400064", "city": "Mumbai", "state": "Maharashtra", "society": "Malad Galaxy Apartments"},
        
        # Delhi
        {"pincode": "110001", "city": "New Delhi", "state": "Delhi", "society": "Connaught Place"},
        {"pincode": "110016", "city": "New Delhi", "state": "Delhi", "society": "Hauz Khas Enclave"},
        {"pincode": "110017", "city": "New Delhi", "state": "Delhi", "society": "Green Park Extension"},
        {"pincode": "110024", "city": "New Delhi", "state": "Delhi", "society": "Lajpat Nagar Central"},
        {"pincode": "110025", "city": "New Delhi", "state": "Delhi", "society": "Defence Colony"},
        {"pincode": "110070", "city": "New Delhi", "state": "Delhi", "society": "Saket District Centre"},
        
        # Bangalore
        {"pincode": "560001", "city": "Bangalore", "state": "Karnataka", "society": "MG Road Center"},
        {"pincode": "560008", "city": "Bangalore", "state": "Karnataka", "society": "Shantinagar Housing"},
        {"pincode": "560011", "city": "Bangalore", "state": "Karnataka", "society": "Jayanagar 4th Block"},
        {"pincode": "560034", "city": "Bangalore", "state": "Karnataka", "society": "Koramangala Layout"},
        {"pincode": "560066", "city": "Bangalore", "state": "Karnataka", "society": "Whitefield Prestige"},
        {"pincode": "560103", "city": "Bangalore", "state": "Karnataka", "society": "Electronic City Phase 1"},
        
        # Chennai
        {"pincode": "600001", "city": "Chennai", "state": "Tamil Nadu", "society": "George Town"},
        {"pincode": "600006", "city": "Chennai", "state": "Tamil Nadu", "society": "Mylapore Temple View"},
        {"pincode": "600040", "city": "Chennai", "state": "Tamil Nadu", "society": "T Nagar Residency"},
        {"pincode": "600042", "city": "Chennai", "state": "Tamil Nadu", "society": "Velachery Lake View"},
        {"pincode": "600093", "city": "Chennai", "state": "Tamil Nadu", "society": "Adyar River Gardens"},
        {"pincode": "600119", "city": "Chennai", "state": "Tamil Nadu", "society": "Siruseri IT Park Housing"},
        
        # Hyderabad
        {"pincode": "500001", "city": "Hyderabad", "state": "Telangana", "society": "Charminar Complex"},
        {"pincode": "500008", "city": "Hyderabad", "state": "Telangana", "society": "Banjara Hills Road No 12"},
        {"pincode": "500016", "city": "Hyderabad", "state": "Telangana", "society": "Jubilee Hills Park View"},
        {"pincode": "500034", "city": "Hyderabad", "state": "Telangana", "society": "Gachibowli Heights"},
        {"pincode": "500081", "city": "Hyderabad", "state": "Telangana", "society": "HITEC City Serene Homes"},
        {"pincode": "500084", "city": "Hyderabad", "state": "Telangana", "society": "Kondapur Palm Meadows"},
        
        # Kolkata
        {"pincode": "700001", "city": "Kolkata", "state": "West Bengal", "society": "Dalhousie Square"},
        {"pincode": "700019", "city": "Kolkata", "state": "West Bengal", "society": "Ballygunge Place"},
        {"pincode": "700020", "city": "Kolkata", "state": "West Bengal", "society": "Alipore Gardens"},
        {"pincode": "700064", "city": "Kolkata", "state": "West Bengal", "society": "Salt Lake Sector 3"},
        {"pincode": "700091", "city": "Kolkata", "state": "West Bengal", "society": "New Town Action Area 1"},
        {"pincode": "700098", "city": "Kolkata", "state": "West Bengal", "society": "Rajarhat Newtown Heights"},
        
        # Pune
        {"pincode": "411001", "city": "Pune", "state": "Maharashtra", "society": "Shivaji Nagar"},
        {"pincode": "411004", "city": "Pune", "state": "Maharashtra", "society": "Koregaon Park"},
        {"pincode": "411006", "city": "Pune", "state": "Maharashtra", "society": "Aundh Royal Residency"},
        {"pincode": "411014", "city": "Pune", "state": "Maharashtra", "society": "Hadapsar IT Park Homes"},
        {"pincode": "411021", "city": "Pune", "state": "Maharashtra", "society": "Hinjewadi Phase 2"},
        {"pincode": "411045", "city": "Pune", "state": "Maharashtra", "society": "Baner Sus Road Villas"},
        
        # Ahmedabad
        {"pincode": "380001", "city": "Ahmedabad", "state": "Gujarat", "society": "Lal Darwaza"},
        {"pincode": "380006", "city": "Ahmedabad", "state": "Gujarat", "society": "Navrangpura Central"},
        {"pincode": "380015", "city": "Ahmedabad", "state": "Gujarat", "society": "Satellite Residency"},
        {"pincode": "380054", "city": "Ahmedabad", "state": "Gujarat", "society": "Bodakdev Heights"},
        {"pincode": "380059", "city": "Ahmedabad", "state": "Gujarat", "society": "Science City Road Villas"},
        {"pincode": "382424", "city": "Ahmedabad", "state": "Gujarat", "society": "GIFT City Towers"},
        
        # Jaipur
        {"pincode": "302001", "city": "Jaipur", "state": "Rajasthan", "society": "Pink City Center"},
        {"pincode": "302015", "city": "Jaipur", "state": "Rajasthan", "society": "Malviya Nagar Extension"},
        {"pincode": "302017", "city": "Jaipur", "state": "Rajasthan", "society": "Mansarovar Gardens"},
        {"pincode": "302018", "city": "Jaipur", "state": "Rajasthan", "society": "Vaishali Nagar"},
        {"pincode": "302021", "city": "Jaipur", "state": "Rajasthan", "society": "Jagatpura Heights"},
        {"pincode": "302029", "city": "Jaipur", "state": "Rajasthan", "society": "Pratap Nagar Enclave"}
    ]
    
    # Add pincode mappings to database
    for data in pincode_data:
        pincode_mapping = PincodeMapping(
            pincode=data["pincode"],
            city=data["city"],
            state=data["state"],
            society=data["society"]
        )
        db.session.add(pincode_mapping)
    
    try:
        db.session.commit()
        print(f"Successfully added {len(pincode_data)} pincode mappings to the database.")
    except Exception as e:
        db.session.rollback()
        print(f"Error adding pincode mappings: {e}")
        return False
    
    return True

if __name__ == "__main__":
    with app.app_context():
        seed_pincodes()