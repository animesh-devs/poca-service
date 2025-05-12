import asyncio
import websockets
import json
import logging
import sys
import time
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Load environment variables
load_dotenv()

# API base URL
BASE_URL = "http://localhost:8001/api/v1"
WS_URL = "ws://localhost:8001/api/v1/ai-assistant/ws"

# Test user credentials
TEST_EMAIL = "admin@example.com"
TEST_PASSWORD = "password123"  # This is the correct password based on the hash in simple_init_db.py

def get_auth_token(max_retries=3, retry_delay=2):
    """
    Get authentication token with retry logic

    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds

    Returns:
        Authentication token or None if authentication fails
    """
    logging.info("Getting authentication token...")

    # Use form data for OAuth2 compatibility
    login_data = {
        "username": TEST_EMAIL,
        "password": TEST_PASSWORD  # This is the correct password based on the hash in simple_init_db.py
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
                return token_data["access_token"]

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

def create_ai_session(token, chat_id):
    """Create an AI session"""
    logging.info("Creating AI session...")

    headers = {"Authorization": f"Bearer {token}"}
    session_data = {"chat_id": chat_id}

    response = requests.post(
        f"{BASE_URL}/ai/sessions",
        json=session_data,
        headers=headers
    )

    if response.status_code != 200:
        logging.error(f"Failed to create AI session: {response.text}")
        return None

    session_id = response.json()["id"]
    logging.info(f"Created AI session with ID: {session_id}")

    return session_id

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

async def test_websocket():
    """Test WebSocket connection to AI assistant"""
    # Get authentication token
    token = get_auth_token()
    if not token:
        logging.error("Failed to get authentication token. Aborting test.")
        return

    # Get or create a chat
    chat_id = get_or_create_chat(token)
    if not chat_id:
        logging.error("Failed to get or create a chat. Aborting test.")
        return

    # Create an AI session
    session_id = create_ai_session(token, chat_id)
    if not session_id:
        logging.error("Failed to create AI session. Aborting test.")
        return

    # Connect to WebSocket
    ws_url = f"{WS_URL}/{session_id}?token={token}"
    logging.info(f"Connecting to WebSocket at {ws_url}")

    try:
        async with websockets.connect(ws_url) as websocket:
            # Receive welcome message
            response = await websocket.recv()
            logging.info(f"Received: {response}")

            # Test messages
            test_messages = [
                "Hello, I'm not feeling well today.",
                "I have a fever and a sore throat.",
                "What could be wrong with me?",
                "What treatment do you recommend?",
                "Thank you for your help."
            ]

            for message in test_messages:
                # Send message
                message_data = {"message": message}
                await websocket.send(json.dumps(message_data))
                logging.info(f"Sent: {message}")

                # Receive response
                response = await websocket.recv()
                logging.info(f"Received: {response}")

                # If this is a status message, wait for the actual response
                response_data = json.loads(response)
                if response_data.get("type") == "status":
                    response = await websocket.recv()
                    logging.info(f"Received: {response}")

                    # Parse the response to extract the JSON content
                    response_data = json.loads(response)
                    if response_data.get("type") == "ai_response":
                        content = response_data.get("content", {})
                        message = content.get("message", "")
                        is_summary = content.get("isSummary", False)
                        logging.info(f"Message: {message}")
                        logging.info(f"Is Summary: {is_summary}")

                        # If this is a summary, wait for the summary notification
                        if is_summary:
                            summary_notification = await websocket.recv()
                            logging.info(f"Summary Notification: {summary_notification}")

                # Wait a bit before sending the next message
                await asyncio.sleep(1)

            logging.info("WebSocket test completed successfully!")

    except Exception as e:
        logging.error(f"Error in WebSocket test: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
