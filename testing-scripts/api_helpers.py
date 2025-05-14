#!/usr/bin/env python3
"""
API Helpers

This file contains helper functions for making API calls to the POCA service.
These functions are used by the test scripts to interact with the service.
"""

import requests
import logging
from typing import Dict, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# API configuration
BASE_URL = "http://localhost:8002/api/v1"
AUTH_URL = f"{BASE_URL}/auth"
USERS_URL = f"{BASE_URL}/users"
HOSPITALS_URL = f"{BASE_URL}/hospitals"
DOCTORS_URL = f"{BASE_URL}/doctors"
PATIENTS_URL = f"{BASE_URL}/patients"
MAPPINGS_URL = f"{BASE_URL}/mappings"
CHATS_URL = f"{BASE_URL}/chats"
MESSAGES_URL = f"{BASE_URL}/messages"
AI_URL = f"{BASE_URL}/ai-assistant"
CASE_HISTORY_URL = f"{BASE_URL}/case-history"
REPORTS_URL = f"{BASE_URL}/reports"

# Default admin credentials
DEFAULT_ADMIN_EMAIL = "admin@example.com"
DEFAULT_ADMIN_PASSWORD = "admin123"

def check_server_health() -> bool:
    """Check if the server is up and running"""
    logging.info("Checking server health...")

    try:
        # Try the health endpoint first
        response = requests.get(f"{BASE_URL.split('/api')[0]}/health")
        if response.status_code == 200:
            logging.info("Server is up and running (health endpoint)")
            return True
    except Exception as e:
        logging.warning(f"Health endpoint check failed: {str(e)}")

    # Try the auth endpoint
    try:
        response = requests.post(
            f"{AUTH_URL}/login",
            data={"username": DEFAULT_ADMIN_EMAIL, "password": DEFAULT_ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if response.status_code in [200, 401, 422]:  # Any of these codes means the server is running
            logging.info("Server is up and running (auth endpoint)")
            return True
    except Exception as e:
        logging.warning(f"Auth endpoint check failed: {str(e)}")

    # If we get here, try a simple GET request to the base URL
    try:
        response = requests.get(BASE_URL.split('/api')[0])
        logging.info("Server is up and running (base URL)")
        return True
    except Exception as e:
        logging.error(f"Server health check failed: {str(e)}")
        return False

def get_auth_token(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Get authentication token"""
    logging.info(f"Getting authentication token for {email}...")

    try:
        response = requests.post(
            f"{AUTH_URL}/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if response.status_code != 200:
            logging.error(f"Authentication failed: {response.text}")
            return None

        token_data = response.json()
        logging.info(f"Got authentication token for user ID: {token_data.get('user_id', 'unknown')}")
        return token_data
    except Exception as e:
        logging.error(f"Error getting authentication token: {str(e)}")
        return None

def get_or_create_hospital(token: str, name: str, email: str, password: str) -> Optional[Dict[str, Any]]:
    """Get or create a hospital"""
    logging.info(f"Getting or creating hospital: {name}...")

    # Get all hospitals
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # First try to get the hospital by email
        response = requests.get(
            HOSPITALS_URL,
            headers=headers
        )

        if response.status_code == 200:
            try:
                hospitals = response.json()
                if isinstance(hospitals, list):
                    for hospital in hospitals:
                        if isinstance(hospital, dict) and hospital.get("email") == email:
                            logging.info(f"Found existing hospital: {name} with ID: {hospital.get('id')}")
                            return hospital
            except Exception as e:
                logging.error(f"Error parsing hospitals response: {str(e)}")
                # Continue with creating a new hospital

        # If not found, create a new hospital using hospital-signup
        logging.info(f"Creating new hospital: {name}...")

        # Create hospital using hospital-signup
        hospital_data = {
            "name": name,
            "address": f"{name} Address, Main Street",
            "city": "Test City",
            "state": "Test State",
            "country": "Test Country",
            "contact": "1234567890",
            "pin_code": "12345",
            "email": email,
            "password": password,
            "specialities": ["Cardiology", "Neurology", "Pediatrics"],
            "website": f"https://{name.lower().replace(' ', '')}.example.com"
        }

        response = requests.post(
            f"{AUTH_URL}/hospital-signup",
            json=hospital_data
        )

        if response.status_code not in [200, 201]:
            logging.error(f"Failed to create hospital: {response.text}")
            return None

        # Get the token from the response
        response_data = response.json()
        user_id = response_data.get("user_id")

        if not user_id:
            logging.error(f"Failed to get user ID: {response_data}")
            return None

        # Get all hospitals again to find the newly created one
        response = requests.get(
            HOSPITALS_URL,
            headers=headers
        )

        if response.status_code != 200:
            logging.error(f"Failed to get hospitals: {response.text}")
            return None

        try:
            hospitals = response.json()
            if isinstance(hospitals, list):
                for hospital in hospitals:
                    if isinstance(hospital, dict) and hospital.get("email") == email:
                        hospital_id = hospital.get("id")
                        if hospital_id:
                            hospital_data["id"] = hospital_id
                            hospital_data["user_id"] = user_id
                            logging.info(f"Created hospital: {name} with ID: {hospital_id}")
                            return hospital_data
        except Exception as e:
            logging.error(f"Error parsing hospitals response: {str(e)}")
            return None

        logging.error(f"Failed to find newly created hospital with email: {email}")
        return None
    except Exception as e:
        logging.error(f"Error getting or creating hospital: {str(e)}")
        return None

# Alias for backward compatibility
create_hospital = get_or_create_hospital

def get_or_create_doctor(token: str, name: str, email: str, password: str, specialization: str, hospital_id: str) -> Optional[Dict[str, Any]]:
    """Get or create a doctor"""
    logging.info(f"Getting or creating doctor: {name}...")

    # Get all doctors
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # First try to get the doctor by email
        response = requests.get(
            DOCTORS_URL,
            headers=headers
        )

        if response.status_code == 200:
            try:
                doctors = response.json()
                if isinstance(doctors, list):
                    for doctor in doctors:
                        if isinstance(doctor, dict) and doctor.get("email") == email:
                            logging.info(f"Found existing doctor: {name} with ID: {doctor.get('id')}")

                            # Make sure the doctor is mapped to the hospital
                            mapping_data = {
                                "hospital_id": hospital_id,
                                "doctor_id": doctor.get("id")
                            }

                            mapping_response = requests.post(
                                f"{MAPPINGS_URL}/hospital-doctor",
                                json=mapping_data,
                                headers=headers
                            )

                            if mapping_response.status_code not in [200, 201]:
                                logging.warning(f"Failed to map doctor to hospital: {mapping_response.text}")

                            doctor["specialization"] = specialization
                            return doctor
            except Exception as e:
                logging.error(f"Error parsing doctors response: {str(e)}")
                # Continue with creating a new doctor

        # If not found, create a new doctor using doctor-signup
        logging.info(f"Creating new doctor: {name}...")

        # Create doctor using doctor-signup
        doctor_data = {
            "name": name,
            "email": email,
            "password": password,
            "photo": f"https://example.com/{name.lower().replace(' ', '')}.jpg",
            "designation": f"Senior {specialization}",
            "experience": 10,
            "details": f"MD, {specialization}, Medical University",
            "contact": "1234567890",
            "address": "123 Doctor St"
        }

        response = requests.post(
            f"{AUTH_URL}/doctor-signup",
            json=doctor_data
        )

        if response.status_code not in [200, 201]:
            logging.error(f"Failed to create doctor: {response.text}")
            return None

        # Get the token from the response
        response_data = response.json()
        user_id = response_data.get("user_id")

        if not user_id:
            logging.error(f"Failed to get user ID: {response_data}")
            return None

        # Get all doctors again to find the newly created one
        response = requests.get(
            DOCTORS_URL,
            headers=headers
        )

        if response.status_code != 200:
            logging.error(f"Failed to get doctors: {response.text}")
            return None

        try:
            doctors = response.json()
            if isinstance(doctors, list):
                for doctor in doctors:
                    if isinstance(doctor, dict) and doctor.get("email") == email:
                        doctor_id = doctor.get("id")
                        if doctor_id:
                            # Map doctor to hospital
                            mapping_data = {
                                "hospital_id": hospital_id,
                                "doctor_id": doctor_id
                            }

                            mapping_response = requests.post(
                                f"{MAPPINGS_URL}/hospital-doctor",
                                json=mapping_data,
                                headers=headers
                            )

                            if mapping_response.status_code not in [200, 201]:
                                logging.error(f"Failed to map doctor to hospital: {mapping_response.text}")
                                # Continue anyway, this is not critical

                            doctor_data["id"] = doctor_id
                            doctor_data["user_id"] = user_id
                            doctor_data["specialization"] = specialization

                            logging.info(f"Created doctor: {name} with ID: {doctor_id}")
                            return doctor_data
        except Exception as e:
            logging.error(f"Error parsing doctors response: {str(e)}")
            return None

        logging.error(f"Failed to find newly created doctor with email: {email}")
        return None
    except Exception as e:
        logging.error(f"Error getting or creating doctor: {str(e)}")
        return None

# Alias for backward compatibility
create_doctor = get_or_create_doctor

def get_or_create_patient(token: str, name: str, email: str, password: str, age: int, gender: str, hospital_id: str) -> Optional[Dict[str, Any]]:
    """Get or create a patient"""
    logging.info(f"Getting or creating patient: {name}...")

    # Get all patients
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # First try to get the patient by email
        response = requests.get(
            PATIENTS_URL,
            headers=headers
        )

        if response.status_code == 200:
            try:
                patients = response.json()
                if isinstance(patients, list):
                    for patient in patients:
                        if isinstance(patient, dict) and patient.get("email") == email:
                            logging.info(f"Found existing patient: {name} with ID: {patient.get('id')}")

                            # Make sure the patient is mapped to the hospital
                            mapping_data = {
                                "hospital_id": hospital_id,
                                "patient_id": patient.get("id")
                            }

                            mapping_response = requests.post(
                                f"{MAPPINGS_URL}/hospital-patient",
                                json=mapping_data,
                                headers=headers
                            )

                            if mapping_response.status_code not in [200, 201]:
                                logging.warning(f"Failed to map patient to hospital: {mapping_response.text}")

                            return patient
            except Exception as e:
                logging.error(f"Error parsing patients response: {str(e)}")
                # Continue with creating a new patient

        # If not found, create a new patient using patient-signup
        logging.info(f"Creating new patient: {name}...")

        # Create patient using patient-signup
        patient_data = {
            "name": name,
            "email": email,
            "password": password,
            "age": age,
            "gender": gender,
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

        if response.status_code not in [200, 201]:
            logging.error(f"Failed to create patient: {response.text}")
            return None

        # Get the token from the response
        response_data = response.json()
        user_id = response_data.get("user_id")

        if not user_id:
            logging.error(f"Failed to get user ID: {response_data}")
            return None

        # Get all patients again to find the newly created one
        response = requests.get(
            PATIENTS_URL,
            headers=headers
        )

        if response.status_code != 200:
            logging.error(f"Failed to get patients: {response.text}")
            return None

        try:
            patients = response.json()
            if isinstance(patients, list):
                for patient in patients:
                    if isinstance(patient, dict) and patient.get("email") == email:
                        patient_id = patient.get("id")
                        if patient_id:
                            # Map patient to hospital
                            mapping_data = {
                                "hospital_id": hospital_id,
                                "patient_id": patient_id
                            }

                            mapping_response = requests.post(
                                f"{MAPPINGS_URL}/hospital-patient",
                                json=mapping_data,
                                headers=headers
                            )

                            if mapping_response.status_code not in [200, 201]:
                                logging.error(f"Failed to map patient to hospital: {mapping_response.text}")
                                # Continue anyway, this is not critical

                            patient_data["id"] = patient_id
                            patient_data["user_id"] = user_id

                            logging.info(f"Created patient: {name} with ID: {patient_id}")
                            return patient_data
        except Exception as e:
            logging.error(f"Error parsing patients response: {str(e)}")
            return None

        logging.error(f"Failed to find newly created patient with email: {email}")
        return None
    except Exception as e:
        logging.error(f"Error getting or creating patient: {str(e)}")
        return None

# Alias for backward compatibility
create_patient = get_or_create_patient

def map_doctor_to_patient(token: str, doctor_id: str, patient_id: str) -> bool:
    """Map a doctor to a patient"""
    logging.info(f"Mapping doctor {doctor_id} to patient {patient_id}...")

    headers = {"Authorization": f"Bearer {token}"}

    mapping_data = {
        "doctor_id": doctor_id,
        "patient_id": patient_id
    }

    try:
        response = requests.post(
            f"{MAPPINGS_URL}/doctor-patient",
            json=mapping_data,
            headers=headers
        )

        if response.status_code not in [200, 201]:
            logging.error(f"Failed to map doctor to patient: {response.text}")
            return False

        logging.info(f"Mapped doctor {doctor_id} to patient {patient_id}")
        return True
    except Exception as e:
        logging.error(f"Error mapping doctor to patient: {str(e)}")
        return False

def create_chat(token: str, doctor_id: str, patient_id: str) -> Optional[Dict[str, Any]]:
    """Create a chat between a doctor and a patient"""
    logging.info(f"Creating chat between doctor {doctor_id} and patient {patient_id}...")

    headers = {"Authorization": f"Bearer {token}"}

    chat_data = {
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "is_active_for_doctor": True,
        "is_active_for_patient": True
    }

    try:
        response = requests.post(
            CHATS_URL,
            json=chat_data,
            headers=headers
        )

        if response.status_code not in [200, 201]:
            logging.error(f"Failed to create chat: {response.text}")
            return None

        chat_id = response.json().get("id")
        logging.info(f"Created chat with ID: {chat_id}")

        return {"id": chat_id, "doctor_id": doctor_id, "patient_id": patient_id}
    except Exception as e:
        logging.error(f"Error creating chat: {str(e)}")
        return None

def send_message(token: str, chat_id: str, sender_id: str, receiver_id: str, message: str) -> Optional[Dict[str, Any]]:
    """Send a message in a chat"""
    logging.info(f"Sending message in chat {chat_id}...")

    headers = {"Authorization": f"Bearer {token}"}

    message_data = {
        "chat_id": chat_id,
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "message": message,
        "message_type": "text"
    }

    try:
        response = requests.post(
            MESSAGES_URL,
            json=message_data,
            headers=headers
        )

        if response.status_code not in [200, 201]:
            logging.error(f"Failed to send message: {response.text}")
            return None

        message_id = response.json().get("id")
        logging.info(f"Sent message with ID: {message_id}")

        return {"id": message_id, "chat_id": chat_id, "message": message}
    except Exception as e:
        logging.error(f"Error sending message: {str(e)}")
        return None

def create_ai_session(token: str, chat_id: str) -> Optional[Dict[str, Any]]:
    """Create an AI assistant session"""
    logging.info(f"Creating AI session for chat {chat_id}...")

    headers = {"Authorization": f"Bearer {token}"}

    session_data = {
        "chat_id": chat_id
    }

    try:
        response = requests.post(
            f"{AI_URL}/sessions",
            json=session_data,
            headers=headers
        )

        if response.status_code not in [200, 201]:
            logging.error(f"Failed to create AI session: {response.text}")
            return None

        session_id = response.json().get("id")
        logging.info(f"Created AI session with ID: {session_id}")

        return {"id": session_id, "chat_id": chat_id}
    except Exception as e:
        logging.error(f"Error creating AI session: {str(e)}")
        return None

def send_ai_message(token: str, session_id: str, message: str) -> Optional[Dict[str, Any]]:
    """Send a message to the AI assistant"""
    logging.info(f"Sending message to AI session {session_id}...")

    headers = {"Authorization": f"Bearer {token}"}

    message_data = {
        "session_id": session_id,
        "message": message
    }

    try:
        response = requests.post(
            f"{AI_URL}/sessions/{session_id}/messages",
            json=message_data,
            headers=headers
        )

        if response.status_code not in [200, 201]:
            logging.error(f"Failed to send message to AI: {response.text}")
            return None

        response_data = response.json()
        logging.info(f"Sent message to AI. Response: {response_data.get('response', '')[:50]}...")

        return response_data
    except Exception as e:
        logging.error(f"Error sending message to AI: {str(e)}")
        return None
