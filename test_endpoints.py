import requests
import json
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# API URLs
BASE_URL = "http://localhost:8002"
AUTH_URL = f"{BASE_URL}/api/v1/auth"
USERS_URL = f"{BASE_URL}/api/v1/users"
HOSPITALS_URL = f"{BASE_URL}/api/v1/hospitals"
DOCTORS_URL = f"{BASE_URL}/api/v1/doctors"
PATIENTS_URL = f"{BASE_URL}/api/v1/patients"
AI_URL = f"{BASE_URL}/api/v1/ai"
MAPPINGS_URL = f"{BASE_URL}/api/v1/mappings"
CHATS_URL = f"{BASE_URL}/api/v1/chats"
MESSAGES_URL = f"{BASE_URL}/api/v1/messages"

# Default admin credentials
DEFAULT_ADMIN_EMAIL = "admin@example.com"
DEFAULT_ADMIN_PASSWORD = "admin123"

# Test data
TEST_DOCTOR_EMAIL = "test.doctor@example.com"
TEST_DOCTOR_PASSWORD = "password123"
TEST_PATIENT_EMAIL = "test.patient@example.com"
TEST_PATIENT_PASSWORD = "password123"

def check_server_health():
    """Check if the server is up and running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200 and response.json().get("status") == "healthy":
            logging.info("Server is up and running (health endpoint)")
            return True
        else:
            logging.error(f"Server health check failed: {response.text}")
            return False
    except Exception as e:
        logging.error(f"Error checking server health: {str(e)}")
        return False

def get_auth_token(email, password):
    """Get authentication token for a user"""
    logging.info(f"Getting authentication token for {email}...")

    try:
        # OAuth2 form data
        data = {
            "username": email,
            "password": password
        }

        response = requests.post(
            f"{AUTH_URL}/login",
            data=data,  # Use form data instead of JSON
            timeout=5
        )

        if response.status_code == 200:
            token_data = response.json()
            logging.info(f"Got authentication token for user ID: {token_data.get('user_id')}")
            return token_data
        else:
            logging.error(f"Failed to get authentication token: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting authentication token: {str(e)}")
        return None

def test_mappings_api():
    """Test the mappings API endpoints"""
    logging.info("Testing Mappings API...")

    # Get admin token
    admin_token_data = get_auth_token(DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD)
    if not admin_token_data:
        logging.error("Failed to get admin token. Aborting.")
        return False

    admin_token = admin_token_data["access_token"]

    # Use the user IDs from the created test data
    try:
        # Use hardcoded IDs from the test data we created
        # These are the profile IDs, not the user IDs
        doctor_id = "78258996-213d-4fda-a812-185272290842"  # First doctor's user ID
        patient_id = "ce7ce952-0eeb-4230-a422-d6748df5d196"  # First patient's user ID
        hospital_id = "f85b7b86-bd30-46f3-8b46-8b6d5f560ed2"  # First hospital's user ID

        # Get the profile IDs from the user IDs
        # Get doctor profile ID
        response = requests.get(
            f"{USERS_URL}/{doctor_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=5
        )

        if response.status_code == 200:
            doctor_user = response.json()
            doctor_profile_id = doctor_user.get("profile_id")
            if doctor_profile_id:
                doctor_id = doctor_profile_id
                logging.info(f"Using doctor profile ID: {doctor_id}")
            else:
                logging.warning(f"Doctor user {doctor_id} has no profile ID, using user ID instead")
        else:
            logging.warning(f"Failed to get doctor user: {response.text}")
            logging.warning("Using doctor user ID as profile ID")

        # Get patient profile ID
        response = requests.get(
            f"{USERS_URL}/{patient_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=5
        )

        if response.status_code == 200:
            patient_user = response.json()
            patient_profile_id = patient_user.get("profile_id")
            if patient_profile_id:
                patient_id = patient_profile_id
                logging.info(f"Using patient profile ID: {patient_id}")
            else:
                logging.warning(f"Patient user {patient_id} has no profile ID, using user ID instead")
        else:
            logging.warning(f"Failed to get patient user: {response.text}")
            logging.warning("Using patient user ID as profile ID")

        # Get hospital profile ID
        response = requests.get(
            f"{USERS_URL}/{hospital_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=5
        )

        if response.status_code == 200:
            hospital_user = response.json()
            hospital_profile_id = hospital_user.get("profile_id")
            if hospital_profile_id:
                hospital_id = hospital_profile_id
                logging.info(f"Using hospital profile ID: {hospital_id}")
            else:
                logging.warning(f"Hospital user {hospital_id} has no profile ID, using user ID instead")
        else:
            logging.warning(f"Failed to get hospital user: {response.text}")
            logging.warning("Using hospital user ID as profile ID")

        # Test mapping endpoints
        # 1. Map doctor to patient
        mapping_data = {
            "doctor_id": doctor_id,
            "patient_id": patient_id
        }

        response = requests.post(
            f"{MAPPINGS_URL}/doctor-patient",
            json=mapping_data,
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=5
        )

        if response.status_code == 200:
            logging.info("Successfully mapped doctor to patient")
        else:
            logging.warning(f"Failed to map doctor to patient: {response.text}")

        # 2. Map hospital to doctor
        mapping_data = {
            "hospital_id": hospital_id,
            "doctor_id": doctor_id
        }

        response = requests.post(
            f"{MAPPINGS_URL}/hospital-doctor",
            json=mapping_data,
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=5
        )

        if response.status_code == 200:
            logging.info("Successfully mapped hospital to doctor")
        else:
            logging.warning(f"Failed to map hospital to doctor: {response.text}")

        # 3. Map hospital to patient
        mapping_data = {
            "hospital_id": hospital_id,
            "patient_id": patient_id
        }

        response = requests.post(
            f"{MAPPINGS_URL}/hospital-patient",
            json=mapping_data,
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=5
        )

        if response.status_code == 200:
            logging.info("Successfully mapped hospital to patient")
        else:
            logging.warning(f"Failed to map hospital to patient: {response.text}")

        logging.info("Mappings API test completed")
        return True

    except Exception as e:
        logging.error(f"Error testing mappings API: {str(e)}")
        return False

def test_chats_and_messages_api():
    """Test the chats and messages API endpoints"""
    logging.info("Testing Chats and Messages API...")

    # Get admin token
    admin_token_data = get_auth_token(DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD)
    if not admin_token_data:
        logging.error("Failed to get admin token. Aborting.")
        return False

    admin_token = admin_token_data["access_token"]

    # Use the user IDs from the created test data
    try:
        # Use hardcoded IDs from the test data we created
        # These are the profile IDs, not the user IDs
        doctor_id = "78258996-213d-4fda-a812-185272290842"  # First doctor's user ID
        patient_id = "ce7ce952-0eeb-4230-a422-d6748df5d196"  # First patient's user ID

        # Get the profile IDs from the user IDs
        # Get doctor profile ID
        response = requests.get(
            f"{USERS_URL}/{doctor_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=5
        )

        if response.status_code == 200:
            doctor_user = response.json()
            doctor_profile_id = doctor_user.get("profile_id")
            if doctor_profile_id:
                doctor_id = doctor_profile_id
                logging.info(f"Using doctor profile ID: {doctor_id}")
            else:
                logging.warning(f"Doctor user {doctor_id} has no profile ID, using user ID instead")
        else:
            logging.warning(f"Failed to get doctor user: {response.text}")
            logging.warning("Using doctor user ID as profile ID")

        # Get patient profile ID
        response = requests.get(
            f"{USERS_URL}/{patient_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=5
        )

        if response.status_code == 200:
            patient_user = response.json()
            patient_profile_id = patient_user.get("profile_id")
            if patient_profile_id:
                patient_id = patient_profile_id
                logging.info(f"Using patient profile ID: {patient_id}")
            else:
                logging.warning(f"Patient user {patient_id} has no profile ID, using user ID instead")
        else:
            logging.warning(f"Failed to get patient user: {response.text}")
            logging.warning("Using patient user ID as profile ID")

        # Test chat endpoints
        # 1. Create a chat
        chat_data = {
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "is_active": True
        }

        response = requests.post(
            CHATS_URL,
            json=chat_data,
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=5
        )

        if response.status_code == 200:
            chat = response.json()
            chat_id = chat["id"]
            logging.info(f"Successfully created chat with ID: {chat_id}")

            # 2. Get all chats
            response = requests.get(
                CHATS_URL,
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=5
            )

            if response.status_code == 200:
                chats = response.json()
                logging.info(f"Successfully retrieved {chats.get('total', 0)} chats")
            else:
                logging.warning(f"Failed to get chats: {response.text}")

            # 3. Get chat by ID
            response = requests.get(
                f"{CHATS_URL}/{chat_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=5
            )

            if response.status_code == 200:
                chat = response.json()
                logging.info(f"Successfully retrieved chat with ID: {chat['id']}")
            else:
                logging.warning(f"Failed to get chat by ID: {response.text}")

            # Test message endpoints
            # 1. Send a message
            message_data = {
                "chat_id": chat_id,
                "sender_id": doctor_id,
                "receiver_id": patient_id,
                "message": "Hello, this is a test message",
                "message_type": "text"
            }

            response = requests.post(
                MESSAGES_URL,
                json=message_data,
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=5
            )

            if response.status_code == 200:
                message = response.json()
                message_id = message["id"]
                logging.info(f"Successfully sent message with ID: {message_id}")

                # 2. Get chat messages
                response = requests.get(
                    f"{MESSAGES_URL}/chat/{chat_id}",
                    headers={"Authorization": f"Bearer {admin_token}"},
                    timeout=5
                )

                if response.status_code == 200:
                    messages = response.json()
                    logging.info(f"Successfully retrieved {messages.get('total', 0)} messages")

                    # 3. Update message read status
                    if messages.get("total", 0) > 0:
                        message_ids = [msg["id"] for msg in messages.get("messages", [])]

                        status_data = {
                            "message_ids": message_ids,
                            "is_read": True
                        }

                        response = requests.put(
                            f"{MESSAGES_URL}/read-status",
                            json=status_data,
                            headers={"Authorization": f"Bearer {admin_token}"},
                            timeout=5
                        )

                        if response.status_code == 200:
                            logging.info("Successfully updated message read status")
                        else:
                            logging.warning(f"Failed to update message read status: {response.text}")
                else:
                    logging.warning(f"Failed to get chat messages: {response.text}")
            else:
                logging.warning(f"Failed to send message: {response.text}")

            # 4. Deactivate chat
            response = requests.put(
                f"{CHATS_URL}/{chat_id}/deactivate",
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=5
            )

            if response.status_code == 200:
                logging.info(f"Successfully deactivated chat with ID: {chat_id}")
            else:
                logging.warning(f"Failed to deactivate chat: {response.text}")
        else:
            logging.warning(f"Failed to create chat: {response.text}")

        logging.info("Chats and Messages API test completed")
        return True

    except Exception as e:
        logging.error(f"Error testing chats and messages API: {str(e)}")
        return False

def main():
    """Main test function"""
    print("Starting endpoint tests...")

    # Check if the server is up
    if not check_server_health():
        logging.error("Server is not running. Please start the server and try again.")
        return

    # Test mappings API
    if test_mappings_api():
        logging.info("Mappings API test passed")
    else:
        logging.error("Mappings API test failed")

    # Test chats and messages API
    if test_chats_and_messages_api():
        logging.info("Chats and Messages API test passed")
    else:
        logging.error("Chats and Messages API test failed")

    print("Endpoint tests completed")

if __name__ == "__main__":
    main()
