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

def create_profile_photo_record(photo_filename: str, admin_user_id: str, db) -> str:
    """Create a database record for a profile photo using environment-based URL"""
    try:
        # Create a predictable document ID based on filename
        import hashlib
        photo_hash = hashlib.md5(photo_filename.encode()).hexdigest()
        storage_id = f"profile-{photo_hash}"

        # Get the public base URL from environment variable or use default
        public_base_url = os.getenv("PUBLIC_BASE_URL", settings.PUBLIC_BASE_URL)

        # Create downloadable link using the public base URL from environment
        download_link = f"{public_base_url}{settings.API_V1_PREFIX}/documents/{storage_id}/download"

        # Check if document already exists
        existing_doc = db.query(FileDocument).filter(FileDocument.id == storage_id).first()
        if existing_doc:
            # Update the link in case the PUBLIC_BASE_URL has changed
            if existing_doc.link != download_link:
                existing_doc.link = download_link
                db.flush()
                logger.info(f"Updated profile photo URL: {photo_filename} -> {download_link}")
            else:
                logger.info(f"Profile photo record already exists: {photo_filename} -> {download_link}")
            return download_link

        # Try to find the photo file in possible locations
        possible_paths = [
            os.path.join('data', 'doctor profile photos', photo_filename),
            os.path.join('data', 'patient profile photos', photo_filename),
            os.path.join('..', 'data', 'doctor profile photos', photo_filename),
            os.path.join('..', 'data', 'patient profile photos', photo_filename),
            photo_filename  # Just the filename in current directory
        ]

        photo_path = None
        file_size = 0

        for path in possible_paths:
            if os.path.exists(path):
                photo_path = path
                file_size = os.path.getsize(path)
                break

        if not photo_path:
            logger.warning(f"Profile photo file not found: {photo_filename}")
            # Use a placeholder URL that works on any server
            return f"https://via.placeholder.com/150x150/cccccc/666666?text={photo_filename.split('.')[0]}"

        # Create document record in database
        db_document = FileDocument(
            id=storage_id,
            file_name=photo_filename,
            size=file_size,
            link=download_link,
            document_type=DocumentType.OTHER,
            uploaded_by=admin_user_id,
            uploaded_by_role=UploadedBy.ADMIN,
            remark=f"Profile photo for test data - Path: {photo_path}",
            entity_id=None
        )
        db.add(db_document)
        db.flush()

        logger.info(f"Created profile photo record: {photo_filename} -> {download_link} (Path: {photo_path})")
        return download_link

    except Exception as e:
        logger.error(f"Failed to create profile photo record {photo_filename}: {e}")
        return f"https://via.placeholder.com/150x150/cccccc/666666?text={photo_filename.split('.')[0]}"

def clean_db():
    """Drop all tables and recreate them"""
    logger.info("Initializing database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")

def create_test_data():
    """Create test data with 2 hospitals, 5 patients with Indian names, 5 doctors with specific specialties, plus mother and newborn care patients"""
    # Get database session
    db = next(get_db())

    try:
        # Run migration to add health fields to patients table
        logger.info("Running migration to add health fields to patients table...")
        try:
            from sqlalchemy import text

            # Check if the health fields already exist using SQLite-specific PRAGMA
            result = db.execute(text("PRAGMA table_info(patients)"))
            existing_columns = [row[1] for row in result.fetchall()]  # row[1] is column name

            health_fields = ['age', 'blood_group', 'height', 'weight', 'medical_info', 'emergency_contact_name', 'emergency_contact_number']
            missing_fields = [field for field in health_fields if field not in existing_columns]

            if missing_fields:
                logger.info(f"Adding missing health fields: {missing_fields}")
                # Add the missing columns (SQLite doesn't support IF NOT EXISTS in ALTER TABLE)
                migration_queries = []
                for field in missing_fields:
                    if field == 'age':
                        migration_queries.append("ALTER TABLE patients ADD COLUMN age INTEGER")
                    elif field == 'blood_group':
                        migration_queries.append("ALTER TABLE patients ADD COLUMN blood_group VARCHAR")
                    elif field == 'height':
                        migration_queries.append("ALTER TABLE patients ADD COLUMN height INTEGER")
                    elif field == 'weight':
                        migration_queries.append("ALTER TABLE patients ADD COLUMN weight INTEGER")
                    elif field == 'medical_info':
                        migration_queries.append("ALTER TABLE patients ADD COLUMN medical_info JSON")
                    elif field == 'emergency_contact_name':
                        migration_queries.append("ALTER TABLE patients ADD COLUMN emergency_contact_name VARCHAR")
                    elif field == 'emergency_contact_number':
                        migration_queries.append("ALTER TABLE patients ADD COLUMN emergency_contact_number VARCHAR")

                for query in migration_queries:
                    try:
                        db.execute(text(query))
                        logger.info(f"Successfully executed: {query}")
                    except Exception as e:
                        logger.warning(f"Migration query failed (column may already exist): {query} - {e}")

                db.commit()
                logger.info("Migration completed successfully")
            else:
                logger.info("All health fields already exist, skipping migration")

        except Exception as e:
            logger.warning(f"Migration failed, continuing anyway: {e}")
            # Continue with test data creation even if migration fails
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
            doctor_email = f"{doctor_first_name.lower()}@example.com"
            doctor_password = doctor_first_name.lower()
            doctor_specialty = specialties[i]
            doctor_experience = 8 + i * 2  # 8, 10, 12, 14, 16 years
            doctor_contact = f"+91-98765-{43210 + i}"
            doctor_details = f"Experienced {doctor_specialty} with {doctor_experience} years of practice in maternal and child healthcare"

            # Create doctor profile photo record based on specialty
            photo_file = doctor_photo_files[doctor_specialty]
            doctor_photo_url = create_profile_photo_record(photo_file, admin_id, db)

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

            patient_photo_url = create_profile_photo_record(photo_file, admin_id, db)

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
                    is_active_for_doctor=False,
                    is_active_for_patient=False
                )
                db.add(chat)

                # Store chat information
                credentials["chats"].append({
                    "id": chat_id,
                    "doctor_id": doctor.id,
                    "doctor_name": doctor.name,
                    "patient_id": patient_id,
                    "patient_name": patient_name,
                    "is_active_for_doctor": False,
                    "is_active_for_patient": False
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

        # Create Mother and Newborn Care Test Patients
        logger.info("Creating mother and newborn care test patients...")

        # Mother Patient
        mother_user_id = str(uuid.uuid4())
        mother_patient_id = str(uuid.uuid4())
        mother_name = "Priya Sharma"
        mother_email = "mother@example.com"
        mother_password = "password123"
        mother_contact = "+91-9876543212"
        mother_address = "456 Family Street, Mumbai, Maharashtra"

        # Mother's health information
        mother_medical_info = {
            "allergies": ["None"],
            "medications": ["Prenatal vitamins", "Iron supplements", "Calcium tablets"],
            "conditions": ["Post-delivery recovery", "Breastfeeding"]
        }

        # Upload mother's profile photo
        mother_photo_url = create_profile_photo_record(patient_photo_files['female'][0], admin_id, db)

        # Create mother patient profile with health info
        from datetime import date
        mother_patient = Patient(
            id=mother_patient_id,
            user_id=mother_user_id,
            name=mother_name,
            dob=date(1996, 3, 15),  # 28 years old
            gender=Gender.FEMALE,
            contact=mother_contact,
            photo=mother_photo_url,
            age=28,
            blood_group="O+",
            height=165,
            weight=68,  # Post-delivery weight
            medical_info=mother_medical_info,
            emergency_contact_name="Rajesh Sharma (Husband)",
            emergency_contact_number="+91-9876543213"
        )
        db.add(mother_patient)

        # Create mother user-patient relation (self)
        mother_relation_id = str(uuid.uuid4())
        mother_relation = UserPatientRelation(
            id=mother_relation_id,
            user_id=mother_user_id,
            patient_id=mother_patient_id,
            relation=RelationType.SELF
        )
        db.add(mother_relation)

        # Create mother user account
        mother_user = User(
            id=mother_user_id,
            email=mother_email,
            hashed_password=get_password_hash(mother_password),
            name=mother_name,
            role=UserRole.PATIENT,
            contact=mother_contact,
            address=mother_address,
            profile_id=mother_patient_id,
            is_active=True
        )
        db.add(mother_user)

        # Newborn Patient
        newborn_user_id = str(uuid.uuid4())
        newborn_patient_id = str(uuid.uuid4())
        newborn_name = "Baby Arjun Sharma"
        newborn_email = "child@example.com"
        newborn_password = "password123"
        newborn_contact = mother_contact  # Same as mother
        newborn_address = mother_address  # Same as mother

        # Newborn's health information
        newborn_medical_info = {
            "allergies": ["None known"],
            "medications": ["Vitamin D drops"],
            "conditions": ["Healthy newborn", "Breastfeeding"]
        }

        # Upload newborn's profile photo
        newborn_photo_url = create_profile_photo_record(patient_photo_files['male'][0], admin_id, db)

        # Create newborn patient profile with health info
        newborn_patient = Patient(
            id=newborn_patient_id,
            user_id=newborn_user_id,
            name=newborn_name,
            dob=date(2024, 6, 15),  # Born June 15, 2024
            gender=Gender.MALE,
            contact=newborn_contact,
            photo=newborn_photo_url,
            age=0,  # Newborn
            blood_group="O+",
            height=50,  # 50cm birth length
            weight=3,   # 3kg birth weight
            medical_info=newborn_medical_info,
            emergency_contact_name="Priya Sharma (Mother)",
            emergency_contact_number=mother_contact
        )
        db.add(newborn_patient)

        # Create newborn user-patient relation (self)
        newborn_relation_id = str(uuid.uuid4())
        newborn_self_relation = UserPatientRelation(
            id=newborn_relation_id,
            user_id=newborn_user_id,
            patient_id=newborn_patient_id,
            relation=RelationType.SELF
        )
        db.add(newborn_self_relation)

        # Create mother-child relation (mother -> child)
        mother_child_relation_id = str(uuid.uuid4())
        mother_child_relation = UserPatientRelation(
            id=mother_child_relation_id,
            user_id=mother_user_id,
            patient_id=newborn_patient_id,
            relation=RelationType.CHILD
        )
        db.add(mother_child_relation)

        # Create newborn user account
        newborn_user = User(
            id=newborn_user_id,
            email=newborn_email,
            hashed_password=get_password_hash(newborn_password),
            name=newborn_name,
            role=UserRole.PATIENT,
            contact=newborn_contact,
            address=newborn_address,
            profile_id=newborn_patient_id,
            is_active=True
        )
        db.add(newborn_user)

        # Map mother and newborn to appropriate doctors and hospitals
        # Find gynecologist and pediatrician from existing doctors
        gynecologist = None
        pediatrician = None
        for doctor in doctors:
            if "gynecologist" in doctor.designation.lower() or "gynaecologist" in doctor.designation.lower():
                gynecologist = doctor
            elif "pediatrician" in doctor.designation.lower():
                pediatrician = doctor

        # Map both patients to hospitals (use first hospital)
        hospital = hospitals[0]

        for patient_id, patient_name in [(mother_patient_id, mother_name), (newborn_patient_id, newborn_name)]:
            # Hospital-patient mapping
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

            # Map to all 5 doctors (as per existing pattern)
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

                # Create chat between doctor and patient
                chat_id = str(uuid.uuid4())
                chat = Chat(
                    id=chat_id,
                    doctor_id=doctor.id,
                    patient_id=patient_id,
                    is_active_for_doctor=False,
                    is_active_for_patient=False
                )
                db.add(chat)

                # Store chat information
                credentials["chats"].append({
                    "id": chat_id,
                    "doctor_id": doctor.id,
                    "doctor_name": doctor.name,
                    "patient_id": patient_id,
                    "patient_name": patient_name,
                    "is_active_for_doctor": False,
                    "is_active_for_patient": False
                })

        # Add mother and newborn to credentials
        credentials["patients"].extend([
            {
                "name": mother_name,
                "email": mother_email,
                "password": mother_password,
                "id": mother_user_id,
                "contact": mother_contact,
                "address": mother_address,
                "patients": [{
                    "id": mother_patient_id,
                    "name": mother_name,
                    "gender": "female",
                    "age": 28,
                    "relation": "self"
                }]
            },
            {
                "name": newborn_name,
                "email": newborn_email,
                "password": newborn_password,
                "id": newborn_user_id,
                "contact": newborn_contact,
                "address": newborn_address,
                "patients": [{
                    "id": newborn_patient_id,
                    "name": newborn_name,
                    "gender": "male",
                    "age": 0,
                    "relation": "self"
                }]
            }
        ])

        # Create case histories and reports for mother and newborn
        logger.info("Creating case histories and reports for mother and newborn...")

        # Import required models for case history and reports
        from app.models.case_history import CaseHistory
        from app.models.report import Report, ReportType, PatientReportMapping

        # Mother's case history
        mother_case_history = CaseHistory(
            id=str(uuid.uuid4()),
            patient_id=mother_patient_id,
            summary="Post-Delivery Care Summary: 28-year-old female, delivered healthy baby boy on June 15, 2024 via normal delivery. Current status: Post-delivery recovery progressing well. Breastfeeding established successfully. Current medications: Prenatal vitamins, Iron supplements, Calcium tablets. No known allergies. Concerns: Post-delivery recovery, breastfeeding support, maternal nutrition. Recommendations: Continue current supplements, adequate rest, proper nutrition for breastfeeding, regular follow-up visits.",
            documents=[]
        )
        db.add(mother_case_history)

        # Mother's reports
        mother_report1_id = str(uuid.uuid4())
        mother_report1 = Report(
            id=mother_report1_id,
            title="Post-Delivery Health Assessment",
            description="Post-delivery recovery excellent. Uterine involution normal. Breastfeeding well established. Hemoglobin: 11.2 g/dL. Blood pressure: 120/80 mmHg. Recommended: Continue iron supplements, adequate nutrition.",
            report_type=ReportType.POST_DELIVERY
        )
        db.add(mother_report1)

        # Create patient-report mapping for mother report 1
        mother_report1_mapping = PatientReportMapping(
            id=str(uuid.uuid4()),
            patient_id=mother_patient_id,
            report_id=mother_report1_id
        )
        db.add(mother_report1_mapping)

        mother_report2_id = str(uuid.uuid4())
        mother_report2 = Report(
            id=mother_report2_id,
            title="Breastfeeding Assessment",
            description="Breastfeeding established successfully. Good latch observed. Milk supply adequate. No signs of mastitis or nipple trauma. Recommendations: Continue exclusive breastfeeding, proper positioning techniques.",
            report_type=ReportType.LACTATION
        )
        db.add(mother_report2)

        # Create patient-report mapping for mother report 2
        mother_report2_mapping = PatientReportMapping(
            id=str(uuid.uuid4()),
            patient_id=mother_patient_id,
            report_id=mother_report2_id
        )
        db.add(mother_report2_mapping)

        # Newborn's case history
        newborn_case_history = CaseHistory(
            id=str(uuid.uuid4()),
            patient_id=newborn_patient_id,
            summary="Newborn Care Summary: Healthy baby boy born on June 15, 2024 at 39 weeks gestation. Birth weight: 3200g, Birth length: 50cm. Current status: Thriving newborn, exclusively breastfed. Current medications: Vitamin D drops as per pediatric guidelines. No known allergies. Concerns: Growth monitoring, feeding patterns, developmental milestones, vaccination schedule. Recommendations: Continue exclusive breastfeeding, regular weight monitoring, follow vaccination schedule, developmental assessments.",
            documents=[]
        )
        db.add(newborn_case_history)

        # Newborn's reports
        newborn_report1_id = str(uuid.uuid4())
        newborn_report1 = Report(
            id=newborn_report1_id,
            title="Newborn Health Assessment",
            description="Healthy newborn male. Birth weight: 3.2kg (appropriate for gestational age). APGAR scores: 9/10. All newborn screening tests normal. Feeding well, good weight gain pattern.",
            report_type=ReportType.NEWBORN_SCREENING
        )
        db.add(newborn_report1)

        # Create patient-report mapping for newborn report 1
        newborn_report1_mapping = PatientReportMapping(
            id=str(uuid.uuid4()),
            patient_id=newborn_patient_id,
            report_id=newborn_report1_id
        )
        db.add(newborn_report1_mapping)

        newborn_report2_id = str(uuid.uuid4())
        newborn_report2 = Report(
            id=newborn_report2_id,
            title="Growth and Development Chart",
            description="Current weight: 3.2kg, Length: 50cm, Head circumference: 35cm. Growth parameters within normal percentiles. Developmental milestones appropriate for age.",
            report_type=ReportType.GROWTH_CHART
        )
        db.add(newborn_report2)

        # Create patient-report mapping for newborn report 2
        newborn_report2_mapping = PatientReportMapping(
            id=str(uuid.uuid4()),
            patient_id=newborn_patient_id,
            report_id=newborn_report2_id
        )
        db.add(newborn_report2_mapping)

        newborn_report3_id = str(uuid.uuid4())
        newborn_report3 = Report(
            id=newborn_report3_id,
            title="Immunization Record",
            description="Birth vaccines completed: BCG, Hepatitis B (birth dose). Next due: 6 weeks - DPT, Polio, Hepatitis B, Hib, PCV, Rotavirus vaccines.",
            report_type=ReportType.VACCINATION
        )
        db.add(newborn_report3)

        # Create patient-report mapping for newborn report 3
        newborn_report3_mapping = PatientReportMapping(
            id=str(uuid.uuid4()),
            patient_id=newborn_patient_id,
            report_id=newborn_report3_id
        )
        db.add(newborn_report3_mapping)

        logger.info("✅ Mother and newborn test data created successfully!")

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
        if patient['email'] in ['mother@example.com', 'child@example.com']:
            print(f"  🤱 {patient['email']} / {patient['password']} ({patient['name']}) [MOTHER & NEWBORN CARE]")
        else:
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

    # Highlight Mother & Newborn Care Mappings
    print("\n🤱 MOTHER & NEWBORN CARE MAPPINGS:")
    mother_mappings = [m for m in credentials.get("doctor_patient_mappings", []) if m['patient_name'] in ['Priya Sharma', 'Baby Arjun Sharma']]
    if mother_mappings:
        print("  Mother (Priya Sharma) mapped to:")
        for mapping in mother_mappings:
            if mapping['patient_name'] == 'Priya Sharma':
                print(f"    ✓ {mapping['doctor_name']} ({mapping['doctor_name'].split()[-1].replace('Dr.', '').strip()})")

        print("  Newborn (Baby Arjun Sharma) mapped to:")
        for mapping in mother_mappings:
            if mapping['patient_name'] == 'Baby Arjun Sharma':
                print(f"    ✓ {mapping['doctor_name']} ({mapping['doctor_name'].split()[-1].replace('Dr.', '').strip()})")

        print("  🎯 Perfect for Mother & Newborn Care AI Context!")

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
