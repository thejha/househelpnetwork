import logging
import os
import random
import string
import uuid
import json
from flask import session, current_app
from sandbox_api import get_access_token, request_aadhaar_otp, verify_aadhaar_otp as sandbox_verify_otp
from models import AadhaarAPILog, db

logger = logging.getLogger(__name__)

# Store the access token in memory for reuse
access_token = None

def log_api_interaction(request_type, aadhaar_id=None, reference_id=None, request_payload=None, 
                        response_payload=None, success=False, error_message=None, user_id=None):
    """
    Log all API interactions to the database for audit and troubleshooting.
    """
    try:
        # Check if we're in a Flask app context
        if not current_app:
            logger.warning("No Flask app context found, API log won't be stored in database")
            return
        
        # Get session ID if available
        session_id = session.get('session_id', None)
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
        
        # Create log entry
        log_entry = AadhaarAPILog(
            aadhaar_id=aadhaar_id,
            reference_id=reference_id,
            request_type=request_type,
            request_payload=request_payload if isinstance(request_payload, dict) else None,
            response_payload=response_payload if isinstance(response_payload, dict) else None,
            success=success,
            error_message=error_message,
            user_id=user_id,
            session_id=session_id
        )
        
        db.session.add(log_entry)
        db.session.commit()
        logger.info(f"API log stored: {request_type}, success={success}")
        
    except Exception as e:
        logger.exception(f"Failed to log API interaction: {str(e)}")
        # Don't raise the exception - this is a secondary function

def get_stored_access_token():
    """Get the stored access token or generate a new one."""
    global access_token
    if not access_token:
        response = get_access_token()
        
        # Log API interaction
        log_api_interaction(
            request_type='token',
            request_payload={},
            response_payload=response,
            success=response.get("success", False),
            error_message=None if response.get("success", False) else response.get("message")
        )
        
        if response["success"]:
            access_token = response["access_token"]
        else:
            logger.error(f"Failed to get access token: {response['message']}")
            return None
    return access_token

def generate_random_id(length=10):
    """Generate a random ID."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def generate_aadhaar_otp(aadhaar_id, user_id=None):
    """
    Generate OTP for Aadhaar verification using Sandbox API.
    
    Args:
        aadhaar_id: The 12-digit Aadhaar number
        user_id: Optional user ID to include in logs
        
    Returns:
        Dictionary with results including success status and smart retry recommendation
    """
    logger.info(f"Generating OTP for Aadhaar: {aadhaar_id}")
    
    # Validate Aadhaar format (12 digits)
    if not aadhaar_id or len(aadhaar_id) != 12 or not aadhaar_id.isdigit():
        error_message = "Invalid Aadhaar number format. Please enter a 12-digit number."
        log_api_interaction(
            request_type='generate_otp', 
            aadhaar_id=aadhaar_id,
            request_payload={"aadhaar_id": aadhaar_id},
            success=False,
            error_message=error_message,
            user_id=user_id
        )
        
        return {
            "success": False,
            "message": error_message,
            "retry_recommended": False,  # Don't retry with invalid format
            "error_type": "INVALID_FORMAT"
        }
    
    # Get access token
    token = get_stored_access_token()
    if not token:
        error_message = "Failed to authenticate with Aadhaar API."
        log_api_interaction(
            request_type='generate_otp', 
            aadhaar_id=aadhaar_id,
            request_payload={"aadhaar_id": aadhaar_id},
            success=False,
            error_message=error_message,
            user_id=user_id
        )
        
        return {
            "success": False,
            "message": error_message,
            "retry_recommended": True,  # Auth errors are usually temporary
            "error_type": "AUTH_FAILURE"
        }
    
    # Request OTP
    try:
        logger.info(f"Sending OTP request to Sandbox API for Aadhaar: {aadhaar_id}")
        request_payload = {"aadhaar_id": aadhaar_id}
        response = request_aadhaar_otp(token, aadhaar_id)
        
        # Log API interaction
        log_api_interaction(
            request_type='generate_otp', 
            aadhaar_id=aadhaar_id,
            reference_id=response.get("reference_id"),
            request_payload=request_payload,
            response_payload=response,
            success=response.get("success", False),
            error_message=None if response.get("success", False) else response.get("message"),
            user_id=user_id
        )
        
        if response["success"]:
            logger.info(f"OTP request successful, reference_id: {response['reference_id']}")
            return {
                "success": True,
                "message": response["message"],
                "reference_id": response["reference_id"]
            }
        else:
            # Analyze specific error messages to provide smart recommendations
            error_msg = response.get("message", "Unknown error")
            logger.error(f"Failed to generate OTP for Aadhaar: {error_msg}")
            
            # Check for specific error types
            retry_recommended = True
            error_type = "UNKNOWN"
            
            # Common error patterns - adjust based on actual API responses
            if "invalid" in error_msg.lower() and "aadhaar" in error_msg.lower():
                error_type = "INVALID_AADHAAR"
                retry_recommended = False  # Invalid Aadhaar number, don't retry
            elif "limit" in error_msg.lower() or "rate" in error_msg.lower():
                error_type = "RATE_LIMIT"
                retry_recommended = True  # Rate limits are temporary, retry later
            elif "not found" in error_msg.lower():
                error_type = "AADHAAR_NOT_FOUND"
                retry_recommended = False  # Aadhaar not found, don't retry
            elif "service" in error_msg.lower() and ("unavailable" in error_msg.lower() or "down" in error_msg.lower()):
                error_type = "SERVICE_UNAVAILABLE"
                retry_recommended = True  # Service issues are temporary
            
            return {
                "success": False,
                "message": f"Failed to send OTP: {error_msg}",
                "error_type": error_type,
                "retry_recommended": retry_recommended
            }
    except Exception as e:
        # Log the full exception details for debugging
        error_message = f"An error occurred while requesting OTP: {str(e)}"
        logger.exception(f"Exception during OTP generation: {str(e)}")
        
        log_api_interaction(
            request_type='generate_otp', 
            aadhaar_id=aadhaar_id,
            request_payload={"aadhaar_id": aadhaar_id},
            success=False,
            error_message=error_message,
            user_id=user_id
        )
        
        return {
            "success": False,
            "message": error_message,
            "error_type": "EXCEPTION",
            "retry_recommended": True  # Most exceptions are temporary
        }

def verify_aadhaar_otp(reference_id, otp, user_id=None):
    """
    Verify OTP for Aadhaar verification using Sandbox API.
    
    Args:
        reference_id: The reference ID received from generate_aadhaar_otp
        otp: The OTP entered by the user
        user_id: Optional user ID to include in logs
        
    Returns:
        Dictionary with results including success status and smart retry recommendation
    """
    logger.info(f"Verifying OTP for reference_id: {reference_id}")
    
    # Get aadhaar_id from session if available
    aadhaar_id = session.get('aadhaar_id')
    logger.info(f"Retrieved aadhaar_id from session: {aadhaar_id}")
    
    # Validate OTP format (6 digits)
    if not otp or len(otp) != 6 or not otp.isdigit():
        error_message = "Invalid OTP format. Please enter a 6-digit number."
        log_api_interaction(
            request_type='verify_otp', 
            reference_id=reference_id,
            aadhaar_id=aadhaar_id,  # Include aadhaar_id from session
            request_payload={"reference_id": reference_id, "otp": otp},
            success=False,
            error_message=error_message,
            user_id=user_id
        )
        
        return {
            "success": False,
            "message": error_message,
            "retry_recommended": False,  # Don't retry with invalid format
            "error_type": "INVALID_FORMAT"
        }
    
    # Get access token
    token = get_stored_access_token()
    if not token:
        error_message = "Failed to authenticate with Aadhaar API."
        log_api_interaction(
            request_type='verify_otp', 
            reference_id=reference_id,
            aadhaar_id=aadhaar_id,  # Include aadhaar_id from session
            request_payload={"reference_id": reference_id, "otp": otp},
            success=False,
            error_message=error_message,
            user_id=user_id
        )
        
        return {
            "success": False,
            "message": error_message,
            "retry_recommended": True,  # Auth errors are usually temporary
            "error_type": "AUTH_FAILURE"
        }
    
    # Verify OTP
    try:
        logger.info(f"Sending OTP verification request to Sandbox API for reference_id: {reference_id}")
        request_payload = {"reference_id": reference_id, "otp": otp}
        response = sandbox_verify_otp(token, reference_id, otp)
        
        # Log API interaction
        log_api_interaction(
            request_type='verify_otp', 
            reference_id=reference_id,
            aadhaar_id=aadhaar_id,  # Include aadhaar_id from session
            request_payload=request_payload,
            response_payload=response,
            success=response.get("success", False),
            error_message=None if response.get("success", False) else response.get("message"),
            user_id=user_id
        )
        
        if response["success"]:
            logger.info("OTP verification successful")
            return {
                "success": True,
                "message": "OTP verified successfully.",
                "user_details": response["aadhaar_data"],
                "aadhaar_id": aadhaar_id  # Include aadhaar_id in the response
            }
        else:
            # Analyze specific error messages to provide smart recommendations
            error_msg = response.get("message", "Unknown error")
            logger.error(f"Failed to verify OTP: {error_msg}")
            
            # Check for specific error types
            retry_recommended = True
            should_regenerate_otp = False
            error_type = "UNKNOWN"
            
            # Common error patterns - adjust based on actual API responses
            if "invalid" in error_msg.lower() and "otp" in error_msg.lower():
                error_type = "INVALID_OTP"
                retry_recommended = True  # User can try again with correct OTP
                should_regenerate_otp = False
            elif "expired" in error_msg.lower():
                error_type = "OTP_EXPIRED"
                retry_recommended = True
                should_regenerate_otp = True  # Need to generate a new OTP
            elif "attempts" in error_msg.lower() or "limit" in error_msg.lower():
                error_type = "MAX_ATTEMPTS"
                retry_recommended = True
                should_regenerate_otp = True  # Need to generate a new OTP
            elif "not found" in error_msg.lower() or "invalid" in error_msg.lower() and "reference" in error_msg.lower():
                error_type = "INVALID_REFERENCE"
                retry_recommended = True
                should_regenerate_otp = True  # Reference ID might be invalid, generate new OTP
            
            return {
                "success": False,
                "message": f"Failed to verify OTP: {error_msg}",
                "error_type": error_type,
                "retry_recommended": retry_recommended,
                "should_regenerate_otp": should_regenerate_otp,
                "aadhaar_id": aadhaar_id  # Include aadhaar_id in the response
            }
    except Exception as e:
        # Log the full exception details for debugging
        error_message = f"An error occurred during verification: {str(e)}"
        logger.exception(f"Exception during OTP verification: {str(e)}")
        
        log_api_interaction(
            request_type='verify_otp', 
            reference_id=reference_id,
            aadhaar_id=aadhaar_id,  # Include aadhaar_id from session
            request_payload={"reference_id": reference_id, "otp": otp},
            success=False,
            error_message=error_message,
            user_id=user_id
        )
        
        return {
            "success": False,
            "message": error_message,
            "error_type": "EXCEPTION",
            "retry_recommended": True,  # Most exceptions are temporary
            "should_regenerate_otp": False,
            "aadhaar_id": aadhaar_id  # Include aadhaar_id in the response
        } 