import requests
import json
import logging
import sys
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def test_ai_endpoints():
    """Test AI API endpoints directly"""
    
    # Create a test chat ID (this would normally come from the database)
    chat_id = str(uuid.uuid4())
    logging.info(f"Using test chat ID: {chat_id}")
    
    # 1. Create an AI session
    logging.info("Creating AI session...")
    session_data = {"chat_id": chat_id}
    
    try:
        session_response = requests.post(
            f"{BASE_URL}/ai/sessions",
            json=session_data
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
            json=message_data
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
            f"{BASE_URL}/ai/sessions/{session_id}/messages"
        )
        
        if messages_response.status_code != 200:
            logging.error(f"Failed to get AI messages: {messages_response.text}")
            return
        
        messages = messages_response.json()["messages"]
        logging.info(f"Retrieved {len(messages)} messages for the session")
        
        # 4. End the AI session
        logging.info("Ending AI session...")
        
        end_session_response = requests.put(
            f"{BASE_URL}/ai/sessions/{session_id}/end"
        )
        
        if end_session_response.status_code != 200:
            logging.error(f"Failed to end AI session: {end_session_response.text}")
            return
        
        logging.info(f"Successfully ended AI session with ID: {session_id}")
        
        logging.info("All AI API tests completed successfully!")
    
    except requests.exceptions.ConnectionError:
        logging.error("Failed to connect to the API. Make sure the server is running.")
    except Exception as e:
        logging.error(f"Error testing AI endpoints: {str(e)}")

if __name__ == "__main__":
    test_ai_endpoints()
