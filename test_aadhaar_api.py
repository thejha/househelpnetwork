"""
Test script for Aadhaar API functionality.
Run this script to test the API connection and OTP generation/verification.
"""
import logging
import time
import sys
from sandbox_api import get_access_token, request_aadhaar_otp, verify_aadhaar_otp

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_aadhaar_api")

def test_aadhaar_api():
    # Test authentication
    logger.info("Testing Aadhaar API authentication...")
    auth_response = get_access_token()
    if auth_response["success"]:
        logger.info("✓ Authentication successful")
        access_token = auth_response["access_token"]
    else:
        logger.error(f"✗ Authentication failed: {auth_response['message']}")
        return False
    
    # Test OTP generation
    logger.info("Testing OTP generation...")
    test_aadhaar = input("Enter a valid Aadhaar number (12 digits): ")
    
    otp_response = request_aadhaar_otp(access_token, test_aadhaar)
    if otp_response["success"]:
        logger.info(f"✓ OTP generation successful. Reference ID: {otp_response['reference_id']}")
        reference_id = otp_response["reference_id"]
    else:
        logger.error(f"✗ OTP generation failed: {otp_response.get('message', 'Unknown error')}")
        return False
    
    # Test OTP verification
    logger.info("Wait for the OTP to be received on the registered mobile number...")
    otp = input("Enter the OTP you received: ")
    
    verify_response = verify_aadhaar_otp(access_token, reference_id, otp)
    if verify_response["success"]:
        logger.info("✓ OTP verification successful")
        logger.info("User details received:")
        user_details = verify_response["aadhaar_data"]
        logger.info(f"  - Name: {user_details.get('name', 'N/A')}")
        logger.info(f"  - Gender: {user_details.get('gender', 'N/A')}")
        logger.info(f"  - DOB: {user_details.get('date_of_birth', 'N/A')}")
        return True
    else:
        logger.error(f"✗ OTP verification failed: {verify_response.get('message', 'Unknown error')}")
        return False

if __name__ == "__main__":
    logger.info("Starting Aadhaar API test...")
    success = test_aadhaar_api()
    if success:
        logger.info("All tests passed successfully!")
    else:
        logger.error("Some tests failed. See above logs for details.") 