#!/usr/bin/env python3
"""
Create Test Data

This script creates comprehensive test data for the POCA service.
It creates hospitals, doctors, patients, and maps them together.
"""

import sys
import logging
import time

# Import helper functions
from api_helpers import (
    check_server_health,
    get_auth_token,
    get_or_create_doctor,
    get_or_create_patient,
    map_doctor_to_patient,
    create_chat,
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_ADMIN_PASSWORD
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Test data
import random
import string

def generate_random_email(prefix):
    """Generate a random email address"""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}.{random_str}@hospital.com"

# Use hardcoded hospital IDs
HOSPITALS = [
    {
        "id": "1",  # Hardcoded ID for General Hospital
        "name": "General Hospital",
        "email": "general@example.com",
        "password": "hospital123"
    },
    {
        "id": "2",  # Hardcoded ID for City Medical Center
        "name": "City Medical Center",
        "email": "city@example.com",
        "password": "hospital123"
    }
]

def generate_random_doctor_email(name):
    """Generate a random doctor email address"""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    name_part = name.lower().replace(' ', '.').replace('.', '')
    return f"{name_part}.{random_str}@doctor.com"

DOCTORS = [
    {
        "name": "Dr. John Smith",
        "email": generate_random_doctor_email("John Smith"),
        "password": "doctor123",
        "specialization": "Cardiology",
        "hospital_index": 0  # Index in the HOSPITALS list
    },
    {
        "name": "Dr. Sarah Johnson",
        "email": generate_random_doctor_email("Sarah Johnson"),
        "password": "doctor123",
        "specialization": "Neurology",
        "hospital_index": 0
    },
    {
        "name": "Dr. Michael Brown",
        "email": generate_random_doctor_email("Michael Brown"),
        "password": "doctor123",
        "specialization": "Pediatrics",
        "hospital_index": 1
    },
    {
        "name": "Dr. Emily Davis",
        "email": generate_random_doctor_email("Emily Davis"),
        "password": "doctor123",
        "specialization": "Dermatology",
        "hospital_index": 1
    }
]

def generate_random_patient_email(name):
    """Generate a random patient email address"""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    name_part = name.lower().replace(' ', '.').replace('.', '')
    return f"{name_part}.{random_str}@patient.com"

PATIENTS = [
    {
        "name": "Alice Williams",
        "email": generate_random_patient_email("Alice Williams"),
        "password": "patient123",
        "age": 35,
        "gender": "female",
        "hospital_index": 0,  # Index in the HOSPITALS list
        "doctor_indices": [0, 1]  # Indices in the DOCTORS list
    },
    {
        "name": "Bob Johnson",
        "email": generate_random_patient_email("Bob Johnson"),
        "password": "patient123",
        "age": 45,
        "gender": "male",
        "hospital_index": 0,
        "doctor_indices": [0]
    },
    {
        "name": "Charlie Brown",
        "email": generate_random_patient_email("Charlie Brown"),
        "password": "patient123",
        "age": 28,
        "gender": "male",
        "hospital_index": 1,
        "doctor_indices": [2, 3]
    },
    {
        "name": "Diana Miller",
        "email": generate_random_patient_email("Diana Miller"),
        "password": "patient123",
        "age": 52,
        "gender": "female",
        "hospital_index": 1,
        "doctor_indices": [2]
    },
    {
        "name": "Ethan Davis",
        "email": generate_random_patient_email("Ethan Davis"),
        "password": "patient123",
        "age": 8,
        "gender": "male",
        "hospital_index": 0,
        "doctor_indices": [1]
    },
    {
        "name": "Fiona Wilson",
        "email": generate_random_patient_email("Fiona Wilson"),
        "password": "patient123",
        "age": 15,
        "gender": "female",
        "hospital_index": 1,
        "doctor_indices": [2, 3]
    }
]

def create_test_data():
    """Create comprehensive test data"""
    print("Creating comprehensive test data for POCA service...")
    print("This may take a few minutes...")

    # Check if the server is up
    if not check_server_health():
        logging.error("Server is not running. Please start the server and try again.")
        return False

    # Get admin token
    admin_token_data = get_auth_token(DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD)
    if not admin_token_data:
        logging.error("Failed to get admin token. Aborting test data creation.")
        return False

    admin_token = admin_token_data["access_token"]

    # Use hardcoded hospital IDs
    hospital_data_list = HOSPITALS

    # Create doctors
    doctor_data_list = []
    for doctor in DOCTORS:
        hospital_index = doctor["hospital_index"]
        if hospital_index >= len(hospital_data_list) or hospital_data_list[hospital_index] is None:
            logging.error(f"Hospital index {hospital_index} is invalid for doctor {doctor['name']}. Skipping.")
            doctor_data_list.append(None)
            continue

        hospital_id = hospital_data_list[hospital_index]["id"]
        doctor_data = get_or_create_doctor(
            admin_token,
            doctor["name"],
            doctor["email"],
            doctor["password"],
            doctor["specialization"],
            hospital_id
        )
        if not doctor_data:
            logging.error(f"Failed to create doctor: {doctor['name']}. Continuing with other doctors.")
            doctor_data_list.append(None)
            continue

        doctor_data_list.append(doctor_data)
        # Add a small delay to avoid rate limiting
        time.sleep(1)

    # Create patients
    patient_data_list = []
    for patient in PATIENTS:
        hospital_index = patient["hospital_index"]
        if hospital_index >= len(hospital_data_list) or hospital_data_list[hospital_index] is None:
            logging.error(f"Hospital index {hospital_index} is invalid for patient {patient['name']}. Skipping.")
            patient_data_list.append(None)
            continue

        hospital_id = hospital_data_list[hospital_index]["id"]
        patient_data = get_or_create_patient(
            admin_token,
            patient["name"],
            patient["email"],
            patient["password"],
            patient["age"],
            patient["gender"],
            hospital_id
        )
        if not patient_data:
            logging.error(f"Failed to create patient: {patient['name']}. Continuing with other patients.")
            patient_data_list.append(None)
            continue

        patient_data_list.append(patient_data)
        # Add a small delay to avoid rate limiting
        time.sleep(1)

    # Map doctors to patients
    for i, patient in enumerate(PATIENTS):
        if i >= len(patient_data_list) or patient_data_list[i] is None:
            continue

        patient_id = patient_data_list[i]["id"]
        for doctor_index in patient["doctor_indices"]:
            if doctor_index >= len(doctor_data_list) or doctor_data_list[doctor_index] is None:
                logging.error(f"Doctor index {doctor_index} is invalid for patient {patient['name']}. Skipping.")
                continue

            doctor_id = doctor_data_list[doctor_index]["id"]
            if not map_doctor_to_patient(admin_token, doctor_id, patient_id):
                logging.error(f"Failed to map doctor {doctor_id} to patient {patient_id}. Continuing.")

            # Create a chat between the doctor and patient
            chat_data = create_chat(admin_token, doctor_id, patient_id)
            if not chat_data:
                logging.error(f"Failed to create chat between doctor {doctor_id} and patient {patient_id}. Continuing.")

            # Add a small delay to avoid rate limiting
            time.sleep(1)

    # Print summary
    print("\nTest data creation completed!")
    print("\nCreated Hospitals:")
    for i, hospital_data in enumerate(hospital_data_list):
        if hospital_data:
            print(f"  {i+1}. {hospital_data['name']} (Email: {hospital_data['email']}, Password: {HOSPITALS[i]['password']})")

    print("\nCreated Doctors:")
    for i, doctor_data in enumerate(doctor_data_list):
        if doctor_data:
            print(f"  {i+1}. {doctor_data['name']} - {doctor_data['specialization']} (Email: {doctor_data['email']}, Password: {DOCTORS[i]['password']})")

    print("\nCreated Patients:")
    for i, patient_data in enumerate(patient_data_list):
        if patient_data:
            print(f"  {i+1}. {patient_data['name']} - {PATIENTS[i]['age']} years old (Email: {patient_data['email']}, Password: {PATIENTS[i]['password']})")

    print("\nYou can now use these users to test the application.")
    return True

if __name__ == "__main__":
    create_test_data()
