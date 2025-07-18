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
    create_case_history,
    create_patient_report,
    MAPPINGS_URL,
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_ADMIN_PASSWORD
)
import requests

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
        "id": "1",  # Hardcoded ID for Mother & Child Care Hospital
        "name": "Mother & Child Care Hospital",
        "email": "motherchild@example.com",
        "password": "hospital123"
    },
    {
        "id": "2",  # Hardcoded ID for Maternity & Newborn Center
        "name": "Maternity & Newborn Center",
        "email": "maternity@example.com",
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
        "name": "Dr. Priya Patel",
        "email": generate_random_doctor_email("Priya Patel"),
        "password": "doctor123",
        "specialization": "Gynecologist",
        "hospital_index": 0  # Index in the HOSPITALS list
    },
    {
        "name": "Dr. Rajesh Kumar",
        "email": generate_random_doctor_email("Rajesh Kumar"),
        "password": "doctor123",
        "specialization": "Pediatrician",
        "hospital_index": 0
    },
    {
        "name": "Dr. Sunita Mehta",
        "email": generate_random_doctor_email("Sunita Mehta"),
        "password": "doctor123",
        "specialization": "Lactation Expert",
        "hospital_index": 0
    },
    {
        "name": "Dr. Amit Sharma",
        "email": generate_random_doctor_email("Amit Sharma"),
        "password": "doctor123",
        "specialization": "Neonatologist",
        "hospital_index": 1
    },
    {
        "name": "Dr. Kavya Reddy",
        "email": generate_random_doctor_email("Kavya Reddy"),
        "password": "doctor123",
        "specialization": "Dietitian",
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
    },
    # Mother and Newborn care test patients
    {
        "name": "Priya Sharma",
        "email": "mother@example.com",
        "password": "password123",
        "age": 28,
        "gender": "female",
        "blood_group": "O+",
        "height": 165,
        "weight": 68,  # Post-delivery weight
        "allergies": ["None"],
        "medications": ["Prenatal vitamins", "Iron supplements", "Calcium tablets"],
        "conditions": ["Post-delivery recovery", "Breastfeeding"],
        "emergency_contact_name": "Rajesh Sharma (Husband)",
        "emergency_contact_number": "+91-9876543213",
        "hospital_index": 0,
        "doctor_indices": [1, 2],  # Gynecologist and Lactation expert
        "relation": "mother",
        "delivery_date": "2024-06-15",
        "delivery_type": "Normal delivery"
    },
    {
        "name": "Baby Arjun Sharma",
        "email": "child@example.com",
        "password": "password123",
        "age": 0,  # Newborn (in months)
        "gender": "male",
        "blood_group": "O+",
        "height": 50,  # 50cm birth length
        "weight": 3,   # 3.2kg birth weight
        "allergies": ["None known"],
        "medications": ["Vitamin D drops"],
        "conditions": ["Healthy newborn", "Breastfeeding"],
        "emergency_contact_name": "Priya Sharma (Mother)",
        "emergency_contact_number": "+91-9876543212",
        "hospital_index": 0,
        "doctor_indices": [1],  # Pediatrician
        "relation": "child",
        "mother_email": "mother@example.com",
        "birth_date": "2024-06-15",
        "birth_weight": 3200,  # grams
        "birth_length": 50,    # cm
        "gestational_age": "39 weeks"
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
            hospital_id,
            blood_group=patient.get("blood_group", "O+"),
            height=patient.get("height", 170),
            weight=patient.get("weight", 70),
            allergies=patient.get("allergies", ["None"]),
            medications=patient.get("medications", ["None"]),
            conditions=patient.get("conditions", ["None"]),
            emergency_contact_name=patient.get("emergency_contact_name", "Emergency Contact"),
            emergency_contact_number=patient.get("emergency_contact_number", "9876543210")
        )
        if not patient_data:
            logging.error(f"Failed to create patient: {patient['name']}. Continuing with other patients.")
            patient_data_list.append(None)
            continue

        patient_data_list.append(patient_data)
        # Add a small delay to avoid rate limiting
        time.sleep(1)

    # Handle mother-child relationships
    logging.info("Setting up mother-child relationships...")
    mother_patient_data = None
    child_patient_data = None

    # Find mother and child patients
    for i, patient in enumerate(PATIENTS):
        if patient.get("relation") == "mother":
            mother_patient_data = patient_data_list[i]
        elif patient.get("relation") == "child":
            child_patient_data = patient_data_list[i]

    # Create mother-child relationship if both exist
    if mother_patient_data and child_patient_data:
        try:
            # Create user-patient relation mapping (mother -> child)
            relation_data = {
                "user_id": mother_patient_data["user_id"],
                "patient_id": child_patient_data["id"],
                "relation": "child"
            }

            headers = {"Authorization": f"Bearer {admin_token}"}
            response = requests.post(
                f"{MAPPINGS_URL}/user-patient",
                json=relation_data,
                headers=headers
            )

            if response.status_code in [200, 201]:
                logging.info(f"✅ Created mother-child relationship: {mother_patient_data['name']} -> {child_patient_data['name']}")
            else:
                logging.warning(f"Failed to create mother-child relationship: {response.text}")

        except Exception as e:
            logging.error(f"Error creating mother-child relationship: {e}")

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

    # Create case histories and reports for mother and newborn patients
    logging.info("Creating case histories and reports for mother and newborn patients...")

    for i, patient in enumerate(PATIENTS):
        patient_data = patient_data_list[i]
        if not patient_data:
            continue

        # Create case histories with summaries
        if patient.get("relation") == "mother":
            # Mother's post-delivery case history
            case_summary = f"""Post-Delivery Care Summary: 28-year-old female, delivered healthy baby boy on {patient.get('delivery_date', '2024-06-15')} via {patient.get('delivery_type', 'normal delivery')}. Current status: Post-delivery recovery progressing well. Breastfeeding established successfully. Current medications: Prenatal vitamins, Iron supplements, Calcium tablets. No known allergies. Concerns: Post-delivery recovery, breastfeeding support, maternal nutrition. Recommendations: Continue current supplements, adequate rest, proper nutrition for breastfeeding, regular follow-up visits."""
            create_case_history(admin_token, patient_data["id"], case_summary.strip())

            # Mother's reports
            create_patient_report(
                admin_token,
                patient_data["id"],
                "post_delivery",
                "Post-Delivery Health Assessment",
                "Post-delivery recovery excellent. Uterine involution normal. Breastfeeding well established. Hemoglobin: 11.2 g/dL. Blood pressure: 120/80 mmHg. Recommended: Continue iron supplements, adequate nutrition."
            )

            create_patient_report(
                admin_token,
                patient_data["id"],
                "lactation",
                "Breastfeeding Assessment",
                "Breastfeeding established successfully. Good latch observed. Milk supply adequate. No signs of mastitis or nipple trauma. Recommendations: Continue exclusive breastfeeding, proper positioning techniques."
            )

        elif patient.get("relation") == "child":
            # Newborn's case history
            case_summary = f"""Newborn Care Summary: Healthy baby boy born on {patient.get('birth_date', '2024-06-15')} at {patient.get('gestational_age', '39 weeks')} gestation. Birth weight: {patient.get('birth_weight', 3200)}g, Birth length: {patient.get('birth_length', 50)}cm. Current status: Thriving newborn, exclusively breastfed. Current medications: Vitamin D drops as per pediatric guidelines. No known allergies. Concerns: Growth monitoring, feeding patterns, developmental milestones, vaccination schedule. Recommendations: Continue exclusive breastfeeding, regular weight monitoring, follow vaccination schedule, developmental assessments."""
            create_case_history(admin_token, patient_data["id"], case_summary.strip())

            # Newborn's reports
            create_patient_report(
                admin_token,
                patient_data["id"],
                "newborn_screening",
                "Newborn Health Assessment",
                "Healthy newborn male. Birth weight: 3.2kg (appropriate for gestational age). APGAR scores: 9/10. All newborn screening tests normal. Feeding well, good weight gain pattern."
            )

            create_patient_report(
                admin_token,
                patient_data["id"],
                "growth_monitoring",
                "Growth and Development Chart",
                "Current weight: 3.2kg, Length: 50cm, Head circumference: 35cm. Growth parameters within normal percentiles. Developmental milestones appropriate for age."
            )

            create_patient_report(
                admin_token,
                patient_data["id"],
                "vaccination_schedule",
                "Immunization Record",
                "Birth vaccines completed: BCG, Hepatitis B (birth dose). Next due: 6 weeks - DPT, Polio, Hepatitis B, Hib, PCV, Rotavirus vaccines."
            )

        # Add delay between operations
        time.sleep(0.5)

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
