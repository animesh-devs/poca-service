#!/usr/bin/env python3
"""
Docker Flow Test Script (Fixed Version)

This script tests the entire flow as documented in flow.txt using a Docker setup.
It tests the admin, patient, doctor, and hospital access controls.
"""

import requests
import json
import time
import logging
import sys
import os
import random
import string
import subprocess
from typing import Dict, List, Any, Optional, Tuple
import uuid
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("docker_flow_fixed_test.log")
    ]
)
logger = logging.getLogger("docker_flow_fixed_test")

# Generate a random suffix for email addresses
def generate_random_suffix():
    """Generate a random suffix for email addresses"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

RANDOM_SUFFIX = generate_random_suffix()

# API configuration
BASE_URL = "http://localhost:8000"
AUTH_URL = f"{BASE_URL}/api/v1/auth"
USERS_URL = f"{BASE_URL}/api/v1/users"
HOSPITALS_URL = f"{BASE_URL}/api/v1/hospitals"
DOCTORS_URL = f"{BASE_URL}/api/v1/doctors"
PATIENTS_URL = f"{BASE_URL}/api/v1/patients"
MAPPINGS_URL = f"{BASE_URL}/api/v1/mappings"
CHATS_URL = f"{BASE_URL}/api/v1/chats"
MESSAGES_URL = f"{BASE_URL}/api/v1/messages"
AI_URL = f"{BASE_URL}/api/v1/ai"
AI_ASSISTANT_URL = f"{BASE_URL}/api/v1/ai-assistant"
APPOINTMENTS_URL = f"{BASE_URL}/api/v1/appointments"

# Test data
DEFAULT_ADMIN_EMAIL = "admin@example.com"
DEFAULT_ADMIN_PASSWORD = "admin123"

# Test data for hospital
TEST_HOSPITAL_EMAIL = f"flow.hospital.{RANDOM_SUFFIX}@example.com"
TEST_HOSPITAL_PASSWORD = "password123"
TEST_HOSPITAL_NAME = f"Flow Test Hospital {RANDOM_SUFFIX}"
TEST_HOSPITAL_ADDRESS = "123 Hospital St"
TEST_HOSPITAL_CITY = "Medical City"
TEST_HOSPITAL_STATE = "Health State"
TEST_HOSPITAL_COUNTRY = "Healthcare Country"
TEST_HOSPITAL_CONTACT = "123-456-7890"
TEST_HOSPITAL_PIN_CODE = "12345"
TEST_HOSPITAL_SPECIALITIES = ["Cardiology", "Neurology", "Pediatrics"]

# Test data for doctor
TEST_DOCTOR_EMAIL = f"flow.doctor.{RANDOM_SUFFIX}@example.com"
TEST_DOCTOR_PASSWORD = "password123"
TEST_DOCTOR_NAME = f"Dr. Flow Test {RANDOM_SUFFIX}"
TEST_DOCTOR_DESIGNATION = "Senior Physician"
TEST_DOCTOR_EXPERIENCE = 10
TEST_DOCTOR_CONTACT = "123-456-7891"

# Test data for patient
TEST_PATIENT_EMAIL = f"flow.patient.{RANDOM_SUFFIX}@example.com"
TEST_PATIENT_PASSWORD = "password123"
TEST_PATIENT_NAME = f"Flow Test Patient {RANDOM_SUFFIX}"
TEST_PATIENT_DOB = "1990-01-01"
TEST_PATIENT_GENDER = "male"
TEST_PATIENT_CONTACT = "123-456-7892"

# Global variables to store IDs and tokens
admin_token = None
hospital_token = None
doctor_token = None
patient_token = None

hospital_id = None
doctor_id = None
patient_id = None
hospital_profile_id = None
doctor_profile_id = None
patient_profile_id = None
case_history_id = None
chat_id = None
ai_session_id = None
message_id = None

def make_request(method: str, url: str, token: Optional[str] = None, data: Optional[Dict] = None,
                 files: Optional[Dict] = None, expected_status: int = 200) -> Tuple[Dict, bool]:
    """
    Make an HTTP request with proper error handling

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        url: API endpoint URL
        token: Authentication token
        data: Request payload
        files: Files to upload
        expected_status: Expected HTTP status code

    Returns:
        Tuple of (response_data, success_flag)
    """
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            if files:
                response = requests.post(url, headers=headers, data=data, files=files)
            else:
                response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            logger.error(f"Unsupported method: {method}")
            return {}, False

        if response.status_code == expected_status:
            try:
                if response.text:
                    response_data = response.json()
                else:
                    response_data = {}
                return response_data, True
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON response: {response.text}")
                return {}, False
        else:
            logger.error(f"Request failed: {url}, Status: {response.status_code}, Response: {response.text}")
            return {}, False
    except Exception as e:
        logger.error(f"Request error: {url}, Error: {str(e)}")
        return {}, False

def login(email: str, password: str) -> Optional[str]:
    """Login and get access token"""
    data = {"username": email, "password": password}
    response = requests.post(
        f"{AUTH_URL}/login",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if response.status_code == 200:
        logger.info(f"Login successful for {email}")
        return response.json().get("access_token")
    else:
        logger.error(f"Login failed for {email}: {response.text}")
        return None

def check_docker_running() -> bool:
    """Check if Docker is running"""
    logger.info("Checking if Docker is running...")
    try:
        result = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        if result.returncode == 0:
            logger.info("Docker is running")
            return True
        else:
            logger.error("Docker is not running")
            return False
    except Exception as e:
        logger.error(f"Error checking Docker: {str(e)}")
        return False

def check_server_health() -> bool:
    """Check if the server is up and running"""
    logger.info("Checking server health...")

    try:
        # Try the health endpoint first
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            logger.info("Server is up and running (health endpoint)")
            return True
    except Exception as e:
        logger.warning(f"Health endpoint check failed: {str(e)}")

    # Try the auth endpoint
    try:
        response = requests.post(
            f"{AUTH_URL}/login",
            data={"username": DEFAULT_ADMIN_EMAIL, "password": DEFAULT_ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if response.status_code in [200, 401, 422]:  # Any of these codes means the server is running
            logger.info("Server is up and running (auth endpoint)")
            return True
    except Exception as e:
        logger.warning(f"Auth endpoint check failed: {str(e)}")

    # If we get here, try a simple GET request to the base URL
    try:
        response = requests.get(BASE_URL)
        logger.info("Server is up and running (base URL)")
        return True
    except Exception as e:
        logger.error(f"Server health check failed: {str(e)}")
        return False

# Step 1: Hospital signup/login
def test_hospital_signup_login():
    """Test hospital signup and login (Step 1)"""
    global hospital_token, hospital_id, hospital_profile_id

    # Hospital signup
    hospital_data = {
        "email": TEST_HOSPITAL_EMAIL,
        "password": TEST_HOSPITAL_PASSWORD,
        "name": TEST_HOSPITAL_NAME,
        "address": TEST_HOSPITAL_ADDRESS,
        "city": TEST_HOSPITAL_CITY,
        "state": TEST_HOSPITAL_STATE,
        "country": TEST_HOSPITAL_COUNTRY,
        "contact": TEST_HOSPITAL_CONTACT,
        "pin_code": TEST_HOSPITAL_PIN_CODE,
        "specialities": TEST_HOSPITAL_SPECIALITIES
    }

    response, success = make_request("POST", f"{AUTH_URL}/hospital-signup", data=hospital_data)

    if success:
        hospital_token = response.get("access_token")
        hospital_id = response.get("user_id")
        hospital_profile_id = response.get("profile_id")
        logger.info(f"Hospital signup successful")
        logger.info(f"Hospital ID: {hospital_id}")
        logger.info(f"Hospital Profile ID: {hospital_profile_id}")
        return True
    else:
        logger.error("Hospital signup failed")
        return False

# Step 2: Doctor signup/login
def test_doctor_signup_login():
    """Test doctor signup and login (Step 2)"""
    global doctor_token, doctor_id, doctor_profile_id

    # Doctor signup
    doctor_data = {
        "email": TEST_DOCTOR_EMAIL,
        "password": TEST_DOCTOR_PASSWORD,
        "name": TEST_DOCTOR_NAME,
        "designation": TEST_DOCTOR_DESIGNATION,
        "experience": TEST_DOCTOR_EXPERIENCE,
        "contact": TEST_DOCTOR_CONTACT
    }

    response, success = make_request("POST", f"{AUTH_URL}/doctor-signup", data=doctor_data)

    if success:
        doctor_token = response.get("access_token")
        doctor_id = response.get("user_id")
        doctor_profile_id = response.get("profile_id")
        logger.info(f"Doctor signup successful")
        logger.info(f"Doctor ID: {doctor_id}")
        logger.info(f"Doctor Profile ID: {doctor_profile_id}")
        return True
    else:
        logger.error("Doctor signup failed")
        return False

# Step 3: Patient signup/login
def test_patient_signup_login():
    """Test patient signup and login (Step 3)"""
    global patient_token, patient_id, patient_profile_id

    # Patient signup
    patient_data = {
        "email": TEST_PATIENT_EMAIL,
        "password": TEST_PATIENT_PASSWORD,
        "name": TEST_PATIENT_NAME,
        "dob": TEST_PATIENT_DOB,
        "gender": TEST_PATIENT_GENDER,
        "contact": TEST_PATIENT_CONTACT
    }

    response, success = make_request("POST", f"{AUTH_URL}/patient-signup", data=patient_data)

    if success:
        patient_token = response.get("access_token")
        patient_id = response.get("user_id")
        patient_profile_id = response.get("profile_id")
        logger.info(f"Patient signup successful")
        logger.info(f"Patient ID: {patient_id}")
        logger.info(f"Patient Profile ID: {patient_profile_id}")

        # Create user-patient self relation
        relation_data = {
            "user_id": patient_id,
            "patient_id": patient_id,
            "relation": "self"
        }

        relation_response, relation_success = make_request(
            "POST",
            f"{MAPPINGS_URL}/user-patient",
            token=patient_token,
            data=relation_data
        )

        if relation_success:
            logger.info("Created user-patient self relation")
        else:
            logger.warning("Failed to create user-patient self relation, but test continues")

        return True
    else:
        logger.error("Patient signup failed")
        return False

# Step 4: Admin login
def test_admin_login():
    """Test admin login (Step 4)"""
    global admin_token

    admin_token = login(DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD)

    if admin_token:
        logger.info("Admin login successful")
        return True
    else:
        logger.error("Admin login failed")
        return False

# Step 5: Admin maps hospital to doctor
def test_admin_maps_hospital_to_doctor():
    """Test admin maps hospital to doctor (Step 5)"""
    global hospital_profile_id, doctor_profile_id

    if not admin_token or not hospital_id or not doctor_id:
        logger.error("Missing required tokens or IDs for hospital-doctor mapping")
        return False

    # Get user info to get profile IDs if not available
    if not hospital_profile_id:
        response, success = make_request(
            "GET",
            f"{USERS_URL}/{hospital_id}",
            token=admin_token
        )

        if success and response.get("profile_id"):
            hospital_profile_id = response.get("profile_id")
            logger.info(f"Got hospital profile ID: {hospital_profile_id}")
        else:
            logger.error("Failed to get hospital profile ID")
            return False

    if not doctor_profile_id:
        response, success = make_request(
            "GET",
            f"{USERS_URL}/{doctor_id}",
            token=admin_token
        )

        if success and response.get("profile_id"):
            doctor_profile_id = response.get("profile_id")
            logger.info(f"Got doctor profile ID: {doctor_profile_id}")
        else:
            logger.error("Failed to get doctor profile ID")
            return False

    mapping_data = {
        "hospital_id": hospital_profile_id,
        "doctor_id": doctor_profile_id
    }

    response, success = make_request(
        "POST",
        f"{MAPPINGS_URL}/hospital-doctor",
        token=admin_token,
        data=mapping_data
    )

    if success:
        logger.info(f"Mapped hospital {hospital_id} to doctor {doctor_id}")
        return True
    else:
        logger.error("Failed to map hospital to doctor")
        return False

# Step 6: Admin maps hospital to patient
def test_admin_maps_hospital_to_patient():
    """Test admin maps hospital to patient (Step 6)"""
    global hospital_profile_id, patient_profile_id

    if not admin_token or not hospital_id or not patient_id:
        logger.error("Missing required tokens or IDs for hospital-patient mapping")
        return False

    # Get user info to get profile IDs if not available
    if not hospital_profile_id:
        response, success = make_request(
            "GET",
            f"{USERS_URL}/{hospital_id}",
            token=admin_token
        )

        if success and response.get("profile_id"):
            hospital_profile_id = response.get("profile_id")
            logger.info(f"Got hospital profile ID: {hospital_profile_id}")
        else:
            logger.error("Failed to get hospital profile ID")
            return False

    if not patient_profile_id:
        response, success = make_request(
            "GET",
            f"{USERS_URL}/{patient_id}",
            token=admin_token
        )

        if success and response.get("profile_id"):
            patient_profile_id = response.get("profile_id")
            logger.info(f"Got patient profile ID: {patient_profile_id}")
        else:
            logger.error("Failed to get patient profile ID")
            return False

    mapping_data = {
        "hospital_id": hospital_profile_id,
        "patient_id": patient_profile_id
    }

    response, success = make_request(
        "POST",
        f"{MAPPINGS_URL}/hospital-patient",
        token=admin_token,
        data=mapping_data
    )

    if success:
        logger.info(f"Mapped hospital {hospital_id} to patient {patient_id}")
        return True
    else:
        logger.error("Failed to map hospital to patient")
        return False

# Step 7: Admin maps doctor to patient
def test_admin_maps_doctor_to_patient():
    """Test admin maps doctor to patient (Step 7)"""
    global doctor_profile_id, patient_profile_id

    if not admin_token or not doctor_id or not patient_id:
        logger.error("Missing required tokens or IDs for doctor-patient mapping")
        return False

    # Get user info to get profile IDs if not available
    if not doctor_profile_id:
        response, success = make_request(
            "GET",
            f"{USERS_URL}/{doctor_id}",
            token=admin_token
        )

        if success and response.get("profile_id"):
            doctor_profile_id = response.get("profile_id")
            logger.info(f"Got doctor profile ID: {doctor_profile_id}")
        else:
            logger.error("Failed to get doctor profile ID")
            return False

    if not patient_profile_id:
        response, success = make_request(
            "GET",
            f"{USERS_URL}/{patient_id}",
            token=admin_token
        )

        if success and response.get("profile_id"):
            patient_profile_id = response.get("profile_id")
            logger.info(f"Got patient profile ID: {patient_profile_id}")
        else:
            logger.error("Failed to get patient profile ID")
            return False

    mapping_data = {
        "doctor_id": doctor_profile_id,
        "patient_id": patient_profile_id,
        "relation": "doctor"
    }

    response, success = make_request(
        "POST",
        f"{MAPPINGS_URL}/doctor-patient",
        token=admin_token,
        data=mapping_data
    )

    if success:
        logger.info(f"Mapped doctor {doctor_id} to patient {patient_id}")
        return True
    else:
        logger.error("Failed to map doctor to patient")
        return False

def main():
    """Main function to run all tests"""
    # Check if Docker is running
    if not check_docker_running():
        logger.error("Docker is not running. Please start Docker and try again.")
        return

    # Check if server is up
    if not check_server_health():
        logger.error("Server is not running. Please start the server and try again.")
        return

    # Run all tests
    tests = [
        # Step 1-4: Setup
        ("Hospital signup/login", test_hospital_signup_login),
        ("Doctor signup/login", test_doctor_signup_login),
        ("Patient signup/login", test_patient_signup_login),
        ("Admin login", test_admin_login),

        # Step 5-7: Admin mappings
        ("Admin maps hospital to doctor", test_admin_maps_hospital_to_doctor),
        ("Admin maps hospital to patient", test_admin_maps_hospital_to_patient),
        ("Admin maps doctor to patient", test_admin_maps_doctor_to_patient),
    ]

    # Run each test
    results = []
    for test_name, test_func in tests:
        logger.info(f"Running test: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                logger.info(f"Test '{test_name}' passed")
            else:
                logger.error(f"Test '{test_name}' failed")
        except Exception as e:
            logger.error(f"Test '{test_name}' raised an exception: {str(e)}")
            results.append((test_name, False))

    # Print summary
    logger.info("\n--- Test Results Summary ---")
    passed = 0
    failed = 0
    for test_name, success in results:
        status = "PASSED" if success else "FAILED"
        logger.info(f"{test_name}: {status}")
        if success:
            passed += 1
        else:
            failed += 1

    logger.info(f"\nTotal: {len(results)}, Passed: {passed}, Failed: {failed}")

    if failed == 0:
        logger.info("All tests passed!")
    else:
        logger.warning(f"{failed} tests failed.")

if __name__ == "__main__":
    main()
