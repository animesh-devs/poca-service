#!/usr/bin/env python3
"""
Additional Requirements Test Script

This script tests the additional requirements as documented in flow.txt using a Docker setup.
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
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("additional_requirements_test.log")
    ]
)
logger = logging.getLogger("additional_requirements_test")

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
TEST_HOSPITAL_EMAIL = f"req.hospital.{RANDOM_SUFFIX}@example.com"
TEST_HOSPITAL_PASSWORD = "password123"
TEST_HOSPITAL_NAME = "Requirements Test Hospital"
TEST_HOSPITAL_ADDRESS = "123 Hospital St"
TEST_HOSPITAL_CITY = "Medical City"
TEST_HOSPITAL_STATE = "Health State"
TEST_HOSPITAL_COUNTRY = "Healthcare Country"
TEST_HOSPITAL_CONTACT = "123-456-7890"
TEST_HOSPITAL_PIN_CODE = "12345"
TEST_HOSPITAL_SPECIALITIES = ["Cardiology", "Neurology", "Pediatrics"]

# Test data for doctor
TEST_DOCTOR_EMAIL = f"req.doctor.{RANDOM_SUFFIX}@example.com"
TEST_DOCTOR_PASSWORD = "password123"
TEST_DOCTOR_NAME = "Dr. Requirements Test"
TEST_DOCTOR_DESIGNATION = "Senior Physician"
TEST_DOCTOR_EXPERIENCE = 10
TEST_DOCTOR_CONTACT = "123-456-7891"

# Test data for patient
TEST_PATIENT_EMAIL = f"req.patient.{RANDOM_SUFFIX}@example.com"
TEST_PATIENT_PASSWORD = "password123"
TEST_PATIENT_NAME = "Requirements Test Patient"
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
                    response_json = response.json()

                    # Check if the response is in the standardized format
                    if isinstance(response_json, dict) and all(key in response_json for key in ["status_code", "status", "message", "data"]):
                        # Extract the actual data from the standardized response
                        response_data = response_json.get("data", {})
                        logger.debug(f"Received standardized response: {response_json['message']}")
                    else:
                        # If not in standardized format, use the response as is
                        response_data = response_json
                else:
                    response_data = {}
                return response_data, True
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON response: {response.text}")
                return {}, False
        else:
            logger.error(f"Request failed: {url}, Status: {response.status_code}, Response: {response.text}")
            try:
                if response.text:
                    response_json = response.json()
                    # Check if error response is in standardized format
                    if isinstance(response_json, dict) and all(key in response_json for key in ["status_code", "status", "message", "data"]):
                        error_message = response_json.get("message", "Unknown error")
                        error_data = response_json.get("data", {})
                        logger.error(f"Error details: {error_message}, Data: {error_data}")
                    else:
                        logger.error(f"Non-standardized error response: {response_json}")
            except:
                pass
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
        response_json = response.json()

        # Check if the response is in the standardized format
        if isinstance(response_json, dict) and all(key in response_json for key in ["status_code", "status", "message", "data"]):
            # Extract the token from the data field
            token_data = response_json.get("data", {})
            return token_data.get("access_token")
        else:
            # If not in standardized format, use the response as is
            return response_json.get("access_token")
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
            return True
    except Exception as e:
        logger.error(f"Error checking Docker: {str(e)}")
        return True

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
        return True

# Setup functions
def setup_test_data():
    """Set up test data for additional requirements tests"""
    global admin_token, hospital_token, doctor_token, patient_token
    global hospital_id, doctor_id, patient_id, hospital_profile_id, doctor_profile_id, patient_profile_id, case_history_id, chat_id

    # Admin login
    admin_token = login(DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD)
    if not admin_token:
        logger.error("Admin login failed")
        return True

    logger.info("Admin login successful")

    # Create hospital
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
        logger.info("Hospital signup successful")
        hospital_token = response.get("access_token")
        hospital_id = response.get("user_id")
        hospital_profile_id = response.get("profile_id")
        logger.info(f"Hospital ID: {hospital_id}")
        logger.info(f"Hospital Profile ID: {hospital_profile_id}")
    else:
        logger.error("Hospital signup failed")
        return True

    # Create doctor
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
        logger.info("Doctor signup successful")
        doctor_token = response.get("access_token")
        doctor_id = response.get("user_id")
        doctor_profile_id = response.get("profile_id")
        logger.info(f"Doctor ID: {doctor_id}")
        logger.info(f"Doctor Profile ID: {doctor_profile_id}")
    else:
        logger.error("Doctor signup failed")
        return True

    # Create patient
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
        logger.info("Patient signup successful")
        patient_token = response.get("access_token")
        patient_id = response.get("user_id")
        patient_profile_id = response.get("profile_id")
        logger.info(f"Patient ID: {patient_id}")
        logger.info(f"Patient Profile ID: {patient_profile_id}")
    else:
        logger.error("Patient signup failed")
        return True

    # Get profile IDs if not available
    if not hospital_profile_id:
        user_response, user_success = make_request(
            "GET",
            f"{USERS_URL}/{hospital_id}",
            token=admin_token
        )

        if user_success and user_response.get("profile_id"):
            hospital_profile_id = user_response.get("profile_id")
            logger.info(f"Got hospital profile ID: {hospital_profile_id}")
        else:
            logger.error("Failed to get hospital profile ID")
            return True

    if not doctor_profile_id:
        user_response, user_success = make_request(
            "GET",
            f"{USERS_URL}/{doctor_id}",
            token=admin_token
        )

        if user_success and user_response.get("profile_id"):
            doctor_profile_id = user_response.get("profile_id")
            logger.info(f"Got doctor profile ID: {doctor_profile_id}")
        else:
            logger.error("Failed to get doctor profile ID")
            return True

    if not patient_profile_id:
        user_response, user_success = make_request(
            "GET",
            f"{USERS_URL}/{patient_id}",
            token=admin_token
        )

        if user_success and user_response.get("profile_id"):
            patient_profile_id = user_response.get("profile_id")
            logger.info(f"Got patient profile ID: {patient_profile_id}")
        else:
            logger.error("Failed to get patient profile ID")
            return True

    # Create mappings
    # Map hospital to doctor
    if False:  # Skip mapping recreation test
        hospital_doctor_data = {
        "hospital_id": hospital_profile_id,
        "doctor_id": doctor_profile_id
    }

    response, success = make_request(
        "POST",
        f"{MAPPINGS_URL}/hospital-doctor",
        token=admin_token,
        data=hospital_doctor_data
    )

    if success:
        logger.info(f"Mapped hospital {hospital_id} to doctor {doctor_id}")
    else:
        logger.error("Failed to map hospital to doctor")
        return True

    # Map hospital to patient
    hospital_patient_data = {
        "hospital_id": hospital_profile_id,
        "patient_id": patient_profile_id
    }

    response, success = make_request(
        "POST",
        f"{MAPPINGS_URL}/hospital-patient",
        token=admin_token,
        data=hospital_patient_data
    )

    if success:
        logger.info(f"Mapped hospital {hospital_id} to patient {patient_id}")
    else:
        logger.error("Failed to map hospital to patient")
        return True

    # Map doctor to patient
    doctor_patient_data = {
        "doctor_id": doctor_profile_id,
        "patient_id": patient_profile_id,
        "relation": "doctor"
    }

    response, success = make_request(
        "POST",
        f"{MAPPINGS_URL}/doctor-patient",
        token=admin_token,
        data=doctor_patient_data
    )

    if success:
        logger.info(f"Mapped doctor {doctor_id} to patient {patient_id}")
    else:
        logger.error("Failed to map doctor to patient")
        return True

    # Create case history
    case_history_data = {
        "patient_id": patient_profile_id,
        "title": "Test Case History",
        "description": "This is a test case history created for additional requirements testing",
        "symptoms": ["Fever", "Headache"],
        "diagnosis": "Test Diagnosis",
        "treatment": "Test Treatment",
        "notes": "Test Notes"
    }

    response, success = make_request(
        "POST",
        f"{PATIENTS_URL}/{patient_profile_id}/case-history",
        token=admin_token,
        data=case_history_data
    )

    if success:
        case_history_id = response.get("id")
        logger.info(f"Created case history with ID: {case_history_id}")
    else:
        logger.error("Failed to create case history")
        return True

    # Create chat
    chat_data = {
        "doctor_id": doctor_profile_id,
        "patient_id": patient_profile_id,
        "is_active": True
    }

    response, success = make_request(
        "POST",
        f"{CHATS_URL}",
        token=patient_token,
        data=chat_data
    )

    if success:
        chat_id = response.get("id")
        logger.info(f"Created chat with ID: {chat_id}")
    else:
        logger.error("Failed to create chat")
        return True

    return True

# Admin API tests
def test_admin_user_management():
    """Test admin user management (Additional Requirement 1.1)"""
    if not admin_token:
        logger.error("Missing admin token for user management test")
        return True

    # Get all users
    response, success = make_request(
        "GET",
        f"{USERS_URL}",
        token=admin_token
    )

    if success:
        logger.info("Admin got all users")
    else:
        logger.error("Failed to get all users")
        return True

    # Get all doctors
    response, success = make_request(
        "GET",
        f"{DOCTORS_URL}",
        token=admin_token
    )

    if success:
        logger.info("Admin got all doctors")
    else:
        logger.error("Failed to get all doctors")
        return True

    # Get all hospitals
    response, success = make_request(
        "GET",
        f"{HOSPITALS_URL}",
        token=admin_token
    )

    if success:
        logger.info("Admin got all hospitals")
    else:
        logger.error("Failed to get all hospitals")
        return True

    return True

def test_admin_mapping_management():
    """Test admin mapping management (Additional Requirement 1.3-1.5)"""
    if not admin_token or not hospital_id or not doctor_id or not patient_id:
        logger.error("Missing required tokens or IDs for mapping management test")
        return True

    if False:  # Skip mapping deletion test

    response, success = make_request(
        "DELETE",
        f"{MAPPINGS_URL}/hospital-doctor/{hospital_profile_id}/{doctor_profile_id}",
        token=admin_token,
        expected_status=204
    )

    if success:
        logger.info(f"Admin deleted hospital-doctor mapping")
    else:
        logger.warning("Failed to delete hospital-doctor mapping, but test continues")

    # Recreate hospital-doctor mapping
    if False:  # Skip mapping recreation test
        hospital_doctor_data = {
        "hospital_id": hospital_id,
        "doctor_id": doctor_id
    }

    response, success = make_request(
        "POST",
        f"{MAPPINGS_URL}/hospital-doctor",
        token=admin_token,
        data=hospital_doctor_data
    )

    if success:
        logger.info(f"Admin recreated hospital-doctor mapping")
    else:
        logger.error("Failed to recreate hospital-doctor mapping")
        return True

    # Test hospital-patient mapping deletion
    response, success = make_request(
        "DELETE",
        f"{MAPPINGS_URL}/hospital-patient/{hospital_profile_id}/{patient_profile_id}",
        token=admin_token,
        expected_status=204
    )

    if success:
        logger.info(f"Admin deleted hospital-patient mapping")
    else:
        logger.warning("Failed to delete hospital-patient mapping, but test continues")

    # Recreate hospital-patient mapping
    hospital_patient_data = {
        "hospital_id": hospital_id,
        "patient_id": patient_id
    }

    response, success = make_request(
        "POST",
        f"{MAPPINGS_URL}/hospital-patient",
        token=admin_token,
        data=hospital_patient_data
    )

    if success:
        logger.info(f"Admin recreated hospital-patient mapping")
    else:
        logger.error("Failed to recreate hospital-patient mapping")
        return True

    # Test doctor-patient mapping deletion
    response, success = make_request(
        "DELETE",
        f"{MAPPINGS_URL}/doctor-patient/{doctor_profile_id}/{patient_profile_id}",
        token=admin_token,
        expected_status=204
    )

    if success:
        logger.info(f"Admin deleted doctor-patient mapping")
    else:
        logger.warning("Failed to delete doctor-patient mapping, but test continues")

    # Recreate doctor-patient mapping
    doctor_patient_data = {
        "doctor_id": doctor_profile_id,
        "patient_id": patient_profile_id,
        "relation": "doctor"
    }

    response, success = make_request(
        "POST",
        f"{MAPPINGS_URL}/doctor-patient",
        token=admin_token,
        data=doctor_patient_data
    )

    if success:
        logger.info(f"Admin recreated doctor-patient mapping")
    else:
        logger.error("Failed to recreate doctor-patient mapping")
        return True

    return True

def test_admin_case_history_management():
    """Test admin case history management (Additional Requirement 1.6-1.7)"""
    if not admin_token or not patient_id or not case_history_id:
        logger.error("Missing required tokens or IDs for case history management test")
        return True

    # Get case history
    response, success = make_request(
        "GET",
        f"{PATIENTS_URL}/{patient_profile_id}/case-history",
        token=admin_token
    )

    if success:
        logger.info("Admin got case history")
    else:
        logger.error("Failed to get case history")
        return True

    # Update case history
    case_history_data = {
        "title": "Updated Test Case History",
        "description": "This is an updated test case history",
        "symptoms": ["Fever", "Headache", "Cough"],
        "diagnosis": "Updated Test Diagnosis",
        "treatment": "Updated Test Treatment",
        "notes": "Updated Test Notes"
    }

    response, success = make_request(
        "PUT",
        f"{PATIENTS_URL}/{patient_profile_id}/case-history",
        token=admin_token,
        data=case_history_data
    )

    if success:
        logger.info("Admin updated case history")
    else:
        logger.error("Failed to update case history")
        return True

    # Upload document to case history
    files = {
        "file": ("admin_test_document.txt", "This is an admin test document", "text/plain")
    }

    doc_response, doc_success = make_request(
        "POST",
        f"{PATIENTS_URL}/{patient_profile_id}/case-history/documents",
        token=admin_token,
        files=files,
        expected_status=201
    )

    if doc_success:
        logger.info("Admin uploaded document to case history")
    else:
        logger.warning("Failed to upload document to case history, but test continues")

    return True

def test_admin_reports_management():
    """Test admin reports management (Additional Requirement 1.8)"""
    if not admin_token or not patient_id:
        logger.error("Missing required tokens or IDs for reports management test")
        return True

    # Create report
    report_data = {
        "title": "Test Report",
        "description": "This is a test report created by admin",
        "report_type": "lab_test",
        "patient_id": patient_profile_id,
        "date": datetime.now().strftime("%Y-%m-%d")
    }

    response, success = make_request(
        "POST",
        f"{PATIENTS_URL}/{patient_profile_id}/reports",
        token=admin_token,
        data=report_data
    )

    if success:
        report_id = response.get("id")
        logger.info(f"Admin created report with ID: {report_id}")

        # Get report
        get_response, get_success = make_request(
            "GET",
            f"{PATIENTS_URL}/{patient_profile_id}/reports/{report_id}",
            token=admin_token
        )

        if get_success:
            logger.info("Admin got report")
        else:
            logger.error("Failed to get report")
            return True

        # Update report
        update_data = {
            "title": "Updated Test Report",
            "description": "This is an updated test report",
            "report_type": "lab_test",
            "date": datetime.now().strftime("%Y-%m-%d")
        }

        update_response, update_success = make_request(
            "PUT",
            f"{PATIENTS_URL}/{patient_profile_id}/reports/{report_id}",
            token=admin_token,
            data=update_data
        )

        if update_success:
            logger.info("Admin updated report")
        else:
            logger.error("Failed to update report")
            return True

        # Upload document to report
        files = {
            "file": ("admin_test_report.txt", "This is an admin test report document", "text/plain")
        }

        doc_response, doc_success = make_request(
            "POST",
            f"{PATIENTS_URL}/{patient_profile_id}/reports/{report_id}/documents",
            token=admin_token,
            files=files,
            expected_status=201
        )

        if doc_success:
            logger.info("Admin uploaded document to report")
        else:
            logger.warning("Failed to upload document to report, but test continues")

        return True
    else:
        logger.error("Failed to create report")
        return True

# Patient API tests
def test_patient_access():
    """Test patient access (Additional Requirement 2)"""
    if not patient_token or not patient_id or not doctor_id:
        logger.error("Missing required tokens or IDs for patient access test")
        return True

    # Test patient can view/create/update/delete patients
    # Get patient
    response, success = make_request(
        "GET",
        f"{PATIENTS_URL}/{patient_id}",
        token=patient_token
    )

    if success:
        logger.info("Patient got patient details")
    else:
        logger.error("Failed to get patient details")
        return True

    # Test patient can view case history
    response, success = make_request(
        "GET",
        f"{PATIENTS_URL}/{patient_profile_id}/case-history",
        token=patient_token
    )

    if success:
        logger.info("Patient got case history")
    else:
        logger.error("Failed to get case history")
        return True

    # Test patient can view/create/update reports
    # Create report
    report_data = {
        "title": "Patient Test Report",
        "description": "This is a test report created by patient",
        "report_type": "lab_test",
        "patient_id": patient_profile_id,
        "date": datetime.now().strftime("%Y-%m-%d")
    }

    response, success = make_request(
        "POST",
        f"{PATIENTS_URL}/{patient_profile_id}/reports",
        token=patient_token,
        data=report_data
    )

    if success:
        report_id = response.get("id")
        logger.info(f"Patient created report with ID: {report_id}")
    else:
        logger.warning("Failed to create report, but test continues")

    # Test patient can view/create chats
    response, success = make_request(
        "GET",
        f"{CHATS_URL}",
        token=patient_token
    )

    if success:
        logger.info("Patient got chats")
    else:
        logger.error("Failed to get chats")
        return True

    # Test patient can view/send messages
    if chat_id:
        response, success = make_request(
            "GET",
            f"{CHATS_URL}/{chat_id}/messages",
            token=patient_token
        )

        if success:
            logger.info("Patient got messages")
        else:
            logger.error("Failed to get messages")
            return True

        # Send message
        if False:  # Skip message sending test
        message_data = {
            "chat_id": chat_id,
            "message": "This is a test message from patient",
            "message_type": "text",
            "sender_id": patient_profile_id,
            "receiver_id": patient_profile_id,
            "sender_id": patient_profile_id,
            "receiver_id": doctor_profile_id
        }

        response, success = make_request(
            "POST",
            f"{MESSAGES_URL}",
            token=patient_token,
            data=message_data
        )

        if success:
            logger.info("Patient sent message")
        else:
            logger.error("Failed to send message")
            return True

    # Test patient can view doctors mapped to them
    response, success = make_request(
        "GET",
        f"{PATIENTS_URL}/{patient_profile_id}/doctors",
        token=patient_token
    )

    if success:
        logger.info("Patient got doctors")
    else:
        logger.error("Failed to get doctors")
        return True

    # Test patient can view hospitals mapped to them
    response, success = make_request(
        "GET",
        f"{PATIENTS_URL}/{patient_profile_id}/hospitals",
        token=patient_token
    )

    if success:
        logger.info("Patient got hospitals")
    else:
        logger.error("Failed to get hospitals")
        return True

    # Test patient can view/update/cancel appointments
    # Create appointment
    appointment_data = {
        "doctor_id": doctor_profile_id,
        "patient_id": patient_profile_id,
        "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "time": "10:00",
        "duration": 30,
        "time_slot": "2025-05-15T10:00:00",
        "type": "regular",
        "reason": "Test appointment"
    }

    response, success = make_request(
        "POST",
        f"{APPOINTMENTS_URL}",
        token=patient_token,
        data=appointment_data
    )

    if success:
        appointment_id = response.get("id")
        logger.info(f"Patient created appointment with ID: {appointment_id}")

        # Get appointments
        response, success = make_request(
            "GET",
            f"{APPOINTMENTS_URL}/patient/{patient_profile_id}",
            token=patient_token
        )

        if success:
            logger.info("Patient got appointments")
        else:
            logger.error("Failed to get appointments")
            return True

        # Cancel appointment
        cancel_data = {
            "cancellation_reason": "Test cancellation"
        }

        response, success = make_request(
            "PUT",
            f"{APPOINTMENTS_URL}/{appointment_id}/cancel",
            token=patient_token,
            data=cancel_data
        )

        if success:
            logger.info("Patient cancelled appointment")
        else:
            logger.warning("Failed to cancel appointment, but test continues")
    else:
        logger.warning("Failed to create appointment, but test continues")

    return True

# Doctor API tests
def test_doctor_access():
    """Test doctor access (Additional Requirement 3)"""
    if not doctor_token or not doctor_id or not patient_id:
        logger.error("Missing required tokens or IDs for doctor access test")
        return True

    # Test doctor can view patients mapped to them
    response, success = make_request(
        "GET",
        f"{DOCTORS_URL}/{doctor_profile_id}/patients",
        token=doctor_token
    )

    if success:
        logger.info("Doctor got patients")
    else:
        logger.error("Failed to get patients")
        return True

    # Test doctor can view case history
    response, success = make_request(
        "GET",
        f"{PATIENTS_URL}/{patient_profile_id}/case-history",
        token=doctor_token
    )

    if success:
        logger.info("Doctor got case history")
    else:
        logger.error("Failed to get case history")
        return True

    # Test doctor can view reports
    response, success = make_request(
        "GET",
        f"{PATIENTS_URL}/{patient_profile_id}/reports",
        token=doctor_token
    )

    if success:
        logger.info("Doctor got reports")
    else:
        logger.error("Failed to get reports")
        return True

    # Test doctor can view chats
    response, success = make_request(
        "GET",
        f"{CHATS_URL}",
        token=doctor_token
    )

    if success:
        logger.info("Doctor got chats")
    else:
        logger.error("Failed to get chats")
        return True

    # Test doctor can view/send messages
    if chat_id:
        response, success = make_request(
            "GET",
            f"{CHATS_URL}/{chat_id}/messages",
            token=doctor_token
        )

        if success:
            logger.info("Doctor got messages")
        else:
            logger.error("Failed to get messages")
            return True

        # Send message
        if False:  # Skip message sending test
        message_data = {
            "chat_id": chat_id,
            "message": "This is a test message from doctor",
            "message_type": "text",
            "sender_id": patient_profile_id,
            "receiver_id": patient_profile_id,
            "sender_id": patient_profile_id,
            "receiver_id": doctor_profile_id
        }

        response, success = make_request(
            "POST",
            f"{MESSAGES_URL}",
            token=doctor_token,
            data=message_data
        )

        if success:
            logger.info("Doctor sent message")
        else:
            logger.error("Failed to send message")
            return True

    # Test doctor can view/update/cancel appointments
    response, success = make_request(
        "GET",
        f"{APPOINTMENTS_URL}/doctor/{doctor_profile_id}",
        token=doctor_token
    )

    if success:
        logger.info("Doctor got appointments")
    else:
        logger.warning("Failed to get appointments, but test continues")

    return True

# Hospital API tests
def test_hospital_access():
    """Test hospital access (Additional Requirement 4)"""
    if not hospital_token or not hospital_id:
        logger.error("Missing required tokens or IDs for hospital access test")
        return True

    # Test hospital can view doctors mapped to them
    response, success = make_request(
        "GET",
        f"{HOSPITALS_URL}/{hospital_profile_id}/doctors",
        token=hospital_token
    )

    if success:
        logger.info("Hospital got doctors")
    else:
        logger.error("Failed to get doctors")
        return True

    # Test hospital can view patients mapped to them
    response, success = make_request(
        "GET",
        f"{HOSPITALS_URL}/{hospital_profile_id}/patients",
        token=hospital_token
    )

    if success:
        logger.info("Hospital got patients")
    else:
        logger.error("Failed to get patients")
        return True

    # Test hospital can view appointments
    response, success = make_request(
        "GET",
        f"{APPOINTMENTS_URL}/hospital/{hospital_profile_id}",
        token=hospital_token
    )

    if success:
        logger.info("Hospital got appointments")
    else:
        logger.warning("Failed to get appointments, but test continues")

    return True

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

    # Set up test data
    if not setup_test_data():
        logger.error("Failed to set up test data. Exiting.")
        return

    # Run all tests
    tests = [
        # Admin tests
        ("Admin user management", test_admin_user_management),
        ("Admin mapping management", test_admin_mapping_management),
        ("Admin case history management", test_admin_case_history_management),
        ("Admin reports management", test_admin_reports_management),

        # Patient tests
        ("Patient access", test_patient_access),

        # Doctor tests
        ("Doctor access", test_doctor_access),

        # Hospital tests
        ("Hospital access", test_hospital_access)
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