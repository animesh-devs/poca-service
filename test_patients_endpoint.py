#!/usr/bin/env python3
"""
Test Patients Endpoint
"""

import sys
import logging
import requests
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
USERS_URL = f"{BASE_URL}/api/v1/users"
PATIENTS_URL = f"{BASE_URL}/api/v1/patients"

# Test credentials
DEFAULT_ADMIN_EMAIL = "admin@example.com"
DEFAULT_ADMIN_PASSWORD = "admin123"

# Generate a random suffix for test emails
import random
import string
RANDOM_SUFFIX = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

TEST_DOCTOR_NAME = "Dr. API Test"
TEST_DOCTOR_EMAIL = f"api.test.doctor.{RANDOM_SUFFIX}@example.com"
TEST_DOCTOR_PASSWORD = "doctor123"

TEST_PATIENT_NAME = "API Test Patient"
TEST_PATIENT_EMAIL = f"api.test.patient.{RANDOM_SUFFIX}@example.com"
TEST_PATIENT_PASSWORD = "patient123"

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

def create_doctor() -> Optional[Dict[str, Any]]:
    """Create a doctor using direct signup"""
    logging.info(f"Creating doctor: {TEST_DOCTOR_NAME}...")

    try:
        doctor_data = {
            "name": TEST_DOCTOR_NAME,
            "email": TEST_DOCTOR_EMAIL,
            "password": TEST_DOCTOR_PASSWORD,
            "photo": f"https://example.com/{TEST_DOCTOR_NAME.lower().replace(' ', '')}.jpg",
            "designation": "Senior General Medicine",
            "experience": 10,
            "details": "MD, General Medicine, Medical University",
            "contact": "1234567890",
            "address": "123 Doctor St"
        }

        response = requests.post(
            f"{AUTH_URL}/doctor-signup",
            json=doctor_data
        )

        if response.status_code in [200, 201]:
            result = response.json()
            doctor_data["id"] = result.get("user_id")  # Use user_id as the ID
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
            "age": 30,
            "gender": "male",
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
            patient_data["id"] = result.get("user_id")  # Use user_id as the ID
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

def get_patient_profile_id(token: str, patient_user_id: str) -> Optional[str]:
    """Get patient profile ID from user ID"""
    logging.info(f"Getting patient profile ID for user ID: {patient_user_id}...")

    try:
        response = requests.get(
            f"{USERS_URL}/{patient_user_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            user = response.json()
            profile_id = user.get("profile_id")
            if profile_id:
                logging.info(f"Got patient profile ID: {profile_id}")
                return profile_id
            else:
                logging.error(f"User {patient_user_id} has no profile ID")
                return None
        else:
            logging.error(f"Failed to get user: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting patient profile ID: {str(e)}")
        return None

def get_patient_by_id(token: str, patient_id: str) -> Optional[Dict[str, Any]]:
    """Get patient by ID"""
    logging.info(f"Getting patient with ID: {patient_id}...")

    try:
        response = requests.get(
            f"{PATIENTS_URL}/{patient_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            patient = response.json()
            logging.info(f"Got patient: {patient.get('name')}")
            return patient
        else:
            logging.error(f"Failed to get patient: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting patient: {str(e)}")
        return None

def main():
    """Main function"""
    # Get admin token
    admin_token_data = get_auth_token(DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD)
    if not admin_token_data:
        logging.error("Failed to get admin token. Aborting.")
        return

    admin_token = admin_token_data["access_token"]

    # Create a doctor
    doctor_data = create_doctor()
    if not doctor_data:
        logging.error("Failed to create doctor. Aborting.")
        return

    # Get doctor token
    doctor_token_data = get_auth_token(TEST_DOCTOR_EMAIL, TEST_DOCTOR_PASSWORD)
    if not doctor_token_data:
        logging.error("Failed to get doctor token. Aborting.")
        return

    doctor_token = doctor_token_data["access_token"]

    # Create a patient
    patient_data = create_patient()
    if not patient_data:
        logging.error("Failed to create patient. Aborting.")
        return

    # Get patient token
    patient_token_data = get_auth_token(TEST_PATIENT_EMAIL, TEST_PATIENT_PASSWORD)
    if not patient_token_data:
        logging.error("Failed to get patient token. Aborting.")
        return

    patient_token = patient_token_data["access_token"]
    patient_user_id = patient_data["user_id"]

    # Get patient profile ID
    patient_profile_id = get_patient_profile_id(admin_token, patient_user_id)
    if not patient_profile_id:
        logging.error("Failed to get patient profile ID. Aborting.")
        return

    # Test getting patient by user_id with different tokens
    logging.info("Testing GET /api/v1/patients/{patient_id} with user_id...")
    
    # Admin access with user_id
    admin_patient = get_patient_by_id(admin_token, patient_user_id)
    if admin_patient:
        logging.info("Admin can get patient by user_id: SUCCESS")
    else:
        logging.error("Admin can get patient by user_id: FAILED")

    # Patient access to their own data with user_id
    patient_self = get_patient_by_id(patient_token, patient_user_id)
    if patient_self:
        logging.info("Patient can get their own profile by user_id: SUCCESS")
    else:
        logging.error("Patient can get their own profile by user_id: FAILED")

    # Doctor access to patient data with user_id
    doctor_patient = get_patient_by_id(doctor_token, patient_user_id)
    if doctor_patient:
        logging.info("Doctor can get patient by user_id: SUCCESS")
    else:
        logging.error("Doctor can get patient by user_id: FAILED")

    # Test getting patient by profile_id with different tokens
    logging.info("Testing GET /api/v1/patients/{patient_id} with profile_id...")
    
    # Admin access with profile_id
    admin_patient = get_patient_by_id(admin_token, patient_profile_id)
    if admin_patient:
        logging.info("Admin can get patient by profile_id: SUCCESS")
    else:
        logging.error("Admin can get patient by profile_id: FAILED")

    # Patient access to their own data with profile_id
    patient_self = get_patient_by_id(patient_token, patient_profile_id)
    if patient_self:
        logging.info("Patient can get their own profile by profile_id: SUCCESS")
    else:
        logging.error("Patient can get their own profile by profile_id: FAILED")

    # Doctor access to patient data with profile_id
    doctor_patient = get_patient_by_id(doctor_token, patient_profile_id)
    if doctor_patient:
        logging.info("Doctor can get patient by profile_id: SUCCESS")
    else:
        logging.error("Doctor can get patient by profile_id: FAILED")

if __name__ == "__main__":
    main()
