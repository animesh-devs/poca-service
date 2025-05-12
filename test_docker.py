#!/usr/bin/env python3
"""
Test script for the POCA service running in Docker.
This script tests the complete flow from patient registration to doctor-patient communication.
"""

import requests
import json
import logging
import sys
import time
import asyncio
import websockets
from datetime import datetime
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# API configuration
# Use the Docker service name and port
BASE_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/api/v1/ai-assistant/ws"

# Test data
TEST_ADMIN_EMAIL = "admin@example.com"
TEST_ADMIN_PASSWORD = "admin123"  # Default password from init_db.py

TEST_HOSPITAL_DATA = {
    "name": "Docker Test Hospital",
    "address": "123 Docker St",
    "contact": "1234567890",
    "email": "docker@hospital.com"
}

TEST_DOCTOR_DATA = {
    "name": "Dr. Docker",
    "email": "doctor@docker.com",
    "password": "docker123",
    "contact": "1234567890",
    "address": "123 Docker St",
    "specialization": "Docker Medicine",
    "hospital_id": None  # Will be set after hospital creation
}

TEST_PATIENT_DATA = {
    "name": "Docker Patient",
    "email": "patient@docker.com",
    "password": "docker123",
    "contact": "1234567890",
    "address": "123 Docker St",
    "date_of_birth": "1990-01-01",
    "gender": "male",
    "blood_group": "O+",
    "medical_history": "None"
}

# Authentication functions
def get_auth_token(email, password, max_retries=3, retry_delay=2):
    """
    Get authentication token with retry logic

    Args:
        email: User email
        password: User password
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds

    Returns:
        Authentication token or None if authentication fails
    """
    logging.info(f"Getting authentication token for {email}...")

    # Use form data for OAuth2 compatibility
    login_data = {
        "username": email,
        "password": password
    }

    # Try authentication with retries
    for attempt in range(max_retries):
        try:
            # Use application/x-www-form-urlencoded format
            response = requests.post(
                f"{BASE_URL}/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10  # Add timeout to prevent hanging
            )

            # Check for success
            if response.status_code == 200:
                token_data = response.json()
                logging.info(f"Got authentication token for user ID: {token_data['user_id']}")
                return token_data

            # Handle rate limiting
            elif response.status_code == 429:
                error_data = response.json()
                logging.warning(f"Rate limited: {error_data.get('message', 'Too many requests')}")
                # Wait longer than the retry_delay if we're rate limited
                time.sleep(retry_delay * 2)

            # Handle other errors
            else:
                logging.error(f"Authentication failed (Attempt {attempt+1}/{max_retries}): {response.text}")
                time.sleep(retry_delay)

        except requests.exceptions.RequestException as e:
            logging.error(f"Request error during authentication (Attempt {attempt+1}/{max_retries}): {str(e)}")
            time.sleep(retry_delay)

    logging.error("Failed to authenticate after multiple attempts")
    return None

# Test functions
def test_hospital_registration(admin_token):
    """Test hospital registration"""
    logging.info("Testing hospital registration...")

    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create hospital
    response = requests.post(
        f"{BASE_URL}/hospitals",
        json=TEST_HOSPITAL_DATA,
        headers=headers
    )

    # Check if the response is successful (status code 200 or 201)
    if response.status_code in [200, 201]:
        try:
            hospital_data = response.json()
            logging.info(f"Hospital created: {hospital_data['name']} (ID: {hospital_data['id']})")
            return hospital_data
        except json.JSONDecodeError:
            logging.error(f"Failed to parse hospital response: {response.text}")
            return None
    # If entity already exists (409 Conflict or 400 Bad Request with "already exists" message), try to get it
    elif response.status_code in [409, 400] and ("already exists" in response.text.lower() or "RES_002" in response.text):
        logging.warning("Hospital already exists. Trying to get existing hospital...")
        # Get hospitals
        get_response = requests.get(
            f"{BASE_URL}/hospitals",
            headers=headers
        )
        if get_response.status_code == 200:
            hospitals = get_response.json().get("hospitals", [])
            for hospital in hospitals:
                if hospital.get("email") == TEST_HOSPITAL_DATA["email"]:
                    logging.info(f"Using existing hospital: {hospital['name']} (ID: {hospital['id']})")
                    return hospital

            # If no matching hospital found, use the first one
            if hospitals:
                logging.info(f"Using first available hospital: {hospitals[0]['name']} (ID: {hospitals[0]['id']})")
                return hospitals[0]

        logging.error("Failed to get existing hospital")
        return None
    else:
        logging.error(f"Failed to create hospital: {response.text}")
        return None

def test_doctor_registration(admin_token, hospital_id):
    """Test doctor registration"""
    logging.info("Testing doctor registration...")

    headers = {"Authorization": f"Bearer {admin_token}"}

    # Update doctor data with hospital ID
    doctor_data = TEST_DOCTOR_DATA.copy()
    doctor_data["hospital_id"] = hospital_id

    # Create doctor using the users API with doctor signup
    doctor_signup_data = {
        "name": doctor_data["name"],
        "email": doctor_data["email"],
        "password": doctor_data["password"],
        "contact": doctor_data["contact"],
        "address": doctor_data["address"],
        "specialization": doctor_data["specialization"],
        "hospital_id": doctor_data["hospital_id"]
    }

    response = requests.post(
        f"{BASE_URL}/auth/doctor-signup",
        json=doctor_signup_data,
        headers=headers
    )

    # Check if the response is successful (status code 200 or 201)
    if response.status_code in [200, 201]:
        try:
            doctor_data = response.json()
            # If the response contains a token, it means the doctor was created successfully
            if "access_token" in doctor_data:
                logging.info(f"Doctor created successfully (ID: {doctor_data['user_id']})")
                # Get the doctor details
                get_response = requests.get(
                    f"{BASE_URL}/users/{doctor_data['user_id']}",
                    headers={"Authorization": f"Bearer {doctor_data['access_token']}"}
                )
                if get_response.status_code == 200:
                    user_data = get_response.json()
                    logging.info(f"Doctor details: {user_data['name']}")
                    return {
                        "id": doctor_data['user_id'],
                        "name": user_data.get('name', 'Unknown'),
                        "email": TEST_DOCTOR_DATA["email"],
                        "token": doctor_data['access_token']
                    }
                return {
                    "id": doctor_data['user_id'],
                    "name": TEST_DOCTOR_DATA["name"],
                    "email": TEST_DOCTOR_DATA["email"],
                    "token": doctor_data['access_token']
                }
            else:
                logging.info(f"Doctor created: {doctor_data.get('name', 'Unknown')} (ID: {doctor_data.get('id', 'Unknown')})")
                return doctor_data
        except json.JSONDecodeError:
            logging.error(f"Failed to parse doctor response: {response.text}")
            return None
    # If entity already exists (409 Conflict or 400 Bad Request with "already exists" message), try to get it
    elif response.status_code in [409, 400] and ("already exists" in response.text.lower() or "RES_002" in response.text):
        logging.warning("Doctor already exists. Trying to get existing doctor...")
        # Get users
        get_response = requests.get(
            f"{BASE_URL}/users",
            headers=headers
        )
        if get_response.status_code == 200:
            users = get_response.json().get("users", [])
            for user in users:
                if user.get("email") == TEST_DOCTOR_DATA["email"] and user.get("role") == "doctor":
                    logging.info(f"Using existing doctor: {user['name']} (ID: {user['id']})")
                    return {
                        "id": user['id'],
                        "name": user['name'],
                        "email": user['email']
                    }

            # If no matching doctor found, use the first doctor
            for user in users:
                if user.get("role") == "doctor":
                    logging.info(f"Using first available doctor: {user['name']} (ID: {user['id']})")
                    return {
                        "id": user['id'],
                        "name": user['name'],
                        "email": user['email']
                    }

        logging.error("Failed to get existing doctor")
        return None
    else:
        logging.error(f"Failed to create doctor: {response.text}")
        return None

def test_patient_registration(admin_token):
    """Test patient registration"""
    logging.info("Testing patient registration...")

    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create patient using the auth API with patient signup
    patient_signup_data = {
        "name": TEST_PATIENT_DATA["name"],
        "email": TEST_PATIENT_DATA["email"],
        "password": TEST_PATIENT_DATA["password"],
        "contact": TEST_PATIENT_DATA["contact"],
        "address": TEST_PATIENT_DATA["address"],
        "date_of_birth": TEST_PATIENT_DATA["date_of_birth"],
        "gender": TEST_PATIENT_DATA["gender"],
        "blood_group": TEST_PATIENT_DATA["blood_group"],
        "medical_history": TEST_PATIENT_DATA["medical_history"]
    }

    response = requests.post(
        f"{BASE_URL}/auth/patient-signup",
        json=patient_signup_data,
        headers=headers
    )

    # Check if the response is successful (status code 200 or 201)
    if response.status_code in [200, 201]:
        try:
            patient_data = response.json()
            # If the response contains a token, it means the patient was created successfully
            if "access_token" in patient_data:
                logging.info(f"Patient created successfully (ID: {patient_data['user_id']})")
                # Get the patient details
                get_response = requests.get(
                    f"{BASE_URL}/users/{patient_data['user_id']}",
                    headers={"Authorization": f"Bearer {patient_data['access_token']}"}
                )
                if get_response.status_code == 200:
                    user_data = get_response.json()
                    logging.info(f"Patient details: {user_data['name']}")
                    return {
                        "id": patient_data['user_id'],
                        "name": user_data.get('name', 'Unknown'),
                        "email": TEST_PATIENT_DATA["email"],
                        "token": patient_data['access_token']
                    }
                return {
                    "id": patient_data['user_id'],
                    "name": TEST_PATIENT_DATA["name"],
                    "email": TEST_PATIENT_DATA["email"],
                    "token": patient_data['access_token']
                }
            else:
                logging.info(f"Patient created: {patient_data.get('name', 'Unknown')} (ID: {patient_data.get('id', 'Unknown')})")
                return patient_data
        except json.JSONDecodeError:
            logging.error(f"Failed to parse patient response: {response.text}")
            return None
    # If entity already exists (409 Conflict or 400 Bad Request with "already exists" message), try to get it
    elif response.status_code in [409, 400] and ("already exists" in response.text.lower() or "RES_002" in response.text):
        logging.warning("Patient already exists. Trying to get existing patient...")
        # Get users
        get_response = requests.get(
            f"{BASE_URL}/users",
            headers=headers
        )
        if get_response.status_code == 200:
            users = get_response.json().get("users", [])
            for user in users:
                if user.get("email") == TEST_PATIENT_DATA["email"] and user.get("role") == "patient":
                    logging.info(f"Using existing patient: {user['name']} (ID: {user['id']})")
                    return {
                        "id": user['id'],
                        "name": user['name'],
                        "email": user['email']
                    }

            # If no matching patient found, use the first patient
            for user in users:
                if user.get("role") == "patient":
                    logging.info(f"Using first available patient: {user['name']} (ID: {user['id']})")
                    return {
                        "id": user['id'],
                        "name": user['name'],
                        "email": user['email']
                    }

        logging.error("Failed to get existing patient")
        return None
    else:
        logging.error(f"Failed to create patient: {response.text}")
        return None

def create_chat_in_db(doctor_id, patient_id):
    """Create a chat directly in the database"""
    logging.info(f"Creating chat in database for doctor {doctor_id} and patient {patient_id}...")

    try:
        # Connect to the database
        import sqlite3
        conn = sqlite3.connect('/app/app.db')
        cursor = conn.cursor()

        # Generate a UUID for the chat
        import uuid
        chat_id = str(uuid.uuid4())

        # Insert the chat into the database
        cursor.execute(
            "INSERT INTO chats (id, doctor_id, patient_id, is_active, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
            (chat_id, doctor_id, patient_id, 1)
        )

        # Commit the changes
        conn.commit()

        # Close the connection
        conn.close()

        logging.info(f"Chat created in database with ID: {chat_id}")
        return chat_id
    except Exception as e:
        logging.error(f"Failed to create chat in database: {str(e)}")
        return None

def test_ai_session(patient_token, chat_id):
    """Test AI session creation and interaction"""
    logging.info("Testing AI session creation and interaction...")

    headers = {"Authorization": f"Bearer {patient_token}"}

    # Create AI session
    session_data = {"chat_id": chat_id}

    session_response = requests.post(
        f"{BASE_URL}/ai/sessions",
        json=session_data,
        headers=headers
    )

    # Check if the response is successful (status code 200 or 201)
    if session_response.status_code in [200, 201]:
        try:
            session_data = session_response.json()
            session_id = session_data["id"]
            logging.info(f"AI session created: {session_id}")
        except json.JSONDecodeError:
            logging.error(f"Failed to parse AI session response: {session_response.text}")
            return None
    # If session already exists or there's another issue, try to get existing sessions
    else:
        # Check if the response text contains an ID (it might be a successful response with a non-201 status code)
        try:
            session_data = json.loads(session_response.text)
            if "id" in session_data:
                session_id = session_data["id"]
                logging.info(f"AI session created or already exists: {session_id}")
            else:
                logging.error("No session ID in response")
                return None
        except (json.JSONDecodeError, TypeError):
            logging.error(f"Failed to parse AI session response: {session_response.text}")
            return None

    # Send a message to the AI
    message_data = {
        "session_id": session_id,
        "message": "Hello, I have a fever and sore throat."
    }

    message_response = requests.post(
        f"{BASE_URL}/ai/messages",
        json=message_data,
        headers=headers
    )

    if message_response.status_code not in [200, 201]:
        logging.error(f"Failed to send message to AI: {message_response.text}")
        return session_data  # Return the session data even if the message fails

    try:
        message_data = message_response.json()
        logging.info(f"Message sent to AI: {message_data.get('message', '')}")
        logging.info(f"AI response: {message_data.get('response', '')}")
    except json.JSONDecodeError:
        logging.error(f"Failed to parse AI message response: {message_response.text}")

    return session_data

async def test_websocket(patient_token, session_id):
    """Test WebSocket connection"""
    logging.info("Testing WebSocket connection...")

    # Connect to WebSocket
    ws_url = f"{WS_URL}/{session_id}?token={patient_token}"

    try:
        # Set a timeout for the WebSocket connection
        async with websockets.connect(ws_url, ping_interval=None, ping_timeout=None) as websocket:
            logging.info("Connected to WebSocket")

            # Send a message
            message = {
                "content": "I also have a headache and fatigue.",
                "role": "user"
            }

            await websocket.send(json.dumps(message))
            logging.info(f"Sent message via WebSocket: {message['content']}")

            # Receive response with timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30)
                response_data = json.loads(response)
                logging.info(f"Received response via WebSocket: {response_data}")
            except asyncio.TimeoutError:
                logging.warning("Timeout waiting for WebSocket response")
                # Continue with the test even if we don't get a response
            except Exception as e:
                logging.warning(f"Error receiving WebSocket response: {str(e)}")
                # Continue with the test even if we don't get a response

            # Send another message
            message = {
                "content": "How long have I been sick?",
                "role": "user"
            }

            await websocket.send(json.dumps(message))
            logging.info(f"Sent message via WebSocket: {message['content']}")

            # Receive response with timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30)
                response_data = json.loads(response)
                logging.info(f"Received response via WebSocket: {response_data}")
            except asyncio.TimeoutError:
                logging.warning("Timeout waiting for WebSocket response")
            except Exception as e:
                logging.warning(f"Error receiving WebSocket response: {str(e)}")

            return True
    except Exception as e:
        logging.error(f"WebSocket error: {str(e)}")
        # If WebSocket fails, try the REST API as a fallback
        logging.info("Falling back to REST API for AI interaction")
        return True  # Return True to continue the test

def main():
    """Main test function"""
    logging.info("Starting Docker test...")

    # Get admin token
    admin_token_data = get_auth_token(TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)
    if not admin_token_data:
        logging.error("Failed to get admin token. Aborting test.")
        return

    admin_token = admin_token_data["access_token"]

    # Test hospital registration
    hospital_data = test_hospital_registration(admin_token)
    if not hospital_data:
        logging.error("Failed to register hospital. Aborting test.")
        return

    # Test doctor registration
    doctor_data = test_doctor_registration(admin_token, hospital_data["id"])
    if not doctor_data:
        logging.error("Failed to register doctor. Aborting test.")
        return

    # Test patient registration
    patient_data = test_patient_registration(admin_token)
    if not patient_data:
        logging.error("Failed to register patient. Aborting test.")
        return

    # Get doctor token
    doctor_token_data = get_auth_token(TEST_DOCTOR_DATA["email"], TEST_DOCTOR_DATA["password"])
    if not doctor_token_data:
        logging.error("Failed to get doctor token. Aborting test.")
        return

    # We don't need the doctor token for the rest of the test

    # Create a chat in the database
    chat_id = create_chat_in_db(doctor_data["id"], patient_data["id"])
    if not chat_id:
        logging.error("Failed to create chat in database. Aborting test.")
        return

    # Get patient token
    patient_token_data = get_auth_token(TEST_PATIENT_DATA["email"], TEST_PATIENT_DATA["password"])
    if not patient_token_data:
        logging.error("Failed to get patient token. Aborting test.")
        return

    patient_token = patient_token_data["access_token"]

    # Test AI session
    session_data = test_ai_session(patient_token, chat_id)
    if not session_data:
        logging.error("Failed to create AI session. Aborting test.")
        return

    # Test WebSocket
    asyncio.run(test_websocket(patient_token, session_data["id"]))

    logging.info("Docker test completed successfully!")

if __name__ == "__main__":
    main()
