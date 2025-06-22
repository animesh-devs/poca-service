#!/usr/bin/env python3
import os
import sys
import uuid
from datetime import datetime, timedelta
import random
import logging
import warnings

# Suppress bcrypt warnings before any other imports
warnings.filterwarnings("ignore", message=".*error reading bcrypt version.*")
warnings.filterwarnings("ignore", message=".*trapped.*error reading bcrypt version.*")

# Configure logging with a filter to suppress bcrypt warnings
class BcryptWarningFilter(logging.Filter):
    def filter(self, record):
        return not ("error reading bcrypt version" in record.getMessage() or
                   "trapped" in record.getMessage())

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Apply the filter to suppress bcrypt warnings
logging.getLogger('passlib.handlers.bcrypt').addFilter(BcryptWarningFilter())
logging.getLogger().addFilter(BcryptWarningFilter())

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
from app.models.chat import Chat, Message, MessageType
from app.models.ai import AISession, AIMessage
from app.models.document import FileDocument, DocumentType, UploadedBy
from app.api.auth import get_password_hash
from app.services.document_storage import document_storage
from app.config import settings

# Store credentials and entity information for output
credentials = {
    "admin": [],
    "hospitals": [],
    "doctors": [],
    "patients": [],
    "hospital_doctor_mappings": [],
    "hospital_patient_mappings": [],
    "doctor_patient_mappings": [],
    "chats": [],
    "ai_sessions": [],
    "ai_messages": []
}

def upload_profile_photo(photo_path: str, admin_user_id: str, db) -> str:
    """Upload a profile photo and return the download link"""
    try:
        # Read the photo file
        with open(photo_path, 'rb') as f:
            file_content = f.read()

        # Get filename from path
        filename = os.path.basename(photo_path)

        # Determine content type based on file extension
        if filename.lower().endswith('.png'):
            content_type = 'image/png'
        elif filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
            content_type = 'image/jpeg'
        else:
            content_type = 'image/png'  # default

        # Store document in memory storage
        storage_id = document_storage.store_document(
            file_content=file_content,
            filename=filename,
            content_type=content_type
        )

        # Create downloadable link using the public base URL
        download_link = f"{settings.PUBLIC_BASE_URL}{settings.API_V1_PREFIX}/documents/{storage_id}/download"

        # Create document record in database
        db_document = FileDocument(
            id=storage_id,  # Use the storage ID as the document ID
            file_name=filename,
            size=len(file_content),
            link=download_link,
            document_type=DocumentType.OTHER,
            uploaded_by=admin_user_id,
            uploaded_by_role=UploadedBy.ADMIN,
            remark="Profile photo uploaded during test data creation",
            entity_id=None
        )
        db.add(db_document)

        logger.info(f"Uploaded profile photo: {filename} -> {download_link}")
        return download_link

    except Exception as e:
        logger.error(f"Failed to upload profile photo {photo_path}: {e}")
        return f"https://example.com/default-profile.jpg"  # fallback

def clean_db():
    """Drop all tables and recreate them"""
    logger.info("Initializing database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")

def create_test_data():
    """Create test data with 2 hospitals, 5 patients with Indian names, and 5 doctors with specific specialties"""
    # Get database session
    db = next(get_db())

    try:
        # Create admin user
        admin_id = str(uuid.uuid4())
        admin_name = "Admin User"
        admin_email = "admin@example.com"
        admin_password = "admin123"
        admin_user = User(
            id=admin_id,
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            name=admin_name,
            role=UserRole.ADMIN,
            contact="+1234567890",
            address="123 Admin St, Adminville",
            is_active=True
        )
        db.add(admin_user)
        credentials["admin"].append({
            "name": admin_name,
            "email": admin_email,
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
            hospital_address = f"{100+i} Hospital Ave, Medtown"
            hospital_contact = f"+1555{i}55{i}555"

            # Create hospital profile
            hospital = Hospital(
                id=hospital_id,
                name=hospital_name,
                address=hospital_address,
                city="Medtown",
                state="Medstate",
                country="Medcountry",
                contact=hospital_contact,
                pin_code=f"1000{i}",
                email=hospital_email,
                specialities=["Cardiology", "Neurology", "Pediatrics", "Orthopedics"],
                website=f"https://hospital{i+1}.example.com"
            )
            db.add(hospital)

            # Create hospital user
            hospital_user_id = str(uuid.uuid4())
            hospital_user = User(
                id=hospital_user_id,
                email=hospital_email,
                hashed_password=get_password_hash(hospital_password),
                name=hospital_name,
                role=UserRole.HOSPITAL,
                contact=hospital_contact,
                address=hospital_address,
                profile_id=hospital_id,
                is_active=True
            )
            db.add(hospital_user)

            hospitals.append(hospital)
            credentials["hospitals"].append({
                "name": hospital_name,
                "email": hospital_email,
                "password": hospital_password,
                "id": hospital_id,
                "user_id": hospital_user_id,
                "address": hospital_address,
                "contact": hospital_contact
            })

        # Profile photo mapping for patients based on gender
        patient_photo_files = {
            'female': ['female1.png', 'female2.png', 'female3.png'],
            'male': ['male1.png', 'male2.png']
        }

        # Create 5 doctors with Indian names and specific specialties
        doctors = []
        specialties = ["Pediatrician", "Gynecologist", "Dietitian", "Physiotherapist", "Lactation Expert"]
        first_names = ['Rajesh', 'Priya', 'Amit', 'Kavya', 'Suresh']
        last_names = ['Sharma', 'Patel', 'Kumar', 'Reddy', 'Singh']

        # Doctor profile photo mapping based on specialty
        doctor_photo_files = {
            "Pediatrician": "pediatrist.png",
            "Gynecologist": "gynocologist.png",
            "Dietitian": "dietitian.png",
            "Physiotherapist": "physiotharapist.png",
            "Lactation Expert": "lactation.png"
        }

        for i in range(5):
            doctor_id = str(uuid.uuid4())
            doctor_first_name = first_names[i]
            doctor_last_name = last_names[i]
            doctor_name = f"Dr. {doctor_first_name} {doctor_last_name}"
            doctor_email = f"doctor{i+1}@example.com"
            doctor_password = f"doctor{i+1}"
            doctor_specialty = specialties[i]
            doctor_experience = 8 + i * 2  # 8, 10, 12, 14, 16 years
            doctor_contact = f"+91-98765-{43210 + i}"
            doctor_details = f"Experienced {doctor_specialty} with {doctor_experience} years of practice in maternal and child healthcare"

            # Upload doctor profile photo based on specialty
            photo_file = doctor_photo_files[doctor_specialty]
            photo_path = os.path.join('data', 'doctor profile photos', photo_file)
            doctor_photo_url = upload_profile_photo(photo_path, admin_id, db)

            # Create doctor profile
            doctor = Doctor(
                id=doctor_id,
                name=doctor_name,
                photo=doctor_photo_url,  # Use the uploaded photo URL
                designation=doctor_specialty,
                experience=doctor_experience,
                details=doctor_details,
                contact=doctor_contact
            )
            db.add(doctor)

            # Create doctor user
            doctor_user_id = str(uuid.uuid4())
            doctor_user = User(
                id=doctor_user_id,
                email=doctor_email,
                hashed_password=get_password_hash(doctor_password),
                name=doctor_name,
                role=UserRole.DOCTOR,
                contact=doctor_contact,
                profile_id=doctor_id,
                is_active=True
            )
            db.add(doctor_user)

            doctors.append(doctor)
            credentials["doctors"].append({
                "name": doctor_name,
                "first_name": doctor_first_name,
                "last_name": doctor_last_name,
                "email": doctor_email,
                "password": doctor_password,
                "id": doctor_id,
                "user_id": doctor_user_id,
                "specialty": doctor_specialty,
                "experience": doctor_experience,
                "contact": doctor_contact,
                "details": doctor_details
            })

            # Map doctors to hospitals
            # First 3 doctors to Hospital 1, last 2 doctors to Hospital 2
            hospital_idx = 1 if i >= 3 else 0
            hospital = hospitals[hospital_idx]

            mapping_id = str(uuid.uuid4())
            hospital_doctor_mapping = HospitalDoctorMapping(
                id=mapping_id,
                hospital_id=hospital.id,
                doctor_id=doctor_id
            )
            db.add(hospital_doctor_mapping)

            # Store mapping information
            credentials["hospital_doctor_mappings"].append({
                "id": mapping_id,
                "hospital_id": hospital.id,
                "hospital_name": hospital.name,
                "doctor_id": doctor_id,
                "doctor_name": doctor_name
            })

        # Create 5 patients with Indian names (each patient is a separate user with self relation)
        patient_names = [
            ("Ananya", "Gupta"),
            ("Rohan", "Mehta"),
            ("Sneha", "Iyer"),
            ("Arjun", "Joshi"),
            ("Meera", "Nair")
        ]

        for i in range(5):
            patient_user_id = str(uuid.uuid4())
            patient_id = str(uuid.uuid4())

            # Use Indian names
            patient_first_name, patient_last_name = patient_names[i]
            patient_name = f"{patient_first_name} {patient_last_name}"
            patient_user_name = patient_name  # patient_user_name should be the name of patient with relation 'self'
            patient_email = f"patient{i+1}@example.com"
            patient_password = f"patient{i+1}"
            patient_contact = f"+91-98765-{54321 + i}"
            patient_address = f"{i+1}/123, {['Koramangala', 'Indiranagar', 'Jayanagar', 'Whitefield', 'HSR Layout'][i]}, Bangalore, Karnataka"

            # Create single patient record with self relation
            gender = [Gender.FEMALE, Gender.MALE, Gender.FEMALE, Gender.MALE, Gender.FEMALE][i]
            patient_age = 25 + i * 2  # Ages: 25, 27, 29, 31, 33
            patient_dob = datetime.now() - timedelta(days=365*patient_age)
            patient_records = []
            self_patient_id = patient_id  # This will be the self patient ID for profile_id

            # Upload profile photo based on gender
            if gender == Gender.FEMALE:
                photo_file = patient_photo_files['female'][i % len(patient_photo_files['female'])]
            else:
                photo_file = patient_photo_files['male'][i % len(patient_photo_files['male'])]

            photo_path = os.path.join('data', 'patient profile photos', photo_file)
            patient_photo_url = upload_profile_photo(photo_path, admin_id, db)

            # Create patient profile
            patient = Patient(
                id=patient_id,
                user_id=patient_user_id,  # Link patient to user
                name=patient_name,
                dob=patient_dob,
                gender=gender,
                contact=patient_contact,
                photo=patient_photo_url  # Use the uploaded photo URL
            )
            db.add(patient)

            # Create user-patient relation (always SELF for single patient per user)
            relation_type = RelationType.SELF
            relation_id = str(uuid.uuid4())
            relation = UserPatientRelation(
                id=relation_id,
                user_id=patient_user_id,
                patient_id=patient_id,
                relation=relation_type
            )
            db.add(relation)

            patient_info = {
                "id": patient_id,
                "name": patient_name,
                "first_name": patient_first_name,
                "last_name": patient_last_name,
                "gender": gender.value,
                "age": patient_age,
                "dob": patient_dob.isoformat(),
                "contact": patient_contact,
                "relation": relation_type.value,
                "relation_id": relation_id
            }

            patient_records.append(patient_info)

            # Create patient user with profile_id set to self patient ID
            patient_user = User(
                id=patient_user_id,
                email=patient_email,
                hashed_password=get_password_hash(patient_password),
                name=patient_user_name,
                role=UserRole.PATIENT,
                contact=patient_contact,
                address=patient_address,
                profile_id=self_patient_id,  # Set profile_id to self patient ID
                is_active=True
            )
            db.add(patient_user)

            # Map patient to hospitals (randomly choose one hospital)
            hospital_idx = random.randint(0, len(hospitals) - 1)
            hospital = hospitals[hospital_idx]

            mapping_id = str(uuid.uuid4())
            hospital_patient_mapping = HospitalPatientMapping(
                id=mapping_id,
                hospital_id=hospital.id,
                patient_id=patient_id
            )
            db.add(hospital_patient_mapping)

            # Store hospital-patient mapping
            credentials["hospital_patient_mappings"].append({
                "id": mapping_id,
                "hospital_id": hospital.id,
                "hospital_name": hospital.name,
                "patient_id": patient_id,
                "patient_name": patient_name
            })

            # Map to ALL 5 doctors (as per requirement)
            for doctor in doctors:
                mapping_id = str(uuid.uuid4())
                doctor_patient_mapping = DoctorPatientMapping(
                    id=mapping_id,
                    doctor_id=doctor.id,
                    patient_id=patient_id
                )
                db.add(doctor_patient_mapping)

                # Store doctor-patient mapping
                credentials["doctor_patient_mappings"].append({
                    "id": mapping_id,
                    "doctor_id": doctor.id,
                    "doctor_name": doctor.name,
                    "patient_id": patient_id,
                    "patient_name": patient_name
                })

                # Create a chat between doctor and patient
                chat_id = str(uuid.uuid4())
                chat = Chat(
                    id=chat_id,
                    doctor_id=doctor.id,
                    patient_id=patient_id,
                    is_active_for_doctor=True,
                    is_active_for_patient=True
                )
                db.add(chat)

                # Store chat information
                credentials["chats"].append({
                    "id": chat_id,
                    "doctor_id": doctor.id,
                    "doctor_name": doctor.name,
                    "patient_id": patient_id,
                    "patient_name": patient_name,
                    "is_active_for_doctor": True,
                    "is_active_for_patient": True
                })


            credentials["patients"].append({
                "name": patient_user_name,
                "email": patient_email,
                "password": patient_password,
                "id": patient_user_id,
                "contact": patient_contact,
                "address": patient_address,
                "patients": patient_records
            })

        # Commit all changes
        db.commit()
        logger.info("Test data created successfully.")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating test data: {e}")
        return False
    finally:
        db.close()

def print_credentials():
    """Print all credentials in a readable format"""
    print("\n=== TEST DATA SUMMARY ===")

    print(f"\nADMIN: {credentials['admin'][0]['email']} / {credentials['admin'][0]['password']}")

    print(f"\nHOSPITALS ({len(credentials['hospitals'])}):")
    for i, hospital in enumerate(credentials["hospitals"]):
        print(f"  {hospital['email']} / {hospital['password']}")

    print(f"\nDOCTORS ({len(credentials['doctors'])}):")
    for i, doctor in enumerate(credentials["doctors"]):
        print(f"  {doctor['email']} / {doctor['password']} ({doctor['specialty']})")

    print(f"\nPATIENTS ({len(credentials['patients'])}):")
    for i, patient in enumerate(credentials["patients"]):
        print(f"  {patient['email']} / {patient['password']} ({patient['name']})")

    print("=== MAPPING INFORMATION ===\n")
    print("Hospital-Doctor Mappings:")
    for mapping in credentials.get("hospital_doctor_mappings", []):
        print(f"  Hospital '{mapping['hospital_name']}' (ID: {mapping['hospital_id']}) -> Doctor '{mapping['doctor_name']}' (ID: {mapping['doctor_id']})")

    print("\nHospital-Patient Mappings:")
    for mapping in credentials.get("hospital_patient_mappings", []):
        print(f"  Hospital '{mapping['hospital_name']}' (ID: {mapping['hospital_id']}) -> Patient '{mapping['patient_name']}' (ID: {mapping['patient_id']})")

    print("\nDoctor-Patient Mappings:")
    for mapping in credentials.get("doctor_patient_mappings", []):
        print(f"  Doctor '{mapping['doctor_name']}' (ID: {mapping['doctor_id']}) -> Patient '{mapping['patient_name']}' (ID: {mapping['patient_id']})")

    print("\nChat Sessions:")
    for chat in credentials.get("chats", []):
        print(f"  Chat ID: {chat['id']}")
        print(f"    Doctor: {chat['doctor_name']} (ID: {chat['doctor_id']})")
        print(f"    Patient: {chat['patient_name']} (ID: {chat['patient_id']})")
        print(f"    Active for Doctor: {chat['is_active_for_doctor']}")
        print(f"    Active for Patient: {chat['is_active_for_patient']}")
        print()

    print("\nAI Sessions:")
    for session in credentials.get("ai_sessions", []):
        print(f"  AI Session ID: {session['id']}")
        print(f"    Chat ID: {session['chat_id']}")
        print(f"    Doctor: {session['doctor_name']} (ID: {session['doctor_id']})")
        print(f"    Patient: {session['patient_name']} (ID: {session['patient_id']})")

        # Find messages for this session
        session_messages = [msg for msg in credentials.get("ai_messages", []) if msg["session_id"] == session["id"]]
        if session_messages:
            print(f"    Messages ({len(session_messages)}):")
            for i, msg in enumerate(session_messages):
                print(f"      Message {i+1}:")
                print(f"        ID: {msg['id']}")
                print(f"        User: {msg['message']}")
                print(f"        AI: {msg['response']}")
                print(f"        Is Summary: {msg['is_summary']}")
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
