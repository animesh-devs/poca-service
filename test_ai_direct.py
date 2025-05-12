import requests
import json
import logging
import sys
import time
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# API base URL
BASE_URL = "http://localhost:8001/api/v1"

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
        "username": "admin@example.com",
        "password": "password123"  # This is the correct password based on the hash in simple_init_db.py
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

def test_ai_direct():
    """Test AI API endpoints directly with authentication"""
    logging.info("Starting direct AI API tests...")

    # Get authentication token
    token = get_auth_token()
    if not token:
        logging.error("Failed to get authentication token. Aborting test.")
        return

    # Get the chat ID from the database
    # First, try to get an existing chat
    try:
        chat_response = requests.get(
            f"{BASE_URL}/chats",
            headers={"Authorization": f"Bearer {token}"}
        )

        if chat_response.status_code == 200 and len(chat_response.json()["chats"]) > 0:
            chat_id = chat_response.json()["chats"][0]["id"]
            logging.info(f"Using existing chat ID: {chat_id}")
        else:
            # If no chat exists, use a random chat ID
            chat_id = str(uuid.uuid4())
            logging.info(f"No existing chats found. Using random chat ID: {chat_id}")
    except Exception as e:
        # If there's an error, use a random chat ID
        chat_id = str(uuid.uuid4())
        logging.info(f"Error getting chats: {str(e)}. Using random chat ID: {chat_id}")

    try:
        # 1. Create an AI session
        logging.info("Creating AI session...")
        session_data = {"chat_id": chat_id}

        session_response = requests.post(
            f"{BASE_URL}/ai/sessions",
            json=session_data,
            headers={"Authorization": f"Bearer {token}"}
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
            headers={"Authorization": f"Bearer {token}"}
        )

        if message_response.status_code != 200:
            logging.error(f"Failed to send message to AI: {message_response.text}")
            return

        message_id = message_response.json()["id"]
        ai_response = message_response.json()["response"]

        logging.info(f"Sent message to AI. Message ID: {message_id}")
        logging.info(f"AI Response: {ai_response}")

        # 3. Send a follow-up message
        logging.info("Sending follow-up message to AI...")
        follow_up_data = {
            "session_id": session_id,
            "message": "What treatments are recommended for the flu?"
        }

        follow_up_response = requests.post(
            f"{BASE_URL}/ai/messages",
            json=follow_up_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        if follow_up_response.status_code != 200:
            logging.error(f"Failed to send follow-up message to AI: {follow_up_response.text}")
            return

        follow_up_id = follow_up_response.json()["id"]
        follow_up_ai_response = follow_up_response.json()["response"]

        logging.info(f"Sent follow-up message to AI. Message ID: {follow_up_id}")
        logging.info(f"AI Response: {follow_up_ai_response}")

        # 4. Get all messages for the session
        logging.info("Getting AI messages...")

        messages_response = requests.get(
            f"{BASE_URL}/ai/sessions/{session_id}/messages",
            headers={"Authorization": f"Bearer {token}"}
        )

        if messages_response.status_code != 200:
            logging.error(f"Failed to get AI messages: {messages_response.text}")
            return

        messages = messages_response.json()["messages"]
        logging.info(f"Retrieved {len(messages)} messages for the session")

        # Print all messages
        for i, msg in enumerate(messages):
            logging.info(f"Message {i+1}:")
            logging.info(f"  User: {msg['message']}")
            logging.info(f"  AI: {msg['response']}")

        # 5. End the AI session
        logging.info("Ending AI session...")

        end_session_response = requests.put(
            f"{BASE_URL}/ai/sessions/{session_id}/end",
            headers={"Authorization": f"Bearer {token}"}
        )

        if end_session_response.status_code != 200:
            logging.error(f"Failed to end AI session: {end_session_response.text}")
            return

        logging.info(f"Successfully ended AI session with ID: {session_id}")

        logging.info("All direct AI API tests completed successfully!")

    except requests.exceptions.ConnectionError:
        logging.error("Failed to connect to the API. Make sure the server is running.")
    except Exception as e:
        logging.error(f"Error testing AI endpoints: {str(e)}")

if __name__ == "__main__":
    test_ai_direct()
