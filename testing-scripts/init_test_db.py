import argparse
import uuid
import os
import sys
from datetime import datetime, timedelta

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import get_db
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

def init_test_data():
    """Initialize the database with test data"""
    # Get database session
    db = next(get_db())

    try:
        # Create hospital
        hospital_id = str(uuid.uuid4())
        hospital = Hospital(
            id=hospital_id,
            name="General Hospital",
            address="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            contact="+1234567890",
            pin_code="10001",
            email="hospital@example.com",
            specialities=["Cardiology", "Neurology", "Pediatrics"],
            website="https://hospital.example.com"
        )
        db.add(hospital)
        db.commit()

        # Create hospital user
        hospital_user_id = str(uuid.uuid4())
        hospital_user = User(
            id=hospital_user_id,
            email="hospital@example.com",
            hashed_password=get_password_hash("hospital123"),
            name="General Hospital",
            role=UserRole.HOSPITAL,
            contact="+1234567890",
            address="123 Main St",
            profile_id=hospital_id,
            is_active=True
        )
        db.add(hospital_user)
        db.commit()

        # Create doctors
        # 1. Cardiologist
        cardio_id = str(uuid.uuid4())
        cardio = Doctor(
            id=cardio_id,
            name="Dr. John Smith",
            photo="https://example.com/doctor1.jpg",
            designation="Senior Cardiologist",
            experience=15,
            details="MD, Cardiology, Harvard Medical School",
            contact="+1234567891"
        )
        db.add(cardio)
        db.commit()

        cardio_user_id = str(uuid.uuid4())
        cardio_user = User(
            id=cardio_user_id,
            email="doctor.cardio@example.com",
            hashed_password=get_password_hash("doctor123"),
            name="Dr. John Smith",
            role=UserRole.DOCTOR,
            contact="+1234567891",
            profile_id=cardio_id,
            is_active=True
        )
        db.add(cardio_user)
        db.commit()

        # 2. Neurologist
        neuro_id = str(uuid.uuid4())
        neuro = Doctor(
            id=neuro_id,
            name="Dr. Sarah Johnson",
            photo="https://example.com/doctor2.jpg",
            designation="Neurologist",
            experience=10,
            details="MD, Neurology, Johns Hopkins",
            contact="+1234567892"
        )
        db.add(neuro)
        db.commit()

        neuro_user_id = str(uuid.uuid4())
        neuro_user = User(
            id=neuro_user_id,
            email="doctor.neuro@example.com",
            hashed_password=get_password_hash("doctor123"),
            name="Dr. Sarah Johnson",
            role=UserRole.DOCTOR,
            contact="+1234567892",
            profile_id=neuro_id,
            is_active=True
        )
        db.add(neuro_user)
        db.commit()

        # Create patients
        # 1. Adult Patient
        adult_id = str(uuid.uuid4())
        adult = Patient(
            id=adult_id,
            name="Jane Doe",
            dob=datetime.now() - timedelta(days=365*35),
            gender=Gender.FEMALE,
            contact="+1234567893",
            photo="https://example.com/patient1.jpg"
        )
        db.add(adult)
        db.commit()

        adult_user_id = str(uuid.uuid4())
        adult_user = User(
            id=adult_user_id,
            email="patient.adult@example.com",
            hashed_password=get_password_hash("patient123"),
            name="Jane Doe",
            role=UserRole.PATIENT,
            contact="+1234567893",
            profile_id=adult_id,
            is_active=True
        )
        db.add(adult_user)
        db.commit()

        # 2. Child Patient
        child_id = str(uuid.uuid4())
        child = Patient(
            id=child_id,
            name="Tommy Doe",
            dob=datetime.now() - timedelta(days=365*8),
            gender=Gender.MALE,
            contact="+1234567894",
            photo="https://example.com/patient2.jpg"
        )
        db.add(child)
        db.commit()

        # Create mappings
        # Hospital-Doctor mappings
        hospital_cardio = HospitalDoctorMapping(
            hospital_id=hospital_id,
            doctor_id=cardio_id
        )
        db.add(hospital_cardio)

        hospital_neuro = HospitalDoctorMapping(
            hospital_id=hospital_id,
            doctor_id=neuro_id
        )
        db.add(hospital_neuro)

        # Hospital-Patient mappings
        hospital_adult = HospitalPatientMapping(
            hospital_id=hospital_id,
            patient_id=adult_id
        )
        db.add(hospital_adult)

        hospital_child = HospitalPatientMapping(
            hospital_id=hospital_id,
            patient_id=child_id
        )
        db.add(hospital_child)

        # Doctor-Patient mappings
        cardio_adult = DoctorPatientMapping(
            doctor_id=cardio_id,
            patient_id=adult_id
        )
        db.add(cardio_adult)

        neuro_child = DoctorPatientMapping(
            doctor_id=neuro_id,
            patient_id=child_id
        )
        db.add(neuro_child)

        # User-Patient relations
        adult_relation = UserPatientRelation(
            user_id=adult_user_id,
            patient_id=adult_id,
            relation=RelationType.SELF
        )
        db.add(adult_relation)

        child_relation = UserPatientRelation(
            user_id=adult_user_id,
            patient_id=child_id,
            relation=RelationType.CHILD
        )
        db.add(child_relation)

        # Create chat sessions
        cardio_adult_chat = Chat(
            doctor_id=cardio_id,
            patient_id=adult_id,
            is_active_for_doctor=True,
            is_active_for_patient=True
        )
        db.add(cardio_adult_chat)

        neuro_child_chat = Chat(
            doctor_id=neuro_id,
            patient_id=child_id,
            is_active_for_doctor=True,
            is_active_for_patient=True
        )
        db.add(neuro_child_chat)

        db.commit()

        print("Test data initialized successfully!")
        print("\nTest Users:")
        print("Admin: admin@example.com / admin123")
        print("Hospital: hospital@example.com / hospital123")
        print("Doctor (Cardiologist): doctor.cardio@example.com / doctor123")
        print("Doctor (Neurologist): doctor.neuro@example.com / doctor123")
        print("Patient (Adult): patient.adult@example.com / patient123")

        return True
    except Exception as e:
        db.rollback()
        print(f"Error creating test data: {e}")
        return False
    finally:
        db.close()

def main():
    """Main function to initialize test data"""
    parser = argparse.ArgumentParser(description="Initialize test data for POCA Service")
    args = parser.parse_args()

    # Initialize test data
    init_test_data()

if __name__ == "__main__":
    main()
