# Testing Workflow

This document outlines the testing workflow for the POCA Service, including API calls and test user credentials.

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

## WebSocket Testing

For WebSocket testing, you can use tools like [websocat](https://github.com/vi/websocat) or browser-based WebSocket clients.

### Chat WebSocket
```bash
websocat "ws://localhost:8000/api/v1/chats/ws/CHAT_ID?token=YOUR_ACCESS_TOKEN"
```

### AI Assistant WebSocket
```bash
websocat "ws://localhost:8000/api/v1/ai-assistant/ws/SESSION_ID?token=YOUR_ACCESS_TOKEN"
```
