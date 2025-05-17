import requests
import json
import logging

# API credentials
API_KEY = "key_live_ou2Lp9ySbBMcfPpE5a7mVaW41iEw5lmc"
API_SECRET = "secret_live_997hFk644JNNvJfjwfrVSOujHvjHjU1U"

# API endpoints
GENERATE_OTP_URL = "https://api.sandbox.co.in/kyc/aadhaar/okyc/otp"
VERIFY_OTP_URL = "https://api.sandbox.co.in/kyc/aadhaar/okyc/verify"

# Configure logging
logger = logging.getLogger(__name__)

def generate_aadhaar_otp(aadhaar_id):
    """
    Generate OTP for Aadhaar verification using Sandbox API
    
    Args:
        aadhaar_id (str): 12-digit Aadhaar ID
        
    Returns:
        dict: Response containing reference_id or error message
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "x-api-secret": API_SECRET
    }
    
    payload = {
        "aadhaar_number": aadhaar_id
    }
    
    try:
        response = requests.post(GENERATE_OTP_URL, headers=headers, json=payload)
        response_data = response.json()
        
        logger.info(f"Aadhaar OTP generation response: {response_data}")
        
        if response.status_code == 200 and "reference_id" in response_data:
            return {
                "success": True,
                "reference_id": response_data["reference_id"],
                "message": response_data.get("message", "OTP sent successfully")
            }
        else:
            return {
                "success": False,
                "message": response_data.get("message", "Failed to generate OTP"),
                "error_code": response_data.get("error_code", "UNKNOWN_ERROR")
            }
    except Exception as e:
        logger.error(f"Error generating Aadhaar OTP: {str(e)}")
        return {
            "success": False,
            "message": f"An error occurred: {str(e)}",
            "error_code": "API_ERROR"
        }

def verify_aadhaar_otp(reference_id, otp):
    """
    Verify OTP for Aadhaar verification using Sandbox API
    
    Args:
        reference_id (str): Reference ID from generate_otp call
        otp (str): 6-digit OTP received on registered mobile
        
    Returns:
        dict: Response containing verification status and user details
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "x-api-secret": API_SECRET
    }
    
    payload = {
        "reference_id": reference_id,
        "otp": otp
    }
    
    try:
        response = requests.post(VERIFY_OTP_URL, headers=headers, json=payload)
        response_data = response.json()
        
        logger.info(f"Aadhaar OTP verification response: {response_data}")
        
        if response.status_code == 200 and response_data.get("status") == "success":
            # Extract user details from response
            user_details = response_data.get("data", {})
            
            return {
                "success": True,
                "message": "Aadhaar verification successful",
                "user_details": {
                    "name": user_details.get("name", ""),
                    "gender": user_details.get("gender", ""),
                    "dob": user_details.get("dob", ""),
                    "address": user_details.get("address", {})
                }
            }
        else:
            return {
                "success": False,
                "message": response_data.get("message", "Failed to verify OTP"),
                "error_code": response_data.get("error_code", "UNKNOWN_ERROR")
            }
    except Exception as e:
        logger.error(f"Error verifying Aadhaar OTP: {str(e)}")
        return {
            "success": False,
            "message": f"An error occurred: {str(e)}",
            "error_code": "API_ERROR"
        } 