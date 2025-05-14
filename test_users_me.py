#!/usr/bin/env python3
"""
Test Users Me Endpoint
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

# Test credentials
DEFAULT_ADMIN_EMAIL = "admin@example.com"
DEFAULT_ADMIN_PASSWORD = "admin123"

# Generate a random suffix for test emails
import random
import string
RANDOM_SUFFIX = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

TEST_DOCTOR_EMAIL = f"api.test.doctor.{RANDOM_SUFFIX}@example.com"
TEST_DOCTOR_PASSWORD = "doctor123"

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
    TEST_DOCTOR_NAME = "Dr. API Test"
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

def get_current_user_profile(token: str) -> Optional[Dict[str, Any]]:
    """Get current user profile"""
    logging.info("Getting current user profile...")

    try:
        response = requests.get(
            f"{USERS_URL}/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            user = response.json()
            logging.info(f"Got current user profile: {user.get('name')}")
            return user
        else:
            logging.error(f"Failed to get current user profile: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting current user profile: {str(e)}")
        return None

def main():
    """Main function"""
    # Get admin token
    admin_token_data = get_auth_token(DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD)
    if not admin_token_data:
        logging.error("Failed to get admin token. Aborting.")
        return

    admin_token = admin_token_data["access_token"]

    # Test admin user profile
    admin_profile = get_current_user_profile(admin_token)
    if admin_profile:
        logging.info("Admin user profile test passed")
    else:
        logging.error("Admin user profile test failed")

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

    # Test doctor user profile
    doctor_profile = get_current_user_profile(doctor_token)
    if doctor_profile:
        logging.info("Doctor user profile test passed")
    else:
        logging.error("Doctor user profile test failed")

if __name__ == "__main__":
    main()
