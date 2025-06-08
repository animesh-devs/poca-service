#!/bin/bash

# Script to reset the database and initialize it afresh with test data

# Set up colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Resetting the database for POCA service...${NC}"

# Check if Docker is running
if ! docker ps &> /dev/null; then
    echo -e "${RED}Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if the container is running
if ! docker ps | grep -q poca-service-api-1; then
    echo -e "${YELLOW}Starting Docker containers...${NC}"
    docker-compose up -d
    echo -e "${GREEN}Waiting for containers to start...${NC}"
    sleep 10
fi

# Stop the application to avoid database locks
echo -e "${YELLOW}Stopping the application...${NC}"
docker exec poca-service-api-1 pkill -f uvicorn || true
sleep 2

# Remove the database file
echo -e "${YELLOW}Removing the database file...${NC}"
docker exec poca-service-api-1 rm -f /app/app.db
echo -e "${GREEN}Database file removed.${NC}"

# Initialize the database
echo -e "${YELLOW}Initializing the database...${NC}"
docker exec poca-service-api-1 python init_db.py --force
echo -e "${GREEN}Database initialized.${NC}"

# Create test data
echo -e "${YELLOW}Creating test data...${NC}"
docker exec poca-service-api-1 python -c "
import sqlite3
import uuid
from passlib.context import CryptContext
import datetime

# Set up password hashing
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

# Connect to the database
conn = sqlite3.connect('/app/app.db')
cursor = conn.cursor()

try:
    # Check if admin user already exists
    cursor.execute('SELECT id FROM users WHERE email = ?', ('admin@example.com',))
    admin_user = cursor.fetchone()

    if admin_user:
        admin_id = admin_user[0]
        print(f'Admin user already exists with ID: {admin_id}')
    else:
        # Create test admin user
        admin_id = str(uuid.uuid4())
        admin_password = 'admin123'
        admin_hashed_password = pwd_context.hash(admin_password)
        cursor.execute(
            'INSERT INTO users (id, email, hashed_password, name, role, is_active) VALUES (?, ?, ?, ?, ?, ?)',
            (admin_id, 'admin@example.com', admin_hashed_password, 'Test Admin', 'ADMIN', 1)
        )
        print(f'Created admin user: admin@example.com / {admin_password}')

    # Check if hospital already exists
    cursor.execute('SELECT id FROM hospitals WHERE email = ?', ('test@hospital.com',))
    hospital = cursor.fetchone()

    if hospital:
        hospital_id = hospital[0]
        print(f'Hospital already exists with ID: {hospital_id}')
    else:
        # Create test hospital
        hospital_id = str(uuid.uuid4())
        cursor.execute(
            'INSERT INTO hospitals (id, name, address, contact, email) VALUES (?, ?, ?, ?, ?)',
            (hospital_id, 'Test Hospital', '123 Test St', '1234567890', 'test@hospital.com')
        )
        print(f'Created hospital: Test Hospital')

    # Check if doctor user already exists
    cursor.execute('SELECT id FROM users WHERE email = ?', ('doctor@example.com',))
    doctor_user = cursor.fetchone()

    if doctor_user:
        doctor_user_id = doctor_user[0]
        print(f'Doctor user already exists with ID: {doctor_user_id}')

        # Check if doctor record already exists
        cursor.execute('SELECT id FROM doctors WHERE id = ?', (doctor_user_id,))
        doctor_record = cursor.fetchone()

        if doctor_record:
            doctor_id = doctor_record[0]
            print(f'Doctor record already exists with ID: {doctor_id}')
        else:
            # Create doctor record
            doctor_id = doctor_user_id
            cursor.execute(
                'INSERT INTO doctors (id, name, contact) VALUES (?, ?, ?)',
                (doctor_id, 'Dr. Test', '1234567890')
            )
            print(f'Created doctor record with ID: {doctor_id}')
    else:
        # Create test doctor user
        doctor_user_id = str(uuid.uuid4())
        doctor_password = 'doctor123'
        doctor_hashed_password = pwd_context.hash(doctor_password)
        cursor.execute(
            'INSERT INTO users (id, email, hashed_password, name, role, is_active) VALUES (?, ?, ?, ?, ?, ?)',
            (doctor_user_id, 'doctor@example.com', doctor_hashed_password, 'Dr. Test', 'DOCTOR', 1)
        )

        # Create doctor record
        doctor_id = doctor_user_id
        cursor.execute(
            'INSERT INTO doctors (id, name, contact) VALUES (?, ?, ?)',
            (doctor_id, 'Dr. Test', '1234567890')
        )

        print(f'Created doctor user and record: doctor@example.com / {doctor_password}')

        # Create hospital-doctor mapping
        mapping_id = str(uuid.uuid4())
        cursor.execute(
            'INSERT INTO hospital_doctor_mappings (id, hospital_id, doctor_id) VALUES (?, ?, ?)',
            (mapping_id, hospital_id, doctor_id)
        )
        print(f'Created hospital-doctor mapping')

    # Check if patient user already exists
    cursor.execute('SELECT id FROM users WHERE email = ?', ('patient@example.com',))
    patient_user = cursor.fetchone()

    if patient_user:
        patient_user_id = patient_user[0]
        print(f'Patient user already exists with ID: {patient_user_id}')

        # Check if patient record already exists
        cursor.execute('SELECT id FROM patients WHERE id = ?', (patient_user_id,))
        patient_record = cursor.fetchone()

        if patient_record:
            patient_id = patient_record[0]
            print(f'Patient record already exists with ID: {patient_id}')
        else:
            # Create patient record
            patient_id = patient_user_id
            cursor.execute(
                'INSERT INTO patients (id, name, dob, gender, contact) VALUES (?, ?, ?, ?, ?)',
                (patient_id, 'Test Patient', '1990-01-01', 'male', '1234567890')
            )
            print(f'Created patient record with ID: {patient_id}')
    else:
        # Create test patient user
        patient_user_id = str(uuid.uuid4())
        patient_password = 'patient123'
        patient_hashed_password = pwd_context.hash(patient_password)

        # Create patient record first
        patient_id = patient_user_id
        cursor.execute(
            'INSERT INTO patients (id, user_id, name, dob, gender, contact) VALUES (?, ?, ?, ?, ?, ?)',
            (patient_id, patient_user_id, 'Test Patient', '1990-01-01', 'male', '1234567890')
        )

        # Create user with profile_id set to patient_id
        cursor.execute(
            'INSERT INTO users (id, email, hashed_password, name, role, profile_id, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (patient_user_id, 'patient@example.com', patient_hashed_password, 'Test Patient', 'PATIENT', patient_id, 1)
        )

        # Create user-patient self relation
        relation_id = str(uuid.uuid4())
        cursor.execute(
            'INSERT INTO user_patient_relations (id, user_id, patient_id, relation) VALUES (?, ?, ?, ?)',
            (relation_id, patient_user_id, patient_id, 'self')
        )

        print(f'Created patient user and record: patient@example.com / {patient_password}')

        # Create hospital-patient mapping
        mapping_id = str(uuid.uuid4())
        cursor.execute(
            'INSERT INTO hospital_patient_mappings (id, hospital_id, patient_id) VALUES (?, ?, ?)',
            (mapping_id, hospital_id, patient_id)
        )
        print(f'Created hospital-patient mapping')

        # Create doctor-patient mapping
        mapping_id = str(uuid.uuid4())
        cursor.execute(
            'INSERT INTO doctor_patient_mappings (id, doctor_id, patient_id) VALUES (?, ?, ?)',
            (mapping_id, doctor_id, patient_id)
        )
        print(f'Created doctor-patient mapping')

    # Check if chat already exists
    cursor.execute('SELECT id FROM chats WHERE doctor_id = ? AND patient_id = ?', (doctor_id, patient_id))
    chat = cursor.fetchone()

    if chat:
        chat_id = chat[0]
        print(f'Chat already exists with ID: {chat_id}')
    else:
        # Create test chat
        chat_id = str(uuid.uuid4())
        cursor.execute(
            'INSERT INTO chats (id, doctor_id, patient_id, is_active, created_at) VALUES (?, ?, ?, ?, ?)',
            (chat_id, doctor_id, patient_id, 1, datetime.datetime.now().isoformat())
        )
        print(f'Created chat between doctor and patient with ID: {chat_id}')

    # Commit changes
    conn.commit()
    print('Test data created successfully!')

except Exception as e:
    print(f'Error creating test data: {e}')
    conn.rollback()

finally:
    # Close connection
    conn.close()
"

# Fix user roles (ensure they are uppercase)
echo -e "${YELLOW}Fixing user roles in the database...${NC}"
docker cp fix_user_roles.py poca-service-api-1:/app/
docker exec poca-service-api-1 python /app/fix_user_roles.py
echo -e "${GREEN}User roles fixed.${NC}"

# Restart the application
echo -e "${YELLOW}Restarting the application...${NC}"
docker exec -d poca-service-api-1 bash -c "cd /app && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo -e "${GREEN}Application restarted.${NC}"

# Wait for the application to start
echo -e "${YELLOW}Waiting for the application to start...${NC}"
sleep 10

# Check if the application is running
echo -e "${YELLOW}Checking if the application is running...${NC}"
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo -e "${GREEN}Application is running and healthy!${NC}"
else
    echo -e "${RED}Application is not running. Check the logs with 'docker-compose logs'.${NC}"
    docker-compose logs
    exit 1
fi

# Check admin user details
echo -e "${YELLOW}Checking admin user details...${NC}"
ADMIN_DETAILS=$(docker exec poca-service-api-1 python -c "
import sqlite3
conn = sqlite3.connect('/app/app.db')
cursor = conn.cursor()
cursor.execute('SELECT id, email, name, is_active FROM users WHERE role = \"ADMIN\"')
user = cursor.fetchone()
conn.close()
if user:
    print(f'ID: {user[0]}, Email: {user[1]}, Name: {user[2]}, Active: {user[3]}')
else:
    print('No admin user found')
")
echo -e "${GREEN}Admin user details: $ADMIN_DETAILS${NC}"

echo -e "${GREEN}Database reset completed with test data!${NC}"
echo -e "${GREEN}You can now run the Docker test script: ./docker_test.sh${NC}"
exit 0
