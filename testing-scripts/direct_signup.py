#!/usr/bin/env python3
"""
Direct Signup Script

This script creates test data for the POCA service by directly using the signup endpoints.
It creates hospitals, doctors, and patients without trying to map them together.
"""

import sys
import logging
import time
import requests
import random
import string

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

# Test data
def generate_random_email(prefix):
    """Generate a random email address"""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}.{random_str}@example.com"

# Hospitals
HOSPITALS = [
    {
        "name": "General Hospital",
        "email": generate_random_email("general"),
        "password": "hospital123"
    },
    {
        "name": "City Medical Center",
        "email": generate_random_email("city"),
        "password": "hospital123"
    }
]

# Doctors
DOCTORS = [
    {
        "name": "Dr. John Smith",
        "email": generate_random_email("john.smith"),
        "password": "doctor123",
        "specialization": "Cardiology"
    },
    {
        "name": "Dr. Sarah Johnson",
        "email": generate_random_email("sarah.johnson"),
        "password": "doctor123",
        "specialization": "Neurology"
    },
    {
        "name": "Dr. Michael Brown",
        "email": generate_random_email("michael.brown"),
        "password": "doctor123",
        "specialization": "Pediatrics"
    },
    {
        "name": "Dr. Emily Davis",
        "email": generate_random_email("emily.davis"),
        "password": "doctor123",
        "specialization": "Dermatology"
    }
]

# Patients
PATIENTS = [
    {
        "name": "Alice Williams",
        "email": generate_random_email("alice.williams"),
        "password": "patient123",
        "age": 35,
        "gender": "female"
    },
    {
        "name": "Bob Johnson",
        "email": generate_random_email("bob.johnson"),
        "password": "patient123",
        "age": 45,
        "gender": "male"
    },
    {
        "name": "Charlie Brown",
        "email": generate_random_email("charlie.brown"),
        "password": "patient123",
        "age": 28,
        "gender": "male"
    },
    {
        "name": "Diana Miller",
        "email": generate_random_email("diana.miller"),
        "password": "patient123",
        "age": 52,
        "gender": "female"
    },
    {
        "name": "Ethan Davis",
        "email": generate_random_email("ethan.davis"),
        "password": "patient123",
        "age": 8,
        "gender": "male"
    },
    {
        "name": "Fiona Wilson",
        "email": generate_random_email("fiona.wilson"),
        "password": "patient123",
        "age": 15,
        "gender": "female"
    }
]

def check_server_health():
    """Check if the server is up and running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Error checking server health: {str(e)}")
        return False

def create_test_data():
    """Create comprehensive test data"""
    print("Creating comprehensive test data for POCA service...")
    print("This may take a few minutes...")

    # Check if server is running
    if not check_server_health():
        print("Server is not running. Please start the server first.")
        return

    # Create hospitals
    hospital_data_list = []
    for hospital in HOSPITALS:
        # Create hospital using hospital-signup
        hospital_data = {
            "name": hospital["name"],
            "address": f"{hospital['name']} Address, Main Street",
            "city": "Test City",
            "state": "Test State",
            "country": "Test Country",
            "contact": "1234567890",
            "pin_code": "12345",
            "email": hospital["email"],
            "password": hospital["password"],
            "specialities": ["Cardiology", "Neurology", "Pediatrics"],
            "website": f"https://{hospital['name'].lower().replace(' ', '')}.example.com"
        }

        response = requests.post(
            f"{AUTH_URL}/hospital-signup",
            json=hospital_data
        )

        if response.status_code not in [200, 201]:
            logging.error(f"Failed to create hospital: {hospital['name']} - {response.text}")
            continue

        hospital_data_list.append(hospital_data)
        print(f"Created hospital: {hospital['name']} with email: {hospital['email']}")
        
        # Add a small delay to avoid rate limiting
        time.sleep(1)
    
    # Create doctors
    doctor_data_list = []
    for doctor in DOCTORS:
        # Create doctor using doctor-signup
        doctor_data = {
            "name": doctor["name"],
            "email": doctor["email"],
            "password": doctor["password"],
            "photo": f"https://example.com/{doctor['name'].lower().replace(' ', '')}.jpg",
            "designation": f"Senior {doctor['specialization']}",
            "experience": 10,
            "details": f"MD, {doctor['specialization']}, Medical University",
            "contact": "1234567890",
            "address": "123 Doctor St"
        }

        response = requests.post(
            f"{AUTH_URL}/doctor-signup",
            json=doctor_data
        )

        if response.status_code not in [200, 201]:
            logging.error(f"Failed to create doctor: {doctor['name']} - {response.text}")
            continue

        doctor_data_list.append(doctor_data)
        print(f"Created doctor: {doctor['name']} with email: {doctor['email']}")
        
        # Add a small delay to avoid rate limiting
        time.sleep(1)

    # Create patients
    patient_data_list = []
    for patient in PATIENTS:
        # Create patient using patient-signup
        patient_data = {
            "name": patient["name"],
            "email": patient["email"],
            "password": patient["password"],
            "age": patient["age"],
            "gender": patient["gender"],
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
            logging.error(f"Failed to create patient: {patient['name']} - {response.text}")
            continue

        patient_data_list.append(patient_data)
        print(f"Created patient: {patient['name']} with email: {patient['email']}")
        
        # Add a small delay to avoid rate limiting
        time.sleep(1)

    # Print summary
    print("\nTest data creation completed!")
    print("\nCreated Hospitals:")
    for hospital in hospital_data_list:
        print(f"- {hospital['name']} (Email: {hospital['email']}, Password: {hospital['password']})")
    
    print("\nCreated Doctors:")
    for doctor in doctor_data_list:
        print(f"- {doctor['name']} (Email: {doctor['email']}, Password: {doctor['password']})")
    
    print("\nCreated Patients:")
    for patient in patient_data_list:
        print(f"- {patient['name']} (Email: {patient['email']}, Password: {patient['password']})")
    
    print("\nYou can now use these users to test the application.")

if __name__ == "__main__":
    create_test_data()
