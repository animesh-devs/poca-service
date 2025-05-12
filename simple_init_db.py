import os
import logging
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from uuid import uuid4

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import database and models
from app.db.database import engine, Base, get_db
from app.models.user import User, UserRole
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.hospital import Hospital
from app.models.mapping import HospitalDoctorMapping, HospitalPatientMapping, DoctorPatientMapping
from app.models.chat import Chat
from app.models.ai import AISession, AIMessage

# Create tables
def create_tables():
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")

# Create test data
def create_test_data():
    logger.info("Creating test data...")

    # Get database session
    db = next(get_db())

    try:
        # Create admin user
        admin_user = User(
            id=str(uuid4()),
            email="admin@example.com",
            hashed_password="$2b$12$wDLqZilS7krGQEv9hHv.LeXS3cb9PJ0PQ2aaiEJrY5RB4tUgtgR6K",  # password123
            name="Admin User",
            role=UserRole.ADMIN,
            contact="1234567890",
            address="123 Admin St"
        )
        db.add(admin_user)

        # Create hospital
        hospital = Hospital(
            id=str(uuid4()),
            name="Test Hospital",
            address="123 Hospital St",
            city="Test City",
            state="Test State",
            country="Test Country",
            contact="9876543210",
            pin_code="123456",
            email="hospital@example.com",
            specialities=["Cardiology", "Neurology", "Pediatrics"],
            website="https://testhospital.com"
        )
        db.add(hospital)

        # Create hospital user
        hospital_user = User(
            id=str(uuid4()),
            email="hospital@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # password123
            name="Test Hospital",
            role=UserRole.HOSPITAL,
            contact="9876543210",
            address="123 Hospital St",
            profile_id=hospital.id
        )
        db.add(hospital_user)

        # Create doctor
        doctor = Doctor(
            id=str(uuid4()),
            name="Dr. John Doe",
            photo="https://example.com/doctor.jpg",
            designation="Cardiologist",
            experience=10,
            details="Experienced cardiologist with 10 years of practice",
            contact="5555555555"
        )
        db.add(doctor)

        # Create doctor user
        doctor_user = User(
            id=str(uuid4()),
            email="doctor@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # password123
            name="Dr. John Doe",
            role=UserRole.DOCTOR,
            contact="5555555555",
            profile_id=doctor.id
        )
        db.add(doctor_user)

        # Create patient
        patient = Patient(
            id=str(uuid4()),
            name="Jane Smith",
            dob=datetime.now() - timedelta(days=365*30),  # 30 years old
            gender="female",
            contact="4444444444",
            photo="https://example.com/patient.jpg"
        )
        db.add(patient)

        # Create patient user
        patient_user = User(
            id=str(uuid4()),
            email="patient@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # password123
            name="Jane Smith",
            role=UserRole.PATIENT,
            contact="4444444444",
            profile_id=patient.id
        )
        db.add(patient_user)

        # Create mappings
        hospital_doctor_mapping = HospitalDoctorMapping(
            id=str(uuid4()),
            hospital_id=hospital.id,
            doctor_id=doctor.id
        )
        db.add(hospital_doctor_mapping)

        hospital_patient_mapping = HospitalPatientMapping(
            id=str(uuid4()),
            hospital_id=hospital.id,
            patient_id=patient.id
        )
        db.add(hospital_patient_mapping)

        doctor_patient_mapping = DoctorPatientMapping(
            id=str(uuid4()),
            doctor_id=doctor.id,
            patient_id=patient.id
        )
        db.add(doctor_patient_mapping)

        # Create chat
        chat = Chat(
            id=str(uuid4()),
            doctor_id=doctor.id,
            patient_id=patient.id,
            is_active=True
        )
        db.add(chat)

        # Commit changes
        db.commit()
        logger.info("Test data created successfully")

        # Return the chat ID for testing
        return chat.id

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating test data: {str(e)}")
        raise
    finally:
        db.close()

def initialize_database():
    """Initialize the database and return the chat ID"""
    create_tables()
    chat_id = create_test_data()
    logger.info(f"Created test chat with ID: {chat_id}")
    logger.info("Database initialization completed successfully")
    return chat_id

if __name__ == "__main__":
    initialize_database()
