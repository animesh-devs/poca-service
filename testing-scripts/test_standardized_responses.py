#!/usr/bin/env python3
"""
Test Standardized Responses

This script tests the standardized response format by making requests to various API endpoints
and verifying that the responses are in the standardized format.

Note: We're using a decorator approach instead of middleware for standardizing responses.
See app/utils/decorators.py for the implementation.
"""

import sys
import logging
import requests
import json
from typing import Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# API URLs
BASE_URL = "http://localhost:8000"
API_V1_PREFIX = "/api/v1"
AUTH_URL = f"{BASE_URL}{API_V1_PREFIX}/auth"
USERS_URL = f"{BASE_URL}{API_V1_PREFIX}/users"
HEALTH_URL = f"{BASE_URL}/health"
ROOT_URL = f"{BASE_URL}/"

# Test credentials
DEFAULT_ADMIN_EMAIL = "admin@example.com"
DEFAULT_ADMIN_PASSWORD = "admin123"

def check_standardized_response(response_json: Dict) -> bool:
    """
    Check if a response is in the standardized format.

    Args:
        response_json: The JSON response to check

    Returns:
        True if the response is in the standardized format, False otherwise
    """
    required_fields = ["status_code", "status", "message", "data"]

    if not isinstance(response_json, dict):
        logging.error(f"Response is not a dictionary: {response_json}")
        return False

    for field in required_fields:
        if field not in response_json:
            logging.error(f"Response is missing required field: {field}")
            return False

    # Check that status is a boolean
    if not isinstance(response_json["status"], bool):
        logging.error(f"Status field is not a boolean: {response_json['status']}")
        return False

    # Check that status_code is an integer
    if not isinstance(response_json["status_code"], int):
        logging.error(f"Status code field is not an integer: {response_json['status_code']}")
        return False

    # Check that message is a string
    if not isinstance(response_json["message"], str):
        logging.error(f"Message field is not a string: {response_json['message']}")
        return False

    return True

def test_endpoint(url: str, method: str = "GET", token: Optional[str] = None,
                 data: Optional[Dict] = None, expected_status: int = 200) -> bool:
    """
    Test an endpoint and verify that the response is in the standardized format.

    Args:
        url: The URL to test
        method: The HTTP method to use
        token: The authentication token to use
        data: The request data to send
        expected_status: The expected HTTP status code

    Returns:
        True if the test passed, False otherwise
    """
    logging.info(f"Testing {method} {url}")

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            logging.error(f"Unsupported method: {method}")
            return False

        if response.status_code != expected_status:
            logging.error(f"Unexpected status code: {response.status_code}, expected: {expected_status}")
            logging.error(f"Response: {response.text}")
            return False

        try:
            response_json = response.json()

            if check_standardized_response(response_json):
                logging.info(f"Response is in the standardized format: {response_json['message']}")
                return True
            else:
                logging.error(f"Response is not in the standardized format: {response_json}")
                return False
        except json.JSONDecodeError:
            logging.error(f"Response is not valid JSON: {response.text}")
            return False
    except Exception as e:
        logging.error(f"Error testing endpoint: {str(e)}")
        return False

def get_auth_token() -> Optional[str]:
    """
    Get an authentication token for the admin user.

    Returns:
        The authentication token, or None if authentication failed
    """
    logging.info(f"Getting authentication token for {DEFAULT_ADMIN_EMAIL}")

    try:
        response = requests.post(
            f"{AUTH_URL}/login",
            data={"username": DEFAULT_ADMIN_EMAIL, "password": DEFAULT_ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if response.status_code != 200:
            logging.error(f"Authentication failed: {response.text}")
            return None

        response_json = response.json()

        # Check if the response is in the standardized format
        if check_standardized_response(response_json):
            # Extract the token from the data field
            token_data = response_json.get("data", {})
            token = token_data.get("access_token")
            if token:
                logging.info(f"Got authentication token")
                return token
            else:
                logging.error(f"Token not found in response data: {token_data}")
                return None
        else:
            # If not in standardized format, use the response as is
            token = response_json.get("access_token")
            if token:
                logging.info(f"Got authentication token (non-standardized response)")
                return token
            else:
                logging.error(f"Token not found in response: {response_json}")
                return None
    except Exception as e:
        logging.error(f"Error getting authentication token: {str(e)}")
        return None

def main():
    """Main function to run the tests"""
    logging.info("Starting standardized response tests")

    # Test non-authenticated endpoints
    test_endpoint(ROOT_URL)
    test_endpoint(HEALTH_URL)

    # Get authentication token
    token = get_auth_token()
    if not token:
        logging.error("Failed to get authentication token. Aborting.")
        return

    # Test authenticated endpoints
    test_endpoint(f"{USERS_URL}/me", token=token)
    test_endpoint(f"{USERS_URL}", token=token)

    logging.info("Standardized response tests completed")

if __name__ == "__main__":
    main()
