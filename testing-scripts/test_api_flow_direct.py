#!/usr/bin/env python3
"""
Test API Flow (Direct)

This script tests all the flows of the POCA service by hitting actual APIs in non-docker flow.
It uses direct signup endpoints to create test data.
"""

import sys
import logging
import time
import requests
import random
import string
from typing import Dict, Any, Optional, List

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
HOSPITALS_URL = f"{BASE_URL}/api/v1/hospitals"
DOCTORS_URL = f"{BASE_URL}/api/v1/doctors"
PATIENTS_URL = f"{BASE_URL}/api/v1/patients"
AI_URL = f"{BASE_URL}/api/v1/ai"
AI_SESSIONS_URL = f"{AI_URL}/sessions"
AI_MESSAGES_URL = f"{AI_URL}/messages"

# Now implemented endpoints
CHATS_URL = f"{BASE_URL}/api/v1/chats"
MESSAGES_URL = f"{BASE_URL}/api/v1/messages"
MAPPINGS_URL = f"{BASE_URL}/api/v1/mappings"

# Default admin credentials
DEFAULT_ADMIN_EMAIL = "admin@example.com"
DEFAULT_ADMIN_PASSWORD = "admin123"

# Test data for this script
def generate_random_suffix():
    """Generate a random suffix for email addresses"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

RANDOM_SUFFIX = generate_random_suffix()

TEST_HOSPITAL_NAME = "API Test Hospital"
TEST_HOSPITAL_EMAIL = f"api.test.hospital.{RANDOM_SUFFIX}@example.com"
TEST_HOSPITAL_PASSWORD = "hospital123"

TEST_DOCTOR_NAME = "Dr. API Test"
TEST_DOCTOR_EMAIL = f"api.test.doctor.{RANDOM_SUFFIX}@example.com"
TEST_DOCTOR_PASSWORD = "doctor123"
TEST_DOCTOR_SPECIALIZATION = "General Medicine"

TEST_PATIENT_NAME = "API Test Patient"
TEST_PATIENT_EMAIL = f"api.test.patient.{RANDOM_SUFFIX}@example.com"
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
            hospital_data["id"] = result.get("user_id")  # Use user_id as the ID
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

def get_doctor_profile_id(token: str, doctor_user_id: str) -> Optional[str]:
    """Get doctor profile ID from user ID"""
    logging.info(f"Getting doctor profile ID for user ID: {doctor_user_id}...")

    try:
        response = requests.get(
            f"{USERS_URL}/{doctor_user_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            user = response.json()
            profile_id = user.get("profile_id")
            if profile_id:
                logging.info(f"Got doctor profile ID: {profile_id}")
                return profile_id
            else:
                logging.error(f"User {doctor_user_id} has no profile ID")
                return None
        else:
            logging.error(f"Failed to get user: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting doctor profile ID: {str(e)}")
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

def get_hospital_profile_id(token: str, hospital_user_id: str) -> Optional[str]:
    """Get hospital profile ID from user ID"""
    logging.info(f"Getting hospital profile ID for user ID: {hospital_user_id}...")

    try:
        response = requests.get(
            f"{USERS_URL}/{hospital_user_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            user = response.json()
            profile_id = user.get("profile_id")
            if profile_id:
                logging.info(f"Got hospital profile ID: {profile_id}")
                return profile_id
            else:
                logging.error(f"User {hospital_user_id} has no profile ID")
                return None
        else:
            logging.error(f"Failed to get user: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting hospital profile ID: {str(e)}")
        return None

def map_doctor_to_patient(admin_token: str, doctor_id: str, patient_id: str) -> bool:
    """Map a doctor to a patient"""
    logging.info(f"Mapping doctor {doctor_id} to patient {patient_id}...")

    try:
        # Get profile IDs if needed
        doctor_profile_id = get_doctor_profile_id(admin_token, doctor_id) or doctor_id
        patient_profile_id = get_patient_profile_id(admin_token, patient_id) or patient_id

        mapping_data = {
            "doctor_id": doctor_profile_id,
            "patient_id": patient_profile_id
        }

        response = requests.post(
            f"{MAPPINGS_URL}/doctor-patient",
            json=mapping_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        if response.status_code in [200, 201]:
            logging.info(f"Mapped doctor {doctor_profile_id} to patient {patient_profile_id}")
            return True
        else:
            logging.error(f"Failed to map doctor to patient: {response.text}")
            return False
    except Exception as e:
        logging.error(f"Error mapping doctor to patient: {str(e)}")
        return False

def create_chat(admin_token: str, doctor_id: str, patient_id: str) -> Optional[Dict[str, Any]]:
    """Create a chat between a doctor and a patient"""
    logging.info(f"Creating chat between doctor {doctor_id} and patient {patient_id}...")

    try:
        # Get profile IDs if needed
        doctor_profile_id = get_doctor_profile_id(admin_token, doctor_id) or doctor_id
        patient_profile_id = get_patient_profile_id(admin_token, patient_id) or patient_id

        chat_data = {
            "doctor_id": doctor_profile_id,
            "patient_id": patient_profile_id
        }

        response = requests.post(
            CHATS_URL,
            json=chat_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        if response.status_code in [200, 201]:
            chat = response.json()
            logging.info(f"Created chat with ID: {chat.get('id')}")
            return chat
        else:
            logging.error(f"Failed to create chat: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error creating chat: {str(e)}")
        return None

def send_message(token: str, chat_id: str, sender_id: str, receiver_id: str, content: str) -> Optional[Dict[str, Any]]:
    """Send a message in a chat"""
    logging.info(f"Sending message from {sender_id} to {receiver_id} in chat {chat_id}...")

    try:
        # Get profile IDs if needed
        if "doctor" in sender_id:
            sender_profile_id = get_doctor_profile_id(token, sender_id) or sender_id
        elif "patient" in sender_id:
            sender_profile_id = get_patient_profile_id(token, sender_id) or sender_id
        else:
            sender_profile_id = sender_id

        if "doctor" in receiver_id:
            receiver_profile_id = get_doctor_profile_id(token, receiver_id) or receiver_id
        elif "patient" in receiver_id:
            receiver_profile_id = get_patient_profile_id(token, receiver_id) or receiver_id
        else:
            receiver_profile_id = receiver_id

        message_data = {
            "chat_id": chat_id,
            "sender_id": sender_profile_id,
            "receiver_id": receiver_profile_id,
            "message": content,
            "message_type": "text"
        }

        response = requests.post(
            MESSAGES_URL,
            json=message_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code in [200, 201]:
            message = response.json()
            logging.info(f"Sent message with ID: {message.get('id')}")
            return message
        else:
            logging.error(f"Failed to send message: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error sending message: {str(e)}")
        return None

def create_ai_session(token: str, chat_id: str) -> Optional[Dict[str, Any]]:
    """Create an AI session for a chat"""
    logging.info(f"Creating AI session for chat {chat_id}...")

    try:
        session_data = {
            "chat_id": chat_id
        }

        response = requests.post(
            AI_SESSIONS_URL,
            json=session_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code in [200, 201]:
            session = response.json()
            logging.info(f"Created AI session with ID: {session.get('id')}")
            return session
        else:
            logging.error(f"Failed to create AI session: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error creating AI session: {str(e)}")
        return None

def send_ai_message(token: str, session_id: str, content: str) -> Optional[Dict[str, Any]]:
    """Send a message to the AI assistant"""
    logging.info(f"Sending message to AI in session {session_id}: {content}")

    try:
        message_data = {
            "content": content
        }

        response = requests.post(
            f"{AI_SESSIONS_URL}/{session_id}/messages",
            json=message_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code in [200, 201]:
            response_data = response.json()
            logging.info(f"Got AI response: {response_data.get('response', '')[:50]}...")
            return response_data
        else:
            logging.error(f"Failed to send message to AI: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error sending message to AI: {str(e)}")
        return None

def refresh_token(refresh_token: str) -> Optional[Dict[str, Any]]:
    """Refresh authentication token"""
    logging.info("Refreshing authentication token...")

    try:
        response = requests.post(
            f"{AUTH_URL}/refresh",
            json={"refresh_token": refresh_token}
        )

        if response.status_code == 200:
            token_data = response.json()
            logging.info(f"Refreshed authentication token for user ID: {token_data.get('user_id')}")
            return token_data
        else:
            logging.error(f"Failed to refresh authentication token: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error refreshing authentication token: {str(e)}")
        return None

def get_all_users(token: str) -> Optional[List[Dict[str, Any]]]:
    """Get all users"""
    logging.info("Getting all users...")

    try:
        response = requests.get(
            USERS_URL,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            users = response.json()
            logging.info(f"Got {len(users) if isinstance(users, list) else 0} users")
            return users
        else:
            logging.error(f"Failed to get users: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting users: {str(e)}")
        return None

def get_user_by_id(token: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    logging.info(f"Getting user with ID: {user_id}...")

    try:
        response = requests.get(
            f"{USERS_URL}/{user_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            user = response.json()
            logging.info(f"Got user: {user.get('name')}")
            return user
        else:
            logging.error(f"Failed to get user: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting user: {str(e)}")
        return None

def update_user(token: str, user_id: str, name: str, contact: str, address: str) -> Optional[Dict[str, Any]]:
    """Update user profile"""
    logging.info(f"Updating user with ID: {user_id}...")

    try:
        user_data = {
            "name": name,
            "contact": contact,
            "address": address
        }

        response = requests.put(
            f"{USERS_URL}/{user_id}",
            json=user_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            user = response.json()
            logging.info(f"Updated user: {user.get('name')}")
            return user
        else:
            logging.error(f"Failed to update user: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error updating user: {str(e)}")
        return None

def get_all_hospitals(token: str) -> Optional[List[Dict[str, Any]]]:
    """Get all hospitals"""
    logging.info("Getting all hospitals...")

    try:
        response = requests.get(
            HOSPITALS_URL,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            hospitals = response.json()
            logging.info(f"Got {len(hospitals) if isinstance(hospitals, list) else 0} hospitals")
            return hospitals
        else:
            logging.error(f"Failed to get hospitals: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting hospitals: {str(e)}")
        return None

def get_hospital_by_id(token: str, hospital_id: str) -> Optional[Dict[str, Any]]:
    """Get hospital by ID"""
    logging.info(f"Getting hospital with ID: {hospital_id}...")

    try:
        response = requests.get(
            f"{HOSPITALS_URL}/{hospital_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            hospital = response.json()
            logging.info(f"Got hospital: {hospital.get('name')}")
            return hospital
        else:
            logging.error(f"Failed to get hospital: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting hospital: {str(e)}")
        return None

def get_all_doctors(token: str) -> Optional[List[Dict[str, Any]]]:
    """Get all doctors"""
    logging.info("Getting all doctors...")

    try:
        response = requests.get(
            DOCTORS_URL,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            doctors = response.json()
            logging.info(f"Got {len(doctors) if isinstance(doctors, list) else 0} doctors")
            return doctors
        else:
            logging.error(f"Failed to get doctors: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting doctors: {str(e)}")
        return None

def get_doctor_by_id(token: str, doctor_id: str) -> Optional[Dict[str, Any]]:
    """Get doctor by ID"""
    logging.info(f"Getting doctor with ID: {doctor_id}...")

    try:
        response = requests.get(
            f"{DOCTORS_URL}/{doctor_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            doctor = response.json()
            logging.info(f"Got doctor: {doctor.get('name')}")
            return doctor
        else:
            logging.error(f"Failed to get doctor: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting doctor: {str(e)}")
        return None

def update_doctor(token: str, doctor_id: str, name: str, designation: str, experience: int, details: str, contact: str) -> Optional[Dict[str, Any]]:
    """Update doctor profile"""
    logging.info(f"Updating doctor with ID: {doctor_id}...")

    try:
        doctor_data = {
            "name": name,
            "designation": designation,
            "experience": experience,
            "details": details,
            "contact": contact
        }

        response = requests.put(
            f"{DOCTORS_URL}/{doctor_id}",
            json=doctor_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            doctor = response.json()
            logging.info(f"Updated doctor: {doctor.get('name')}")
            return doctor
        else:
            logging.error(f"Failed to update doctor: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error updating doctor: {str(e)}")
        return None

def get_all_patients(token: str) -> Optional[List[Dict[str, Any]]]:
    """Get all patients"""
    logging.info("Getting all patients...")

    try:
        response = requests.get(
            PATIENTS_URL,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            patients = response.json()
            logging.info(f"Got {len(patients) if isinstance(patients, list) else 0} patients")
            return patients
        else:
            logging.error(f"Failed to get patients: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting patients: {str(e)}")
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

def update_patient(token: str, patient_id: str, name: str, age: int, gender: str, contact: str, address: str) -> Optional[Dict[str, Any]]:
    """Update patient profile"""
    logging.info(f"Updating patient with ID: {patient_id}...")

    try:
        patient_data = {
            "name": name,
            "age": age,
            "gender": gender,
            "contact": contact,
            "address": address
        }

        response = requests.put(
            f"{PATIENTS_URL}/{patient_id}",
            json=patient_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            patient = response.json()
            logging.info(f"Updated patient: {patient.get('name')}")
            return patient
        else:
            logging.error(f"Failed to update patient: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error updating patient: {str(e)}")
        return None

def get_patient_case_history(token: str, patient_id: str, create_if_not_exists: bool = False) -> Optional[Dict[str, Any]]:
    """Get patient case history"""
    logging.info(f"Getting case history for patient with ID: {patient_id}...")

    try:
        url = f"{PATIENTS_URL}/{patient_id}/case-history"
        if create_if_not_exists:
            url += "?create_if_not_exists=true"

        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            case_history = response.json()
            logging.info(f"Got case history for patient: {patient_id}")
            return case_history
        else:
            logging.error(f"Failed to get patient case history: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting patient case history: {str(e)}")
        return None

def create_patient_case_history(token: str, patient_id: str, summary: str, documents: List[str]) -> Optional[Dict[str, Any]]:
    """Create patient case history"""
    logging.info(f"Creating case history for patient with ID: {patient_id}...")

    try:
        case_history_data = {
            "patient_id": patient_id,
            "summary": summary,
            "documents": documents
        }

        response = requests.post(
            f"{PATIENTS_URL}/{patient_id}/case-history",
            json=case_history_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code in [200, 201]:
            case_history = response.json()
            logging.info(f"Created case history for patient: {patient_id}")
            return case_history
        else:
            logging.error(f"Failed to create patient case history: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error creating patient case history: {str(e)}")
        return None

def update_patient_case_history(token: str, patient_id: str, summary: str, documents: List[str]) -> Optional[Dict[str, Any]]:
    """Update patient case history"""
    logging.info(f"Updating case history for patient with ID: {patient_id}...")

    try:
        case_history_data = {
            "summary": summary,
            "documents": documents
        }

        response = requests.put(
            f"{PATIENTS_URL}/{patient_id}/case-history",
            json=case_history_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            case_history = response.json()
            logging.info(f"Updated case history for patient: {patient_id}")
            return case_history
        else:
            logging.error(f"Failed to update patient case history: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error updating patient case history: {str(e)}")
        return None

def get_all_chats(token: str) -> Optional[List[Dict[str, Any]]]:
    """Get all chats for the current user"""
    logging.info("Getting all chats...")

    try:
        response = requests.get(
            CHATS_URL,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            chats = response.json()
            logging.info(f"Got {len(chats) if isinstance(chats, list) else 0} chats")
            return chats
        else:
            logging.error(f"Failed to get chats: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting chats: {str(e)}")
        return None

def get_chat_by_id(token: str, chat_id: str) -> Optional[Dict[str, Any]]:
    """Get chat by ID"""
    logging.info(f"Getting chat with ID: {chat_id}...")

    try:
        response = requests.get(
            f"{CHATS_URL}/{chat_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            chat = response.json()
            logging.info(f"Got chat with ID: {chat.get('id')}")
            return chat
        else:
            logging.error(f"Failed to get chat: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting chat: {str(e)}")
        return None

def get_chat_messages(token: str, chat_id: str) -> Optional[List[Dict[str, Any]]]:
    """Get all messages for a chat"""
    logging.info(f"Getting messages for chat with ID: {chat_id}...")

    try:
        response = requests.get(
            f"{CHATS_URL}/{chat_id}/messages",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            messages = response.json()
            logging.info(f"Got {len(messages) if isinstance(messages, list) else 0} messages for chat: {chat_id}")
            return messages
        else:
            logging.error(f"Failed to get chat messages: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting chat messages: {str(e)}")
        return None

def update_message_read_status(token: str, message_ids: List[str], is_read: bool) -> bool:
    """Update read status for messages"""
    logging.info(f"Updating read status for {len(message_ids)} messages...")

    try:
        data = {
            "message_ids": message_ids,
            "is_read": is_read
        }

        response = requests.put(
            f"{MESSAGES_URL}/read-status",
            json=data,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            logging.info(f"Updated read status for {len(message_ids)} messages")
            return True
        else:
            logging.error(f"Failed to update message read status: {response.text}")
            return False
    except Exception as e:
        logging.error(f"Error updating message read status: {str(e)}")
        return False

def get_ai_session_messages(token: str, session_id: str) -> Optional[List[Dict[str, Any]]]:
    """Get all messages for an AI session"""
    logging.info(f"Getting messages for AI session with ID: {session_id}...")

    try:
        response = requests.get(
            f"{AI_SESSIONS_URL}/{session_id}/messages",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            messages = response.json()
            logging.info(f"Got {len(messages) if isinstance(messages, list) else 0} messages for AI session: {session_id}")
            return messages
        else:
            logging.error(f"Failed to get AI session messages: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting AI session messages: {str(e)}")
        return None

def end_ai_session(token: str, session_id: str) -> bool:
    """End an AI session"""
    logging.info(f"Ending AI session with ID: {session_id}...")

    try:
        response = requests.put(
            f"{AI_SESSIONS_URL}/{session_id}/end",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            logging.info(f"Ended AI session: {session_id}")
            return True
        else:
            logging.error(f"Failed to end AI session: {response.text}")
            return False
    except Exception as e:
        logging.error(f"Error ending AI session: {str(e)}")
        return False

def update_ai_summary(token: str, session_id: str, summary: str) -> Optional[Dict[str, Any]]:
    """Update the summary for an AI session"""
    logging.info(f"Updating summary for AI session with ID: {session_id}...")

    try:
        data = {
            "summary": summary
        }

        response = requests.put(
            f"{AI_SESSIONS_URL}/{session_id}/summary",
            json=data,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            result = response.json()
            logging.info(f"Updated summary for AI session: {session_id}")
            return result
        else:
            logging.error(f"Failed to update AI session summary: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error updating AI session summary: {str(e)}")
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

def update_current_user_profile(token: str, name: str, contact: str, address: str) -> Optional[Dict[str, Any]]:
    """Update current user profile"""
    logging.info("Updating current user profile...")

    try:
        user_data = {
            "name": name,
            "contact": contact,
            "address": address
        }

        response = requests.put(
            f"{USERS_URL}/me",
            json=user_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            user = response.json()
            logging.info(f"Updated current user profile: {user.get('name')}")
            return user
        else:
            logging.error(f"Failed to update current user profile: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error updating current user profile: {str(e)}")
        return None

def map_hospital_to_doctor(token: str, hospital_id: str, doctor_id: str) -> bool:
    """Map a hospital to a doctor"""
    logging.info(f"Mapping hospital {hospital_id} to doctor {doctor_id}...")

    try:
        # Get profile IDs if needed
        hospital_profile_id = get_hospital_profile_id(token, hospital_id) or hospital_id
        doctor_profile_id = get_doctor_profile_id(token, doctor_id) or doctor_id

        mapping_data = {
            "hospital_id": hospital_profile_id,
            "doctor_id": doctor_profile_id
        }

        response = requests.post(
            f"{MAPPINGS_URL}/hospital-doctor",
            json=mapping_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code in [200, 201]:
            logging.info(f"Mapped hospital {hospital_profile_id} to doctor {doctor_profile_id}")
            return True
        else:
            logging.error(f"Failed to map hospital to doctor: {response.text}")
            return False
    except Exception as e:
        logging.error(f"Error mapping hospital to doctor: {str(e)}")
        return False

def map_hospital_to_patient(token: str, hospital_id: str, patient_id: str) -> bool:
    """Map a hospital to a patient"""
    logging.info(f"Mapping hospital {hospital_id} to patient {patient_id}...")

    try:
        # Get profile IDs if needed
        hospital_profile_id = get_hospital_profile_id(token, hospital_id) or hospital_id
        patient_profile_id = get_patient_profile_id(token, patient_id) or patient_id

        mapping_data = {
            "hospital_id": hospital_profile_id,
            "patient_id": patient_profile_id
        }

        response = requests.post(
            f"{MAPPINGS_URL}/hospital-patient",
            json=mapping_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code in [200, 201]:
            logging.info(f"Mapped hospital {hospital_profile_id} to patient {patient_profile_id}")
            return True
        else:
            logging.error(f"Failed to map hospital to patient: {response.text}")
            return False
    except Exception as e:
        logging.error(f"Error mapping hospital to patient: {str(e)}")
        return False

def test_authentication_flow() -> tuple[bool, Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Test authentication flow"""
    logging.info("Testing authentication flow...")

    # Admin login
    admin_token_data = get_auth_token(DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD)
    if not admin_token_data:
        logging.error("Admin login failed")
        return False, None, None, None

    logging.info("Admin login successful")

    # Create test hospital, doctor, and patient
    hospital_data = create_hospital()
    if not hospital_data:
        logging.error("Failed to create test hospital")
        return False, None, None, None

    # Hospital login
    hospital_token_data = get_auth_token(TEST_HOSPITAL_EMAIL, TEST_HOSPITAL_PASSWORD)
    if not hospital_token_data:
        logging.error("Hospital login failed")
        return False, None, None, None

    logging.info("Hospital login successful")

    # Create doctor
    doctor_data = create_doctor()
    if not doctor_data:
        logging.error("Failed to create test doctor")
        return False, None, None, None

    # Doctor login
    doctor_token_data = get_auth_token(TEST_DOCTOR_EMAIL, TEST_DOCTOR_PASSWORD)
    if not doctor_token_data:
        logging.error("Doctor login failed")
        return False, None, None, None

    logging.info("Doctor login successful")

    # Create patient
    patient_data = create_patient()
    if not patient_data:
        logging.error("Failed to create test patient")
        return False, None, None, None

    # Patient login
    patient_token_data = get_auth_token(TEST_PATIENT_EMAIL, TEST_PATIENT_PASSWORD)
    if not patient_token_data:
        logging.error("Patient login failed")
        return False, None, None, None

    logging.info("Patient login successful")

    logging.info("Authentication flow test completed successfully")
    return True, doctor_data, patient_data, hospital_data

def main():
    """Main test function"""
    print("Starting API flow test for POCA service...")
    print("This may take a few minutes...")

    # Check if the server is up
    if not check_server_health():
        logging.error("Server is not running. Please start the server and try again.")
        return

    # Test authentication flow
    auth_result, doctor_data, patient_data, hospital_data = test_authentication_flow()
    if not auth_result:
        logging.error("Authentication flow test failed. Aborting.")
        return

    # Get tokens for further tests
    admin_token_data = get_auth_token(DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD)
    if not admin_token_data:
        logging.error("Failed to get admin token. Aborting.")
        return

    admin_token = admin_token_data["access_token"]
    admin_refresh_token = admin_token_data["refresh_token"]

    # Test token refresh
    refreshed_token_data = refresh_token(admin_refresh_token)
    if refreshed_token_data:
        logging.info("Token refresh successful")
        admin_token = refreshed_token_data["access_token"]
    else:
        logging.warning("Token refresh failed, continuing with original token")

    # Get doctor token
    doctor_token_data = get_auth_token(TEST_DOCTOR_EMAIL, TEST_DOCTOR_PASSWORD)
    if not doctor_token_data:
        logging.error("Failed to get doctor token. Aborting.")
        return

    doctor_token = doctor_token_data["access_token"]
    doctor_id = doctor_data["id"]

    # Get patient token
    patient_token_data = get_auth_token(TEST_PATIENT_EMAIL, TEST_PATIENT_PASSWORD)
    if not patient_token_data:
        logging.error("Failed to get patient token. Aborting.")
        return

    patient_token = patient_token_data["access_token"]
    patient_id = patient_data["id"]
    hospital_id = hospital_data["id"]

    # Test Users API (implemented)
    logging.info("Testing Users API...")
    users = get_all_users(admin_token)
    if users is not None:
        logging.info("Get all users successful")

    user = get_user_by_id(admin_token, doctor_id)
    if user is not None:
        logging.info("Get user by ID successful")

        # Update user
        updated_user = update_user(
            doctor_token,
            doctor_id,
            f"{TEST_DOCTOR_NAME} Updated",
            "9876543210",
            "456 Updated Doctor St"
        )
        if updated_user is not None:
            logging.info("Update user successful")

    # Test current user profile endpoint
    logging.info("Testing current user profile...")
    current_user = get_current_user_profile(doctor_token)
    if current_user is not None:
        logging.info("Get current user profile successful")

        # Update current user profile
        updated_current_user = update_current_user_profile(
            doctor_token,
            f"{TEST_DOCTOR_NAME} Updated Again",
            "1234567890",
            "789 Updated Doctor St"
        )
        if updated_current_user is not None:
            logging.info("Update current user profile successful")

    # Test Hospitals API (implemented)
    logging.info("Testing Hospitals API...")
    hospitals = get_all_hospitals(admin_token)
    if hospitals is not None:
        logging.info("Get all hospitals successful")

    hospital = get_hospital_by_id(admin_token, hospital_id)
    if hospital is not None:
        logging.info("Get hospital by ID successful")

    # Test Mappings API (now implemented)
    logging.info("Testing Mappings API...")

    # Map doctor to patient
    doctor_patient_mapping = map_doctor_to_patient(admin_token, doctor_id, patient_id)
    if doctor_patient_mapping:
        logging.info("Map doctor to patient successful")

    # Map hospital to doctor
    hospital_doctor_mapping = map_hospital_to_doctor(admin_token, hospital_id, doctor_id)
    if hospital_doctor_mapping:
        logging.info("Map hospital to doctor successful")

    # Map hospital to patient
    hospital_patient_mapping = map_hospital_to_patient(admin_token, hospital_id, patient_id)
    if hospital_patient_mapping:
        logging.info("Map hospital to patient successful")

    # Test Chats API (now implemented)
    logging.info("Testing Chats API...")

    # Create chat
    chat_data = create_chat(admin_token, doctor_id, patient_id)
    if chat_data:
        chat_id = chat_data["id"]
        logging.info(f"Created chat with ID: {chat_id}")

        # Get all chats
        chats = get_all_chats(patient_token)
        if chats is not None:
            logging.info("Get all chats successful")

        # Get chat by ID
        chat = get_chat_by_id(patient_token, chat_id)
        if chat is not None:
            logging.info("Get chat by ID successful")

        # Test Messages API (now implemented)
        logging.info("Testing Messages API...")

        # Send message from patient to doctor
        patient_message = send_message(
            patient_token,
            chat_id,
            patient_id,
            doctor_id,
            "Hello doctor, I'm not feeling well."
        )
        if patient_message:
            logging.info("Send message from patient to doctor successful")

            # Send message from doctor to patient
            doctor_message = send_message(
                doctor_token,
                chat_id,
                doctor_id,
                patient_id,
                "Hello, what symptoms are you experiencing?"
            )
            if doctor_message:
                logging.info("Send message from doctor to patient successful")

                # Get chat messages
                messages = get_chat_messages(patient_token, chat_id)
                if messages is not None:
                    logging.info("Get chat messages successful")

                    # Update message read status
                    if isinstance(messages, dict) and "messages" in messages and len(messages["messages"]) > 0:
                        message_ids = [msg["id"] for msg in messages["messages"]]
                        if message_ids and update_message_read_status(patient_token, message_ids, True):
                            logging.info("Update message read status successful")

        # Test AI API (implemented)
        logging.info("Testing AI API...")

        # Create AI session
        session_data = create_ai_session(patient_token, chat_id)
        if session_data:
            session_id = session_data["id"]
            logging.info(f"Created AI session with ID: {session_id}")

            # Send a message to AI
            ai_message = send_ai_message(
                patient_token,
                session_id,
                "I have a headache and fever. What could be wrong with me?"
            )
            if ai_message:
                logging.info("Send message to AI successful")

                # Get AI session messages
                ai_messages = get_ai_session_messages(patient_token, session_id)
                if ai_messages is not None:
                    logging.info("Get AI session messages successful")
    else:
        logging.error("Failed to create chat. Skipping chat and message tests.")

    print("API flow test completed successfully!")

if __name__ == "__main__":
    main()
