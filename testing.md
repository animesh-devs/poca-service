# Testing Guide for POCA Service

This document provides a comprehensive guide for testing the POCA service, including information about the test scripts, test data, and how to run the tests.

## API Response Format

All API responses follow a standardized format:

```json
{
  "status_code": int,
  "status": bool,
  "message": string,
  "data": any
}
```

The test scripts are designed to handle both the standardized response format and the direct response format for backward compatibility. This allows for a smooth transition as more endpoints are processed by the middleware.

The standardized response format is implemented through middleware that wraps the API responses. The middleware handles:

1. Setting the appropriate status code
2. Adding the status, status_code, and message fields
3. Wrapping the original response in the data field

For more details on the standardized response format, see [API Response Format](docs/api_response_format.md).

## Test Scripts

The following test scripts are available in the `testing-scripts` directory:

1. **create_test_data.py** - Creates comprehensive test data for the service
2. **test_api_flow.py** - Tests all flows by hitting actual APIs in non-docker flow
3. **test_docker_flow.py** - Tests all flows by hitting actual APIs in docker flow
4. **api_helpers.py** - Helper file with methods to call different APIs

## Test Data

The `create_test_data.py` script creates the following test data:

### Hospitals
- General Hospital (Email: general@hospital.com, Password: hospital123)
- City Medical Center (Email: city@hospital.com, Password: hospital123)

### Doctors
- Dr. John Smith - Cardiology (Email: john.smith@doctor.com, Password: doctor123)
- Dr. Sarah Johnson - Neurology (Email: sarah.johnson@doctor.com, Password: doctor123)
- Dr. Michael Brown - Pediatrics (Email: michael.brown@doctor.com, Password: doctor123)
- Dr. Emily Davis - Dermatology (Email: emily.davis@doctor.com, Password: doctor123)

### Patients
- Alice Williams - 35 years old, female (Email: alice@patient.com, Password: patient123)
- Bob Johnson - 45 years old, male (Email: bob@patient.com, Password: patient123)
- Charlie Brown - 28 years old, male (Email: charlie@patient.com, Password: patient123)
- Diana Miller - 52 years old, female (Email: diana@patient.com, Password: patient123)
- Ethan Davis - 8 years old, male (Email: ethan@patient.com, Password: patient123)
- Fiona Wilson - 15 years old, female (Email: fiona@patient.com, Password: patient123)

### Mappings
- Alice Williams is mapped to Dr. John Smith and Dr. Sarah Johnson
- Bob Johnson is mapped to Dr. John Smith
- Charlie Brown is mapped to Dr. Michael Brown and Dr. Emily Davis
- Diana Miller is mapped to Dr. Michael Brown
- Ethan Davis is mapped to Dr. Sarah Johnson
- Fiona Wilson is mapped to Dr. Michael Brown and Dr. Emily Davis

## Running the Tests

### Creating Test Data

To create the test data, run:

```bash
python testing-scripts/create_test_data.py
```

This will create all the hospitals, doctors, patients, and mappings described above.

### Testing API Flow (Non-Docker)

To test all flows by hitting actual APIs in non-docker flow, run:

```bash
python testing-scripts/test_api_flow.py
```

This script tests the following flows:
- Authentication flow (login for admin, hospital, doctor, and patient)
- Mapping flow (mapping doctor to patient)
- Chat flow (creating chat and sending messages)
- AI assistant flow (creating AI session and sending messages)
- Case history flow (simulated)
- Reports flow (simulated)

### Testing Docker Flow

To test all flows by hitting actual APIs in docker flow, run:

```bash
python testing-scripts/test_docker_flow.py
```

This script does the following:
1. Ensures Docker is running and starts the containers if needed
2. Resets the database
3. Tests the same flows as the API flow test

## API Helpers

The `api_helpers.py` file contains helper functions for making API calls to the POCA service. These functions are used by the test scripts to interact with the service.

Key functions include:
- `check_server_health()` - Checks if the server is up and running
- `get_auth_token(email, password)` - Gets authentication token for a user
- `create_hospital(token, name, email, password)` - Creates a hospital
- `create_doctor(token, name, email, password, specialization, hospital_id)` - Creates a doctor
- `create_patient(token, name, email, password, age, gender, hospital_id)` - Creates a patient
- `map_doctor_to_patient(token, doctor_id, patient_id)` - Maps a doctor to a patient
- `create_chat(token, doctor_id, patient_id)` - Creates a chat between a doctor and a patient
- `send_message(token, chat_id, sender_id, receiver_id, message)` - Sends a message in a chat
- `create_ai_session(token, chat_id)` - Creates an AI assistant session
- `send_ai_message(token, session_id, message)` - Sends a message to the AI assistant

## Manual Testing

You can also test the service manually using the test data created by the `create_test_data.py` script. Here are some example API calls:

### Authentication

```bash
# Admin login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123"

# Doctor login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john.smith@doctor.com&password=doctor123"

# Patient login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice@patient.com&password=patient123"
```

### Get User Information

```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Hospitals

```bash
curl -X GET "http://localhost:8000/api/v1/hospitals" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Doctors

```bash
curl -X GET "http://localhost:8000/api/v1/doctors" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Patients

```bash
curl -X GET "http://localhost:8000/api/v1/patients" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Create Chat

```bash
curl -X POST "http://localhost:8000/api/v1/chats" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "doctor_id": "DOCTOR_ID",
    "patient_id": "PATIENT_ID",
    "is_active": true
  }'
```

### Send Message

```bash
curl -X POST "http://localhost:8000/api/v1/messages" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "CHAT_ID",
    "sender_id": "SENDER_ID",
    "receiver_id": "RECEIVER_ID",
    "message": "Hello, this is a test message",
    "message_type": "text"
  }'
```

### WebSocket Chat Connection

```
# Connect to the WebSocket endpoint using a WebSocket client
ws://localhost:8000/api/v1/chats/ws/CHAT_ID?token=YOUR_ACCESS_TOKEN

# Send a message (JSON format)
{
  "content": "Hello, this is a real-time message",
  "message_type": "text"
}
```

### Create AI Session

```bash
curl -X POST "http://localhost:8000/api/v1/ai/sessions" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "CHAT_ID"
  }'
```

### Send Message to AI

```bash
curl -X POST "http://localhost:8000/api/v1/ai/messages" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "SESSION_ID",
    "message": "I have a headache and fever"
  }'
```

## Troubleshooting

If you encounter any issues while running the tests, try the following:

1. Make sure the server is running
2. Check the server logs for any errors
3. Reset the database and try again
4. Ensure Docker is running (for Docker tests)
5. Check the Docker logs for any errors
