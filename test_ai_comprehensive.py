import requests
import json
import logging
import sys
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

# Test user credentials
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

def initialize_database():
    """Initialize the database with test data"""
    logging.info("Initializing database with test data...")
    
    try:
        # Run the database initialization script
        import simple_init_db
        chat_id = simple_init_db.create_test_data()
        logging.info(f"Database initialized with test chat ID: {chat_id}")
        return chat_id
    except Exception as e:
        logging.error(f"Failed to initialize database: {str(e)}")
        return None

def get_or_create_chat(token):
    """Get an existing chat or create a new one"""
    logging.info("Getting or creating a chat...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to get existing chats
    chats_response = requests.get(f"{BASE_URL}/chats", headers=headers)
    
    if chats_response.status_code == 200 and chats_response.json()["total"] > 0:
        chat_id = chats_response.json()["chats"][0]["id"]
        logging.info(f"Using existing chat with ID: {chat_id}")
        return chat_id
    
    # If no chats exist, create a new one
    # First, get a doctor
    doctors_response = requests.get(f"{BASE_URL}/doctors", headers=headers)
    if doctors_response.status_code != 200 or doctors_response.json()["total"] == 0:
        logging.error("No doctors found")
        return None
    
    doctor_id = doctors_response.json()["doctors"][0]["id"]
    
    # Then, get a patient
    patients_response = requests.get(f"{BASE_URL}/patients", headers=headers)
    if patients_response.status_code != 200 or patients_response.json()["total"] == 0:
        logging.error("No patients found")
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
        logging.error(f"Failed to create chat: {chat_response.text}")
        return None
    
    chat_id = chat_response.json()["id"]
    logging.info(f"Created new chat with ID: {chat_id}")
    
    return chat_id

def test_ai_session_lifecycle(token, chat_id):
    """Test the complete lifecycle of an AI session"""
    logging.info("Testing AI session lifecycle...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
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
        return False
    
    session_id = session_response.json()["id"]
    logging.info(f"Created AI session with ID: {session_id}")
    
    # 2. Send multiple messages to the AI
    test_messages = [
        "Hello, I'm not feeling well today.",
        "I have a fever and a sore throat.",
        "What could be wrong with me?",
        "What treatment do you recommend?",
        "Thank you for your help."
    ]
    
    for i, message in enumerate(test_messages):
        logging.info(f"Sending message {i+1}/{len(test_messages)}: '{message}'")
        
        message_data = {
            "session_id": session_id,
            "message": message
        }
        
        message_response = requests.post(
            f"{BASE_URL}/ai/messages",
            json=message_data,
            headers=headers
        )
        
        if message_response.status_code != 200:
            logging.error(f"Failed to send message to AI: {message_response.text}")
            return False
        
        message_id = message_response.json()["id"]
        ai_response = message_response.json()["response"]
        
        logging.info(f"Message ID: {message_id}")
        logging.info(f"AI Response: {ai_response}")
        
        # Add a small delay between messages
        time.sleep(1)
    
    # 3. Get all messages for the session
    logging.info("Getting all AI messages...")
    
    messages_response = requests.get(
        f"{BASE_URL}/ai/sessions/{session_id}/messages",
        headers=headers
    )
    
    if messages_response.status_code != 200:
        logging.error(f"Failed to get AI messages: {messages_response.text}")
        return False
    
    messages = messages_response.json()["messages"]
    logging.info(f"Retrieved {len(messages)} messages for the session")
    
    # Print all messages
    for i, msg in enumerate(messages):
        logging.info(f"Message {i+1}:")
        logging.info(f"  User: {msg['message']}")
        logging.info(f"  AI: {msg['response']}")
    
    # 4. Get the session details
    logging.info("Getting AI session details...")
    
    session_details_response = requests.get(
        f"{BASE_URL}/ai/sessions/{session_id}",
        headers=headers
    )
    
    if session_details_response.status_code != 200:
        logging.error(f"Failed to get AI session details: {session_details_response.text}")
        return False
    
    session_details = session_details_response.json()
    logging.info(f"Session details: {json.dumps(session_details, indent=2)}")
    
    # 5. End the AI session
    logging.info("Ending AI session...")
    
    end_session_response = requests.put(
        f"{BASE_URL}/ai/sessions/{session_id}/end",
        headers=headers
    )
    
    if end_session_response.status_code != 200:
        logging.error(f"Failed to end AI session: {end_session_response.text}")
        return False
    
    ended_session = end_session_response.json()
    logging.info(f"Successfully ended AI session with ID: {ended_session['id']}")
    logging.info(f"Session end timestamp: {ended_session['end_timestamp']}")
    
    return True

def run_comprehensive_tests():
    """Run all tests"""
    logging.info("Starting comprehensive AI API tests...")
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        logging.error("Failed to get authentication token. Aborting tests.")
        return
    
    # Get or create a chat
    chat_id = get_or_create_chat(token)
    if not chat_id:
        logging.error("Failed to get or create a chat. Aborting tests.")
        return
    
    # Test AI session lifecycle
    if test_ai_session_lifecycle(token, chat_id):
        logging.info("AI session lifecycle test completed successfully!")
    else:
        logging.error("AI session lifecycle test failed.")
    
    logging.info("All tests completed.")

if __name__ == "__main__":
    run_comprehensive_tests()
