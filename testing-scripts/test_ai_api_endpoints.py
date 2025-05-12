import requests
import json
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

# Test data
TEST_EMAIL = "admin@example.com"
TEST_PASSWORD = "password123"

def get_auth_token():
    """Get authentication token"""
    logging.info("Getting authentication token...")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    
    if response.status_code != 200:
        logging.error(f"Failed to get authentication token: {response.text}")
        return None
    
    token_data = response.json()
    logging.info(f"Got authentication token for user ID: {token_data['user_id']}")
    
    return token_data["access_token"]

def create_test_chat(token):
    """Create a test chat between a doctor and patient"""
    logging.info("Creating test chat...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get a doctor
    doctors_response = requests.get(f"{BASE_URL}/doctors", headers=headers)
    if doctors_response.status_code != 200:
        logging.error(f"Failed to get doctors: {doctors_response.text}")
        return None
    
    doctors = doctors_response.json()["doctors"]
    if not doctors:
        logging.error("No doctors found")
        return None
    
    doctor_id = doctors[0]["id"]
    logging.info(f"Using doctor ID: {doctor_id}")
    
    # Get a patient
    patients_response = requests.get(f"{BASE_URL}/patients", headers=headers)
    if patients_response.status_code != 200:
        logging.error(f"Failed to get patients: {patients_response.text}")
        return None
    
    patients = patients_response.json()["patients"]
    if not patients:
        logging.error("No patients found")
        return None
    
    patient_id = patients[0]["id"]
    logging.info(f"Using patient ID: {patient_id}")
    
    # Create chat
    chat_data = {
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "is_active": True
    }
    
    chat_response = requests.post(
        f"{BASE_URL}/chats",
        json=chat_data,
        headers=headers
    )
    
    if chat_response.status_code != 200:
        logging.error(f"Failed to create chat: {chat_response.text}")
        return None
    
    chat_id = chat_response.json()["id"]
    logging.info(f"Created chat with ID: {chat_id}")
    
    return chat_id

def test_ai_endpoints():
    """Test AI API endpoints"""
    # Get authentication token
    token = get_auth_token()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a test chat
    chat_id = create_test_chat(token)
    if not chat_id:
        return
    
    # 1. Create an AI session
    logging.info("Creating AI session...")
    session_data = {"chat_id": chat_id}
    
    session_response = requests.post(
        f"{BASE_URL}/ai/sessions",
        json=session_data,
        headers=headers
    )
    
    if session_response.status_code != 200:
        logging.error(f"Failed to create AI session: {session_response.text}")
        return
    
    session_id = session_response.json()["id"]
    logging.info(f"Created AI session with ID: {session_id}")
    
    # 2. Send a message to the AI
    logging.info("Sending message to AI...")
    message_data = {
        "session_id": session_id,
        "message": "What are the symptoms of the flu?"
    }
    
    message_response = requests.post(
        f"{BASE_URL}/ai/messages",
        json=message_data,
        headers=headers
    )
    
    if message_response.status_code != 200:
        logging.error(f"Failed to send message to AI: {message_response.text}")
        return
    
    message_id = message_response.json()["id"]
    ai_response = message_response.json()["response"]
    
    logging.info(f"Sent message to AI. Message ID: {message_id}")
    logging.info(f"AI Response: {ai_response}")
    
    # 3. Get all messages for the session
    logging.info("Getting AI messages...")
    
    messages_response = requests.get(
        f"{BASE_URL}/ai/sessions/{session_id}/messages",
        headers=headers
    )
    
    if messages_response.status_code != 200:
        logging.error(f"Failed to get AI messages: {messages_response.text}")
        return
    
    messages = messages_response.json()["messages"]
    logging.info(f"Retrieved {len(messages)} messages for the session")
    
    # 4. End the AI session
    logging.info("Ending AI session...")
    
    end_session_response = requests.put(
        f"{BASE_URL}/ai/sessions/{session_id}/end",
        headers=headers
    )
    
    if end_session_response.status_code != 200:
        logging.error(f"Failed to end AI session: {end_session_response.text}")
        return
    
    logging.info(f"Successfully ended AI session with ID: {session_id}")
    
    logging.info("All AI API tests completed successfully!")

if __name__ == "__main__":
    test_ai_endpoints()
