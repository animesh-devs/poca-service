import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

# Test user credentials
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "password123"

# Function to get authentication token
def get_auth_token():
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    
    if response.status_code != 200:
        print(f"Authentication failed: {response.text}")
        return None
    
    return response.json()["access_token"]

# Function to create a test chat
def create_test_chat(token):
    headers = {"Authorization": f"Bearer {token}"}
    
    # First, get a doctor and patient ID
    doctors_response = requests.get(f"{BASE_URL}/hospitals/1/doctors", headers=headers)
    if doctors_response.status_code != 200:
        print(f"Failed to get doctors: {doctors_response.text}")
        return None
    
    doctor_id = doctors_response.json()["doctors"][0]["id"]
    
    patients_response = requests.get(f"{BASE_URL}/hospitals/1/patients", headers=headers)
    if patients_response.status_code != 200:
        print(f"Failed to get patients: {patients_response.text}")
        return None
    
    patient_id = patients_response.json()["patients"][0]["id"]
    
    # Create a chat
    chat_data = {
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "is_active": True
    }
    
    chat_response = requests.post(f"{BASE_URL}/chats", json=chat_data, headers=headers)
    if chat_response.status_code != 200:
        print(f"Failed to create chat: {chat_response.text}")
        return None
    
    return chat_response.json()["id"]

# Test AI API endpoints
def test_ai_api():
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("Failed to get authentication token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a test chat
    chat_id = create_test_chat(token)
    if not chat_id:
        print("Failed to create test chat")
        return
    
    print(f"Created test chat with ID: {chat_id}")
    
    # 1. Create an AI session
    session_data = {"chat_id": chat_id}
    session_response = requests.post(f"{BASE_URL}/ai/sessions", json=session_data, headers=headers)
    
    if session_response.status_code != 200:
        print(f"Failed to create AI session: {session_response.text}")
        return
    
    session_id = session_response.json()["id"]
    print(f"Created AI session with ID: {session_id}")
    
    # 2. Send a message to the AI
    message_data = {
        "session_id": session_id,
        "message": "What are the symptoms of the flu?"
    }
    
    message_response = requests.post(f"{BASE_URL}/ai/messages", json=message_data, headers=headers)
    
    if message_response.status_code != 200:
        print(f"Failed to send message to AI: {message_response.text}")
        return
    
    message_id = message_response.json()["id"]
    ai_response = message_response.json()["response"]
    
    print(f"Sent message to AI. Message ID: {message_id}")
    print(f"AI Response: {ai_response}")
    
    # 3. Get all messages for the session
    messages_response = requests.get(f"{BASE_URL}/ai/sessions/{session_id}/messages", headers=headers)
    
    if messages_response.status_code != 200:
        print(f"Failed to get AI messages: {messages_response.text}")
        return
    
    messages = messages_response.json()["messages"]
    print(f"Retrieved {len(messages)} messages for the session")
    
    # 4. End the AI session
    end_session_response = requests.put(f"{BASE_URL}/ai/sessions/{session_id}/end", headers=headers)
    
    if end_session_response.status_code != 200:
        print(f"Failed to end AI session: {end_session_response.text}")
        return
    
    print(f"Successfully ended AI session with ID: {session_id}")
    
    print("All AI API tests completed successfully!")

if __name__ == "__main__":
    test_ai_api()
