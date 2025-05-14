#!/usr/bin/env python3
import os
import sys
import uuid
from datetime import datetime, timedelta
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.db.database import get_db, engine, Base
from app.models.user import User, UserRole
from app.models.hospital import Hospital
from app.models.doctor import Doctor
from app.models.patient import Patient, Gender
from app.models.mapping import (
    HospitalDoctorMapping,
    HospitalPatientMapping,
    DoctorPatientMapping,
    UserPatientRelation,
    RelationType
)
from app.models.chat import Chat
from app.api.auth import get_password_hash

# Store credentials for output
credentials = {
    "admin": [],
    "hospitals": [],
    "doctors": [],
    "patients": []
}

def clean_db():
    """Drop all tables and recreate them"""
    logger.info("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database cleaned and tables recreated.")

def create_test_data():
    """Create test data with 2 hospitals, 4 users, 2-3 patients per user, and 4-5 doctors"""
    # Get database session
    db = next(get_db())

    try:
        # Create admin user
        admin_id = str(uuid.uuid4())
        admin_password = "admin123"
        admin_user = User(
            id=admin_id,
            email="admin@example.com",
            hashed_password=get_password_hash(admin_password),
            name="Admin User",
            role=UserRole.ADMIN,
            contact="+1234567890",
            address="123 Admin St, Adminville",
            is_active=True
        )
        db.add(admin_user)
        credentials["admin"].append({
            "email": "admin@example.com",
            "password": admin_password,
            "id": admin_id
        })

        # Create 2 hospitals
        hospitals = []
        for i in range(2):
            hospital_id = str(uuid.uuid4())
            hospital_name = f"Hospital {i+1}"
            hospital_email = f"hospital{i+1}@example.com"
            hospital_password = f"hospital{i+1}"

            # Create hospital profile
            hospital = Hospital(
                id=hospital_id,
                name=hospital_name,
                address=f"{100+i} Hospital Ave, Medtown",
                city="Medtown",
                state="Medstate",
                country="Medcountry",
                contact=f"+1555{i}55{i}555",
                pin_code=f"1000{i}",
                email=hospital_email,
                specialities=["Cardiology", "Neurology", "Pediatrics", "Orthopedics"],
                website=f"https://hospital{i+1}.example.com"
            )
            db.add(hospital)

            # Create hospital user
            hospital_user = User(
                id=str(uuid.uuid4()),
                email=hospital_email,
                hashed_password=get_password_hash(hospital_password),
                name=hospital_name,
                role=UserRole.HOSPITAL,
                contact=f"+1555{i}55{i}555",
                address=f"{100+i} Hospital Ave, Medtown",
                profile_id=hospital_id,
                is_active=True
            )
            db.add(hospital_user)

            hospitals.append(hospital)
            credentials["hospitals"].append({
                "email": hospital_email,
                "password": hospital_password,
                "id": hospital_id
            })

        # Create 5 doctors
        doctors = []
        specialties = ["Cardiologist", "Neurologist", "Pediatrician", "Orthopedic Surgeon", "General Practitioner"]
        for i in range(5):
            doctor_id = str(uuid.uuid4())
            doctor_name = f"Dr. {['John', 'Sarah', 'Michael', 'Emily', 'David'][i]} {['Smith', 'Johnson', 'Williams', 'Brown', 'Jones'][i]}"
            doctor_email = f"doctor{i+1}@example.com"
            doctor_password = f"doctor{i+1}"

            # Create doctor profile
            doctor = Doctor(
                id=doctor_id,
                name=doctor_name,
                photo=f"https://example.com/doctors/doctor{i+1}.jpg",
                designation=specialties[i],
                experience=5 + i,
                details=f"Experienced {specialties[i]} with {5+i} years of practice",
                contact=f"+1666{i}66{i}666"
            )
            db.add(doctor)

            # Create doctor user
            doctor_user = User(
                id=str(uuid.uuid4()),
                email=doctor_email,
                hashed_password=get_password_hash(doctor_password),
                name=doctor_name,
                role=UserRole.DOCTOR,
                contact=f"+1666{i}66{i}666",
                profile_id=doctor_id,
                is_active=True
            )
            db.add(doctor_user)

            doctors.append(doctor)
            credentials["doctors"].append({
                "email": doctor_email,
                "password": doctor_password,
                "id": doctor_id,
                "specialty": specialties[i]
            })

            # Map doctors to hospitals
            # First 3 doctors to Hospital 1, last 2 doctors to Hospital 2
            hospital = hospitals[1 if i >= 3 else 0]
            hospital_doctor_mapping = HospitalDoctorMapping(
                id=str(uuid.uuid4()),
                hospital_id=hospital.id,
                doctor_id=doctor_id
            )
            db.add(hospital_doctor_mapping)

        # Create 4 patient users with 2-3 patients each
        for i in range(4):
            patient_user_id = str(uuid.uuid4())
            patient_email = f"patient{i+1}@example.com"
            patient_password = f"patient{i+1}"

            # Create patient user
            patient_user = User(
                id=patient_user_id,
                email=patient_email,
                hashed_password=get_password_hash(patient_password),
                name=f"Patient User {i+1}",
                role=UserRole.PATIENT,
                contact=f"+1777{i}77{i}777",
                address=f"{200+i} Patient St, Patientville",
                is_active=True
            )
            db.add(patient_user)

            # Create 2-3 patients for this user
            num_patients = random.randint(2, 3)
            patient_records = []

            for j in range(num_patients):
                patient_id = str(uuid.uuid4())
                # Make sure we don't go out of bounds with our name arrays
                first_names = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eva', 'Frank', 'Grace', 'Henry', 'Ivy', 'Jack', 'Kate', 'Leo']
                last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Miller', 'Davis', 'Garcia', 'Rodriguez', 'Wilson']
                first_name_idx = (i*3+j) % len(first_names)
                last_name_idx = i % len(last_names)
                patient_name = f"{first_names[first_name_idx]} {last_names[last_name_idx]}"
                gender = random.choice([Gender.MALE, Gender.FEMALE])

                # Create patient profile
                patient = Patient(
                    id=patient_id,
                    name=patient_name,
                    dob=datetime.now() - timedelta(days=365*(20+i+j)),
                    gender=gender,
                    contact=f"+1888{i}{j}8{i}{j}888",
                    photo=f"https://example.com/patients/patient{i+1}_{j+1}.jpg"
                )
                db.add(patient)

                # Create user-patient relation
                relation = UserPatientRelation(
                    id=str(uuid.uuid4()),
                    user_id=patient_user_id,
                    patient_id=patient_id,
                    relation=RelationType.SELF if j == 0 else random.choice([RelationType.CHILD, RelationType.PARENT, RelationType.GUARDIAN, RelationType.FRIEND])
                )
                db.add(relation)

                patient_records.append({
                    "id": patient_id,
                    "name": patient_name,
                    "relation": relation.relation.value
                })

                # Map patients to hospitals and doctors
                # Map to either hospital
                hospital = random.choice(hospitals)
                hospital_patient_mapping = HospitalPatientMapping(
                    id=str(uuid.uuid4()),
                    hospital_id=hospital.id,
                    patient_id=patient_id
                )
                db.add(hospital_patient_mapping)

                # Map to 1-2 doctors
                num_doctors = random.randint(1, 2)
                for _ in range(num_doctors):
                    doctor = random.choice(doctors)
                    doctor_patient_mapping = DoctorPatientMapping(
                        id=str(uuid.uuid4()),
                        doctor_id=doctor.id,
                        patient_id=patient_id
                    )
                    db.add(doctor_patient_mapping)

                    # Create a chat between doctor and patient
                    chat = Chat(
                        id=str(uuid.uuid4()),
                        doctor_id=doctor.id,
                        patient_id=patient_id,
                        is_active=True
                    )
                    db.add(chat)

            credentials["patients"].append({
                "email": patient_email,
                "password": patient_password,
                "id": patient_user_id,
                "patients": patient_records
            })

        # Commit all changes
        db.commit()
        logger.info("Test data created successfully!")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating test data: {e}")
        return False
    finally:
        db.close()

def print_credentials():
    """Print all credentials in a readable format"""
    print("\n=== TEST DATA CREDENTIALS ===\n")

    print("ADMIN:")
    for admin in credentials["admin"]:
        print(f"  Email: {admin['email']}")
        print(f"  Password: {admin['password']}")
        print(f"  ID: {admin['id']}")
        print()

    print("HOSPITALS:")
    for i, hospital in enumerate(credentials["hospitals"]):
        print(f"  Hospital {i+1}:")
        print(f"    Email: {hospital['email']}")
        print(f"    Password: {hospital['password']}")
        print(f"    ID: {hospital['id']}")
        print()

    print("DOCTORS:")
    for i, doctor in enumerate(credentials["doctors"]):
        print(f"  Doctor {i+1} ({doctor['specialty']}):")
        print(f"    Email: {doctor['email']}")
        print(f"    Password: {doctor['password']}")
        print(f"    ID: {doctor['id']}")
        print()

    print("PATIENTS:")
    for i, patient in enumerate(credentials["patients"]):
        print(f"  Patient User {i+1}:")
        print(f"    Email: {patient['email']}")
        print(f"    Password: {patient['password']}")
        print(f"    ID: {patient['id']}")
        print(f"    Associated Patients:")
        for j, p in enumerate(patient["patients"]):
            print(f"      Patient {j+1}: {p['name']} (Relation: {p['relation']}, ID: {p['id']})")
        print()

if __name__ == "__main__":
    # Clean the database first
    clean_db()

    # Create test data
    success = create_test_data()

    if success:
        # Print credentials
        print_credentials()
    else:
        print("Failed to create test data. Check the logs for details.")
