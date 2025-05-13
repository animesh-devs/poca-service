"""
Create Test Data

This script creates test data for the POCA service.
It creates:
- 2 hospitals
- 4 users (2 doctors, 2 patients)
- Maps the doctors and patients to hospitals
"""

import requests
import logging
import sys
import uuid
import time
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# API URLs
BASE_URL = "http://localhost:8002"
AUTH_URL = f"{BASE_URL}/api/v1/auth"
USERS_URL = f"{BASE_URL}/api/v1/users"
HOSPITALS_URL = f"{BASE_URL}/api/v1/hospitals"
MAPPINGS_URL = f"{BASE_URL}/api/v1/mappings"

# Default admin credentials
DEFAULT_ADMIN_EMAIL = "admin@example.com"
DEFAULT_ADMIN_PASSWORD = "admin123"

# Test data
TEST_HOSPITALS = [
    {
        "name": "Test Hospital 1",
        "email": f"test.hospital1.{uuid.uuid4().hex[:8]}@example.com",
        "password": "password123",
        "address": "123 Test Hospital St",
        "city": "Test City",
        "state": "Test State",
        "country": "Test Country",
        "contact": "1234567890",
        "pin_code": "123456",
        "specialities": ["Cardiology", "Neurology"],
        "website": "https://testhospital1.example.com"
    },
    {
        "name": "Test Hospital 2",
        "email": f"test.hospital2.{uuid.uuid4().hex[:8]}@example.com",
        "password": "password123",
        "address": "456 Test Hospital St",
        "city": "Test City",
        "state": "Test State",
        "country": "Test Country",
        "contact": "0987654321",
        "pin_code": "654321",
        "specialities": ["Orthopedics", "Pediatrics"],
        "website": "https://testhospital2.example.com"
    }
]

TEST_DOCTORS = [
    {
        "name": "Dr. Test Doctor 1",
        "email": f"test.doctor1.{uuid.uuid4().hex[:8]}@example.com",
        "password": "password123",
        "speciality": "Cardiology",
        "qualification": "MD",
        "experience": 10,
        "contact": "1111111111",
        "address": "123 Test Doctor St"
    },
    {
        "name": "Dr. Test Doctor 2",
        "email": f"test.doctor2.{uuid.uuid4().hex[:8]}@example.com",
        "password": "password123",
        "speciality": "Neurology",
        "qualification": "MD",
        "experience": 8,
        "contact": "2222222222",
        "address": "456 Test Doctor St"
    },
    {
        "name": "Dr. Test Doctor 3",
        "email": f"test.doctor3.{uuid.uuid4().hex[:8]}@example.com",
        "password": "password123",
        "speciality": "Orthopedics",
        "qualification": "MD",
        "experience": 12,
        "contact": "3333333333",
        "address": "789 Test Doctor St"
    },
    {
        "name": "Dr. Test Doctor 4",
        "email": f"test.doctor4.{uuid.uuid4().hex[:8]}@example.com",
        "password": "password123",
        "speciality": "Pediatrics",
        "qualification": "MD",
        "experience": 5,
        "contact": "4444444444",
        "address": "012 Test Doctor St"
    }
]

TEST_PATIENTS = [
    {
        "name": "Test Patient 1",
        "email": f"test.patient1.{uuid.uuid4().hex[:8]}@example.com",
        "password": "password123",
        "age": 35,
        "gender": "male",
        "blood_group": "A+",
        "contact": "5555555555",
        "address": "123 Test Patient St",
        "emergency_contact": "1111111111"
    },
    {
        "name": "Test Patient 2",
        "email": f"test.patient2.{uuid.uuid4().hex[:8]}@example.com",
        "password": "password123",
        "age": 28,
        "gender": "female",
        "blood_group": "B+",
        "contact": "6666666666",
        "address": "456 Test Patient St",
        "emergency_contact": "2222222222"
    },
    {
        "name": "Test Patient 3",
        "email": f"test.patient3.{uuid.uuid4().hex[:8]}@example.com",
        "password": "password123",
        "age": 42,
        "gender": "male",
        "blood_group": "O+",
        "contact": "7777777777",
        "address": "789 Test Patient St",
        "emergency_contact": "3333333333"
    },
    {
        "name": "Test Patient 4",
        "email": f"test.patient4.{uuid.uuid4().hex[:8]}@example.com",
        "password": "password123",
        "age": 50,
        "gender": "female",
        "blood_group": "AB+",
        "contact": "8888888888",
        "address": "012 Test Patient St",
        "emergency_contact": "4444444444"
    }
]

def get_auth_token(email, password):
    """Get authentication token for a user"""
    logging.info(f"Getting authentication token for {email}...")

    try:
        # OAuth2 form data
        data = {
            "username": email,
            "password": password
        }

        response = requests.post(
            f"{AUTH_URL}/login",
            data=data,  # Use form data instead of JSON
            timeout=5
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

def create_hospital(token, hospital_data):
    """Create a new hospital"""
    logging.info(f"Creating hospital: {hospital_data['name']}...")

    try:
        response = requests.post(
            f"{AUTH_URL}/hospital-signup",
            json=hospital_data,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )

        # Accept both 200 and 201 status codes as success
        if response.status_code in [200, 201]:
            try:
                hospital = response.json()
                # Check if the response contains user_id
                if 'user_id' in hospital:
                    logging.info(f"Created hospital: {hospital_data['name']} with ID: {hospital.get('user_id')}")
                    return hospital
                else:
                    # If user_id is not in the response but we got a success status code,
                    # the hospital was likely created but the response format is different
                    logging.warning(f"Hospital created but response format is unexpected: {response.text}")
                    # Try to extract user_id from the response if possible
                    if isinstance(hospital, dict):
                        for key, value in hospital.items():
                            if 'id' in key.lower() and isinstance(value, str):
                                logging.info(f"Using {key}: {value} as user_id")
                                hospital['user_id'] = value
                                return hospital
                    # If we can't extract a user_id, create a dummy one
                    hospital['user_id'] = str(uuid.uuid4())
                    logging.warning(f"Using generated user_id: {hospital['user_id']}")
                    return hospital
            except ValueError:
                # If the response is not valid JSON but we got a success status code,
                # the hospital was likely created
                logging.warning(f"Hospital created but response is not valid JSON: {response.text}")
                return {
                    "user_id": str(uuid.uuid4()),
                    "name": hospital_data['name'],
                    "email": hospital_data['email']
                }
        else:
            logging.error(f"Failed to create hospital: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error creating hospital: {str(e)}")
        return None

def create_doctor(token, doctor_data):
    """Create a new doctor"""
    logging.info(f"Creating doctor: {doctor_data['name']}...")

    try:
        # Note: token is not used for doctor signup but kept for consistency
        response = requests.post(
            f"{AUTH_URL}/doctor-signup",
            json=doctor_data,
            timeout=5
        )

        # Accept both 200 and 201 status codes as success
        if response.status_code in [200, 201]:
            try:
                doctor = response.json()
                # Check if the response contains user_id
                if 'user_id' in doctor:
                    logging.info(f"Created doctor: {doctor_data['name']} with ID: {doctor.get('user_id')}")
                    return doctor
                else:
                    # If user_id is not in the response but we got a success status code,
                    # the doctor was likely created but the response format is different
                    logging.warning(f"Doctor created but response format is unexpected: {response.text}")
                    # Try to extract user_id from the response if possible
                    if isinstance(doctor, dict):
                        for key, value in doctor.items():
                            if 'id' in key.lower() and isinstance(value, str):
                                logging.info(f"Using {key}: {value} as user_id")
                                doctor['user_id'] = value
                                return doctor
                    # If we can't extract a user_id, create a dummy one
                    doctor['user_id'] = str(uuid.uuid4())
                    logging.warning(f"Using generated user_id: {doctor['user_id']}")
                    return doctor
            except ValueError:
                # If the response is not valid JSON but we got a success status code,
                # the doctor was likely created
                logging.warning(f"Doctor created but response is not valid JSON: {response.text}")
                return {
                    "user_id": str(uuid.uuid4()),
                    "name": doctor_data['name'],
                    "email": doctor_data['email']
                }
        else:
            logging.error(f"Failed to create doctor: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error creating doctor: {str(e)}")
        return None

def create_patient(token, patient_data):
    """Create a new patient"""
    logging.info(f"Creating patient: {patient_data['name']}...")

    try:
        # Note: token is not used for patient signup but kept for consistency
        response = requests.post(
            f"{AUTH_URL}/patient-signup",
            json=patient_data,
            timeout=5
        )

        # Accept both 200 and 201 status codes as success
        if response.status_code in [200, 201]:
            try:
                patient = response.json()
                # Check if the response contains user_id
                if 'user_id' in patient:
                    logging.info(f"Created patient: {patient_data['name']} with ID: {patient.get('user_id')}")
                    return patient
                else:
                    # If user_id is not in the response but we got a success status code,
                    # the patient was likely created but the response format is different
                    logging.warning(f"Patient created but response format is unexpected: {response.text}")
                    # Try to extract user_id from the response if possible
                    if isinstance(patient, dict):
                        for key, value in patient.items():
                            if 'id' in key.lower() and isinstance(value, str):
                                logging.info(f"Using {key}: {value} as user_id")
                                patient['user_id'] = value
                                return patient
                    # If we can't extract a user_id, create a dummy one
                    patient['user_id'] = str(uuid.uuid4())
                    logging.warning(f"Using generated user_id: {patient['user_id']}")
                    return patient
            except ValueError:
                # If the response is not valid JSON but we got a success status code,
                # the patient was likely created
                logging.warning(f"Patient created but response is not valid JSON: {response.text}")
                return {
                    "user_id": str(uuid.uuid4()),
                    "name": patient_data['name'],
                    "email": patient_data['email']
                }
        else:
            logging.error(f"Failed to create patient: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error creating patient: {str(e)}")
        return None

def get_doctor_by_user_id(token, user_id):
    """Get doctor by user ID"""
    logging.info(f"Getting doctor with user ID: {user_id}...")

    try:
        # First, get the user to check if it's a doctor
        response = requests.get(
            f"{USERS_URL}/{user_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )

        if response.status_code == 200:
            user = response.json()
            logging.info(f"Got user: {user.get('name')}")

            # Check if the user is a doctor
            if user.get('role') != 'doctor':
                logging.error(f"User {user_id} is not a doctor")
                return None

            # Get the doctor profile ID
            profile_id = user.get('profile_id')
            if not profile_id:
                # If profile_id is not directly available, we'll use the user_id as the doctor_id
                logging.warning(f"User {user_id} has no profile_id, using user_id as doctor_id")
                profile_id = user_id

            return {"id": profile_id, "user_id": user_id, "name": user.get('name')}
        else:
            logging.error(f"Failed to get user: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting user: {str(e)}")
        return None

def get_patient_by_user_id(token, user_id):
    """Get patient by user ID"""
    logging.info(f"Getting patient with user ID: {user_id}...")

    try:
        # First, get the user to check if it's a patient
        response = requests.get(
            f"{USERS_URL}/{user_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )

        if response.status_code == 200:
            user = response.json()
            logging.info(f"Got user: {user.get('name')}")

            # Check if the user is a patient
            if user.get('role') != 'patient':
                logging.error(f"User {user_id} is not a patient")
                return None

            # Get the patient profile ID
            profile_id = user.get('profile_id')
            if not profile_id:
                # If profile_id is not directly available, we'll use the user_id as the patient_id
                logging.warning(f"User {user_id} has no profile_id, using user_id as patient_id")
                profile_id = user_id

            return {"id": profile_id, "user_id": user_id, "name": user.get('name')}
        else:
            logging.error(f"Failed to get user: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting user: {str(e)}")
        return None

def get_hospital_by_user_id(token, user_id):
    """Get hospital by user ID"""
    logging.info(f"Getting hospital with user ID: {user_id}...")

    try:
        # First, get the user to check if it's a hospital
        response = requests.get(
            f"{USERS_URL}/{user_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )

        if response.status_code == 200:
            user = response.json()
            logging.info(f"Got user: {user.get('name')}")

            # Check if the user is a hospital
            if user.get('role') != 'hospital':
                logging.error(f"User {user_id} is not a hospital")
                return None

            # Get the hospital profile ID
            profile_id = user.get('profile_id')
            if not profile_id:
                # If profile_id is not directly available, we'll use the user_id as the hospital_id
                logging.warning(f"User {user_id} has no profile_id, using user_id as hospital_id")
                profile_id = user_id

            return {"id": profile_id, "user_id": user_id, "name": user.get('name')}
        else:
            logging.error(f"Failed to get user: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting user: {str(e)}")
        return None

def map_hospital_to_doctor(token, hospital_id, doctor_id):
    """Map a hospital to a doctor"""
    logging.info(f"Mapping hospital {hospital_id} to doctor {doctor_id}...")

    try:
        mapping_data = {
            "hospital_id": hospital_id,
            "doctor_id": doctor_id
        }

        response = requests.post(
            f"{MAPPINGS_URL}/hospital-doctor",
            json=mapping_data,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )

        # Accept both 200 and 201 status codes as success
        if response.status_code in [200, 201]:
            mapping = response.json()
            logging.info(f"Mapped hospital {hospital_id} to doctor {doctor_id}")
            return mapping
        # If the mapping already exists, consider it a success
        elif response.status_code == 400 and "already exists" in response.text.lower():
            logging.info(f"Mapping between hospital {hospital_id} and doctor {doctor_id} already exists")
            return {"hospital_id": hospital_id, "doctor_id": doctor_id, "status": "already_exists"}
        else:
            logging.error(f"Failed to map hospital to doctor: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error mapping hospital to doctor: {str(e)}")
        return None

def map_hospital_to_patient(token, hospital_id, patient_id):
    """Map a hospital to a patient"""
    logging.info(f"Mapping hospital {hospital_id} to patient {patient_id}...")

    try:
        mapping_data = {
            "hospital_id": hospital_id,
            "patient_id": patient_id
        }

        response = requests.post(
            f"{MAPPINGS_URL}/hospital-patient",
            json=mapping_data,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )

        # Accept both 200 and 201 status codes as success
        if response.status_code in [200, 201]:
            mapping = response.json()
            logging.info(f"Mapped hospital {hospital_id} to patient {patient_id}")
            return mapping
        # If the mapping already exists, consider it a success
        elif response.status_code == 400 and "already exists" in response.text.lower():
            logging.info(f"Mapping between hospital {hospital_id} and patient {patient_id} already exists")
            return {"hospital_id": hospital_id, "patient_id": patient_id, "status": "already_exists"}
        else:
            logging.error(f"Failed to map hospital to patient: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error mapping hospital to patient: {str(e)}")
        return None

def map_doctor_to_patient(token, doctor_id, patient_id):
    """Map a doctor to a patient"""
    logging.info(f"Mapping doctor {doctor_id} to patient {patient_id}...")

    try:
        mapping_data = {
            "doctor_id": doctor_id,
            "patient_id": patient_id
        }

        response = requests.post(
            f"{MAPPINGS_URL}/doctor-patient",
            json=mapping_data,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )

        # Accept both 200 and 201 status codes as success
        if response.status_code in [200, 201]:
            mapping = response.json()
            logging.info(f"Mapped doctor {doctor_id} to patient {patient_id}")
            return mapping
        # If the mapping already exists, consider it a success
        elif response.status_code == 400 and "already exists" in response.text.lower():
            logging.info(f"Mapping between doctor {doctor_id} and patient {patient_id} already exists")
            return {"doctor_id": doctor_id, "patient_id": patient_id, "status": "already_exists"}
        else:
            logging.error(f"Failed to map doctor to patient: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error mapping doctor to patient: {str(e)}")
        return None

def check_server_health():
    """Check if the server is running and healthy"""
    logging.info("Checking server health...")

    try:
        # Try the health endpoint first
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            logging.info("Server is up and running (health endpoint)")
            return True
        else:
            logging.warning(f"Health endpoint check failed: {response.text}")
    except Exception as e:
        logging.warning(f"Health endpoint check failed: {str(e)}")

    try:
        # Try the auth endpoint as a fallback
        response = requests.post(f"{AUTH_URL}/login", timeout=5)
        if response.status_code in [400, 401, 422]:  # These are expected errors for invalid login
            logging.info("Server is up and running (auth endpoint)")
            return True
        else:
            logging.warning(f"Auth endpoint check failed: {response.text}")
    except Exception as e:
        logging.warning(f"Auth endpoint check failed: {str(e)}")

    try:
        # Try the root endpoint as a last resort
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            logging.info("Server is up and running (root endpoint)")
            return True
        else:
            logging.error(f"Server health check failed: {response.text}")
    except Exception as e:
        logging.error(f"Server health check failed: {str(e)}")

    return False

def main():
    """Main function to create test data"""
    print("Creating test data for POCA service...")

    # Check if the server is running
    if not check_server_health():
        logging.error("Server is not running. Please start the server and try again.")
        return

    # Get admin token
    admin_token_data = get_auth_token(DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD)
    if not admin_token_data:
        logging.error("Failed to get admin token. Aborting.")
        return

    admin_token = admin_token_data["access_token"]

    # Create hospitals
    hospitals = []
    for hospital_data in TEST_HOSPITALS:
        hospital = create_hospital(admin_token, hospital_data)
        if hospital:
            hospitals.append({
                "data": hospital,
                "email": hospital_data["email"],
                "password": hospital_data["password"]
            })

    # Create doctors
    doctors = []
    for doctor_data in TEST_DOCTORS:
        doctor = create_doctor(admin_token, doctor_data)
        if doctor:
            doctors.append({
                "data": doctor,
                "email": doctor_data["email"],
                "password": doctor_data["password"]
            })

    # Create patients
    patients = []
    for patient_data in TEST_PATIENTS:
        patient = create_patient(admin_token, patient_data)
        if patient:
            patients.append({
                "data": patient,
                "email": patient_data["email"],
                "password": patient_data["password"]
            })

    # Wait a bit for the data to be fully processed
    time.sleep(2)

    # Get the profile IDs
    hospital_profiles = []
    for hospital in hospitals:
        profile = get_hospital_by_user_id(admin_token, hospital["data"]["user_id"])
        if profile:
            hospital_profiles.append(profile)

    doctor_profiles = []
    for doctor in doctors:
        profile = get_doctor_by_user_id(admin_token, doctor["data"]["user_id"])
        if profile:
            doctor_profiles.append(profile)

    patient_profiles = []
    for patient in patients:
        profile = get_patient_by_user_id(admin_token, patient["data"]["user_id"])
        if profile:
            patient_profiles.append(profile)

    # Create mappings
    # Map each doctor to hospital 1 or 2
    for i, doctor in enumerate(doctor_profiles):
        hospital = hospital_profiles[i % len(hospital_profiles)]
        map_hospital_to_doctor(admin_token, hospital["id"], doctor["id"])

    # Map each patient to hospital 1 or 2
    for i, patient in enumerate(patient_profiles):
        hospital = hospital_profiles[i % len(hospital_profiles)]
        map_hospital_to_patient(admin_token, hospital["id"], patient["id"])

    # Map each patient to 1-2 doctors
    for i, patient in enumerate(patient_profiles):
        # Map to primary doctor
        doctor1 = doctor_profiles[i % len(doctor_profiles)]
        map_doctor_to_patient(admin_token, doctor1["id"], patient["id"])

        # Map to secondary doctor
        doctor2 = doctor_profiles[(i + 1) % len(doctor_profiles)]
        map_doctor_to_patient(admin_token, doctor2["id"], patient["id"])

    # Save the created data to a file for reference
    with open("test_data.txt", "w") as f:
        f.write("Test Hospitals:\n")
        for i, hospital in enumerate(hospitals):
            f.write(f"{i+1}. {hospital['data']['user_id']} - {hospital['email']} - {hospital['password']}\n")
            if i < len(hospital_profiles):
                f.write(f"   Profile ID: {hospital_profiles[i]['id']}\n")

        f.write("\nTest Doctors:\n")
        for i, doctor in enumerate(doctors):
            f.write(f"{i+1}. {doctor['data']['user_id']} - {doctor['email']} - {doctor['password']}\n")
            if i < len(doctor_profiles):
                f.write(f"   Profile ID: {doctor_profiles[i]['id']}\n")

        f.write("\nTest Patients:\n")
        for i, patient in enumerate(patients):
            f.write(f"{i+1}. {patient['data']['user_id']} - {patient['email']} - {patient['password']}\n")
            if i < len(patient_profiles):
                f.write(f"   Profile ID: {patient_profiles[i]['id']}\n")

    print("Test data creation completed!")
    print("Check test_data.txt for details of the created entities.")

if __name__ == "__main__":
    main()
