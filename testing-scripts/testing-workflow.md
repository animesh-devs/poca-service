# Testing Workflow

This document outlines the testing workflow for the POCA Service, including API calls, test user credentials, and automated test scripts.

## Test Users

The following test users are available after running `init_test_db.py`:

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@example.com | admin123 |
| Hospital | hospital@example.com | hospital123 |
| Doctor (Cardiologist) | doctor.cardio@example.com | doctor123 |
| Doctor (Neurologist) | doctor.neuro@example.com | doctor123 |
| Patient (Adult) | patient.adult@example.com | patient123 |

## Testing Workflow

### 1. Authentication

#### Login as Admin
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123"
```

#### Login as Doctor
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=doctor.cardio@example.com&password=doctor123"
```

#### Login as Patient
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=patient.adult@example.com&password=patient123"
```

### 2. User Management

#### Get Current User Profile
```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Update Current User Profile
```bash
curl -X PUT "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name",
    "contact": "+1234567890"
  }'
```

### 3. Hospital Management

#### Get All Hospitals
```bash
curl -X GET "http://localhost:8000/api/v1/hospitals" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Get Hospital by ID
```bash
curl -X GET "http://localhost:8000/api/v1/hospitals/HOSPITAL_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Get Hospital Doctors
```bash
curl -X GET "http://localhost:8000/api/v1/hospitals/HOSPITAL_ID/doctors" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Doctor Management

#### Get All Doctors
```bash
curl -X GET "http://localhost:8000/api/v1/doctors" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Get Doctor by ID
```bash
curl -X GET "http://localhost:8000/api/v1/doctors/DOCTOR_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Get Doctor's Patients
```bash
curl -X GET "http://localhost:8000/api/v1/doctors/DOCTOR_ID/patients" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5. Patient Management

#### Get All Patients
```bash
curl -X GET "http://localhost:8000/api/v1/patients" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Get Patient by ID
```bash
curl -X GET "http://localhost:8000/api/v1/patients/PATIENT_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Get Patient's Doctors
```bash
curl -X GET "http://localhost:8000/api/v1/patients/PATIENT_ID/doctors" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 6. Mapping Management

#### Map Doctor to Patient
```bash
curl -X POST "http://localhost:8000/api/v1/mappings/doctor-patient" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "doctor_id": "DOCTOR_ID",
    "patient_id": "PATIENT_ID"
  }'
```

### 7. Chat Management

#### Get All Chat Sessions
```bash
curl -X GET "http://localhost:8000/api/v1/chats" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Get Chat Session by ID
```bash
curl -X GET "http://localhost:8000/api/v1/chats/CHAT_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Get Chat Messages
```bash
curl -X GET "http://localhost:8000/api/v1/chats/CHAT_ID/messages" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 8. Message Management

#### Send Message
```bash
curl -X POST "http://localhost:8000/api/v1/messages" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "CHAT_ID",
    "sender_id": "SENDER_USER_ID",
    "receiver_id": "RECEIVER_USER_ID",
    "message": "Hello, this is a test message",
    "message_type": "text"
  }'
```

### 9. AI Assistant

#### Create AI Session
```bash
curl -X POST "http://localhost:8000/api/v1/ai-assistant/sessions" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "CHAT_ID"
  }'
```

#### Send Message to AI Assistant
```bash
curl -X POST "http://localhost:8000/api/v1/ai-assistant/sessions/SESSION_ID/messages" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "SESSION_ID",
    "message": "I have been experiencing headaches for the past week"
  }'
```

## Real-time Communication Testing

The POCA service supports WebSocket for real-time communication.

### WebSocket Testing

For WebSocket testing, you can use tools like [websocat](https://github.com/vi/websocat), browser-based WebSocket clients, or the Postman WebSocket client.

### Using Postman

1. Import the "POCA Service WebSocket APIs" collection
2. Use the pre-configured WebSocket requests with the WSS protocol

### Using websocat or other tools

When using command-line tools or custom clients, make sure to use the WSS protocol:

### Chat WebSocket
```bash
websocat "wss://localhost:8000/api/v1/chats/ws/CHAT_ID?token=YOUR_ACCESS_TOKEN"
```

### AI Assistant WebSocket
```bash
websocat "wss://localhost:8000/api/v1/ai-assistant/ws/SESSION_ID?token=YOUR_ACCESS_TOKEN"
```

> **Note**: If you're testing locally with a self-signed certificate, you may need to use the `--insecure` flag with websocat or equivalent options in other tools.

### WebSocket Features

| Feature | WebSocket |
|---------|-----------|
| **Protocol** | Native WebSocket |
| **Browser Support** | Modern browsers |
| **Message Format** | JSON strings |
| **Authentication** | Query parameters |
| **Endpoint** | `/api/v1/ai-assistant/ws/{session_id}` |

## Automated Test Scripts

The following automated test scripts are available to test the POCA Service:

### 1. Test Data Creation

#### create_test_data.py
This script creates test data for the POCA service, including hospitals, doctors, patients, and mappings between them.

**Usage:**
```bash
python create_test_data.py
```

**What it does:**
- Creates 2 hospitals
- Creates 4 doctors with different specialties
- Creates 4 patients
- Maps doctors to patients
- Maps hospitals to doctors
- Maps hospitals to patients
- Saves the created data to a file for reference

### 2. API Testing (Non-Docker)

#### test_api_flow_direct.py
This script tests all the flows of the POCA service by hitting actual APIs in non-docker flow. It uses direct signup endpoints to create test data.

**Usage:**
```bash
cd testing-scripts
python test_api_flow_direct.py
```

**What it does:**
- Tests authentication flow (admin, hospital, doctor, patient)
- Tests user management APIs
- Tests hospital management APIs
- Tests doctor management APIs
- Tests patient management APIs
- Tests mapping APIs (hospital-doctor, hospital-patient, doctor-patient)
- Tests chat APIs
- Tests message APIs
- Tests AI assistant APIs

### 3. API Testing (Docker)

#### test_docker_flow_direct.py
This script tests all the flows of the POCA service by hitting actual APIs in docker flow. It uses direct signup endpoints to create test data.

**Usage:**
```bash
cd testing-scripts
python test_docker_flow_direct.py
```

**What it does:**
- Checks if Docker is running
- Checks if the Docker container is running
- Tests authentication flow (admin, hospital, doctor, patient)
- Tests user management APIs
- Tests hospital management APIs
- Tests doctor management APIs
- Tests patient management APIs
- Tests mapping APIs (hospital-doctor, hospital-patient, doctor-patient)
- Tests chat APIs
- Tests message APIs
- Tests AI assistant APIs

### 4. API Helper Files

#### test_endpoints.py
This script tests specific API endpoints of the POCA service, focusing on mappings, chats, and messages.

**Usage:**
```bash
python test_endpoints.py
```

**What it does:**
- Tests mappings API (hospital-doctor, hospital-patient, doctor-patient)
- Tests chats API (create, get, deactivate)
- Tests messages API (send, get, update read status)

## Test Data Requirements

The test scripts maintain the following test data:
- 2 hospitals
- 4 users (2 doctors, 2 patients)
- 2-3 patients per doctor
- 4-5 doctors in total

This ensures comprehensive testing of all API endpoints and workflows.
