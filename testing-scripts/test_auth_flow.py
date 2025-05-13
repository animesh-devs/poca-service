#!/usr/bin/env python3
"""
Test Authentication Flow

This script tests the authentication flow of the POCA service by creating users and logging in.
"""

import sys
import logging
import time
import requests
import random
import string
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# API URLs
BASE_URL = "http://localhost:8002"
AUTH_URL = f"{BASE_URL}/api/v1/auth"

# Default admin credentials
DEFAULT_ADMIN_EMAIL = "admin@example.com"
DEFAULT_ADMIN_PASSWORD = "admin123"

# Test data for this script
def generate_random_suffix():
    """Generate a random suffix for email addresses"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

RANDOM_SUFFIX = generate_random_suffix()

TEST_HOSPITAL_NAME = "Auth Test Hospital"
TEST_HOSPITAL_EMAIL = f"auth.test.hospital.{RANDOM_SUFFIX}@example.com"
TEST_HOSPITAL_PASSWORD = "hospital123"

TEST_DOCTOR_NAME = "Dr. Auth Test"
TEST_DOCTOR_EMAIL = f"auth.test.doctor.{RANDOM_SUFFIX}@example.com"
TEST_DOCTOR_PASSWORD = "doctor123"
TEST_DOCTOR_SPECIALIZATION = "General Medicine"

TEST_PATIENT_NAME = "Auth Test Patient"
TEST_PATIENT_EMAIL = f"auth.test.patient.{RANDOM_SUFFIX}@example.com"
TEST_PATIENT_PASSWORD = "patient123"
TEST_PATIENT_AGE = 30
TEST_PATIENT_GENDER = "male"

def check_server_health() -> bool:
    """Check if the server is up and running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            logging.info("Server is up and running (health endpoint)")
            return True
        else:
            logging.error(f"Server health check failed with status code: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"Error checking server health: {str(e)}")
        return False

def get_auth_token(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Get authentication token"""
    logging.info(f"Getting authentication token for {email}...")
    
    try:
        response = requests.post(
            f"{AUTH_URL}/login",
            data={
                "username": email,
                "password": password
            }
        )
        
        if response.status_code == 200:
            token_data = response.json()
            logging.info(f"Got authentication token for user ID: {token_data.get('user_id')}")
            return token_data
        else:
            logging.error(f"Failed to get authentication token: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting authentication token: {str(e)}")
        return None

def create_hospital() -> Optional[Dict[str, Any]]:
    """Create a hospital using direct signup"""
    logging.info(f"Creating hospital: {TEST_HOSPITAL_NAME}...")
    
    try:
        hospital_data = {
            "name": TEST_HOSPITAL_NAME,
            "address": f"{TEST_HOSPITAL_NAME} Address, Main Street",
            "city": "Test City",
            "state": "Test State",
            "country": "Test Country",
            "contact": "1234567890",
            "pin_code": "12345",
            "email": TEST_HOSPITAL_EMAIL,
            "password": TEST_HOSPITAL_PASSWORD,
            "specialities": ["Cardiology", "Neurology", "Pediatrics"],
            "website": f"https://{TEST_HOSPITAL_NAME.lower().replace(' ', '')}.example.com"
        }

        response = requests.post(
            f"{AUTH_URL}/hospital-signup",
            json=hospital_data
        )

        if response.status_code in [200, 201]:
            result = response.json()
            hospital_data["id"] = result.get("user_id")
            hospital_data["user_id"] = result.get("user_id")
            logging.info(f"Created hospital: {TEST_HOSPITAL_NAME} with ID: {hospital_data['id']}")
            
            # Print the full response for debugging
            logging.info(f"Hospital signup response: {result}")
            
            return hospital_data
        else:
            logging.error(f"Failed to create hospital: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error creating hospital: {str(e)}")
        return None

def create_doctor() -> Optional[Dict[str, Any]]:
    """Create a doctor using direct signup"""
    logging.info(f"Creating doctor: {TEST_DOCTOR_NAME}...")
    
    try:
        doctor_data = {
            "name": TEST_DOCTOR_NAME,
            "email": TEST_DOCTOR_EMAIL,
            "password": TEST_DOCTOR_PASSWORD,
            "photo": f"https://example.com/{TEST_DOCTOR_NAME.lower().replace(' ', '')}.jpg",
            "designation": f"Senior {TEST_DOCTOR_SPECIALIZATION}",
            "experience": 10,
            "details": f"MD, {TEST_DOCTOR_SPECIALIZATION}, Medical University",
            "contact": "1234567890",
            "address": "123 Doctor St"
        }

        response = requests.post(
            f"{AUTH_URL}/doctor-signup",
            json=doctor_data
        )

        if response.status_code in [200, 201]:
            result = response.json()
            doctor_data["id"] = result.get("user_id")
            doctor_data["user_id"] = result.get("user_id")
            logging.info(f"Created doctor: {TEST_DOCTOR_NAME} with ID: {doctor_data['id']}")
            
            # Print the full response for debugging
            logging.info(f"Doctor signup response: {result}")
            
            return doctor_data
        else:
            logging.error(f"Failed to create doctor: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error creating doctor: {str(e)}")
        return None

def create_patient() -> Optional[Dict[str, Any]]:
    """Create a patient using direct signup"""
    logging.info(f"Creating patient: {TEST_PATIENT_NAME}...")
    
    try:
        patient_data = {
            "name": TEST_PATIENT_NAME,
            "email": TEST_PATIENT_EMAIL,
            "password": TEST_PATIENT_PASSWORD,
            "age": TEST_PATIENT_AGE,
            "gender": TEST_PATIENT_GENDER,
            "blood_group": "O+",
            "height": 170,
            "weight": 70,
            "allergies": ["None"],
            "medications": ["None"],
            "conditions": ["None"],
            "emergency_contact_name": "Emergency Contact",
            "emergency_contact_number": "9876543210",
            "contact": "1234567890",
            "address": "123 Patient St"
        }

        response = requests.post(
            f"{AUTH_URL}/patient-signup",
            json=patient_data
        )

        if response.status_code in [200, 201]:
            result = response.json()
            patient_data["id"] = result.get("user_id")
            patient_data["user_id"] = result.get("user_id")
            logging.info(f"Created patient: {TEST_PATIENT_NAME} with ID: {patient_data['id']}")
            
            # Print the full response for debugging
            logging.info(f"Patient signup response: {result}")
            
            return patient_data
        else:
            logging.error(f"Failed to create patient: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error creating patient: {str(e)}")
        return None

def test_authentication_flow() -> bool:
    """Test authentication flow"""
    logging.info("Testing authentication flow...")
    
    # Admin login
    admin_token_data = get_auth_token(DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD)
    if not admin_token_data:
        logging.error("Admin login failed")
        return False
    
    logging.info("Admin login successful")
    
    # Create test hospital, doctor, and patient
    hospital_data = create_hospital()
    if not hospital_data:
        logging.error("Failed to create test hospital")
        return False
    
    # Hospital login
    hospital_token_data = get_auth_token(TEST_HOSPITAL_EMAIL, TEST_HOSPITAL_PASSWORD)
    if not hospital_token_data:
        logging.error("Hospital login failed")
        return False
    
    logging.info("Hospital login successful")
    
    # Create doctor
    doctor_data = create_doctor()
    if not doctor_data:
        logging.error("Failed to create test doctor")
        return False
    
    # Doctor login
    doctor_token_data = get_auth_token(TEST_DOCTOR_EMAIL, TEST_DOCTOR_PASSWORD)
    if not doctor_token_data:
        logging.error("Doctor login failed")
        return False
    
    logging.info("Doctor login successful")
    
    # Create patient
    patient_data = create_patient()
    if not patient_data:
        logging.error("Failed to create test patient")
        return False
    
    # Patient login
    patient_token_data = get_auth_token(TEST_PATIENT_EMAIL, TEST_PATIENT_PASSWORD)
    if not patient_token_data:
        logging.error("Patient login failed")
        return False
    
    logging.info("Patient login successful")
    
    logging.info("Authentication flow test completed successfully")
    return True

def main():
    """Main test function"""
    print("Starting authentication flow test for POCA service...")
    print("This may take a few minutes...")
    
    # Check if the server is up
    if not check_server_health():
        logging.error("Server is not running. Please start the server and try again.")
        return
    
    # Test authentication flow
    if test_authentication_flow():
        print("Authentication flow test completed successfully!")
    else:
        print("Authentication flow test failed.")

if __name__ == "__main__":
    main()
