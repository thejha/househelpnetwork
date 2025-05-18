import logging
import requests
import json

logger = logging.getLogger(__name__)

# API credentials
API_KEY = "key_live_5FG3zMrDHspKWq5ifOBYBi5J3rcadaGK"
API_SECRET = "secret_live_qRHK9amHpJhX3Txja8Aw1pIqMBPA2pTy"
API_VERSION = "2.0"

def get_access_token():
    """Generate an access token from Sandbox API."""
    url = "https://api.sandbox.co.in/authenticate"
    
    headers = {
        "accept": "application/json",
        "x-api-key": API_KEY,
        "x-api-secret": API_SECRET,
        "x-api-version": API_VERSION
    }
    
    try:
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Extract the access token
            access_token = data.get("access_token")
            logger.info("Successfully generated access token")
            return {
                "success": True,
                "access_token": access_token,
                "message": "Access token generated successfully"
            }
        else:
            logger.error(f"Failed to get access token: {response.status_code} - {response.text}")
            return {
                "success": False,
                "message": f"Failed to authenticate: {response.text}"
            }
    except Exception as e:
        logger.error(f"Exception when getting access token: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

def request_aadhaar_otp(access_token, aadhaar_number):
    """Request OTP for Aadhaar verification."""
    url = "https://api.sandbox.co.in/kyc/aadhaar/okyc/otp"
    
    payload = {
        "@entity": "in.co.sandbox.kyc.aadhaar.okyc.otp.request",
        "aadhaar_number": aadhaar_number,
        "consent": "Y",
        "reason": "kyc"
    }
    
    headers = {
        "accept": "application/json",
        "authorization": access_token,
        "x-api-key": API_KEY,
        "x-api-version": API_VERSION,
        "content-type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Extract the reference ID
            if "data" in data and "reference_id" in data["data"]:
                reference_id = data["data"]["reference_id"]
                message = data["data"].get("message", "OTP sent successfully")
                return {
                    "success": True,
                    "reference_id": reference_id,
                    "message": message
                }
            else:
                return {
                    "success": False,
                    "message": "No reference ID found in response"
                }
        else:
            logger.error(f"Failed to request OTP: {response.status_code} - {response.text}")
            return {
                "success": False,
                "message": f"Failed to request OTP: {response.text}"
            }
    except Exception as e:
        logger.error(f"Exception when requesting OTP: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

def verify_aadhaar_otp(access_token, reference_id, otp):
    """Verify OTP for Aadhaar verification."""
    url = "https://api.sandbox.co.in/kyc/aadhaar/okyc/otp/verify"
    
    payload = {
        "@entity": "in.co.sandbox.kyc.aadhaar.okyc.request",
        "reference_id": str(reference_id),
        "otp": str(otp)
    }
    
    headers = {
        "accept": "application/json",
        "authorization": access_token,
        "x-api-key": API_KEY,
        "x-api-version": API_VERSION,
        "content-type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Extract Aadhaar data
            if "data" in data:
                aadhaar_data = data["data"]
                return {
                    "success": True,
                    "aadhaar_data": aadhaar_data
                }
            else:
                return {
                    "success": False,
                    "message": "No Aadhaar data found in response"
                }
        else:
            logger.error(f"Failed to verify OTP: {response.status_code} - {response.text}")
            return {
                "success": False,
                "message": f"Failed to verify OTP: {response.text}"
            }
    except Exception as e:
        logger.error(f"Exception when verifying OTP: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        } 