#!/usr/bin/env python3
"""
Test script to verify that all APIs return responses in the standardized format
"""
import requests
import json
import io
import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

BASE_URL = "http://localhost:8000/api/v1"

def login(email: str, password: str) -> str:
    """Login and return access token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if response.status_code == 200:
        data = response.json()
        if "data" in data and "access_token" in data["data"]:
            return data["data"]["access_token"]
        elif "access_token" in data:
            return data["access_token"]
    print(f"Login failed: {response.status_code} - {response.text}")
    return None

def check_standardized_format(response_data: dict, endpoint: str) -> bool:
    """Check if response follows the standardized format"""
    required_fields = ["status_code", "status", "message", "data"]

    if not all(field in response_data for field in required_fields):
        print(f"✗ {endpoint}: Missing required fields. Got: {list(response_data.keys())}")
        return False

    if not isinstance(response_data["status_code"], int):
        print(f"✗ {endpoint}: status_code should be int, got {type(response_data['status_code'])}")
        return False

    if not isinstance(response_data["status"], bool):
        print(f"✗ {endpoint}: status should be bool, got {type(response_data['status'])}")
        return False

    if not isinstance(response_data["message"], str):
        print(f"✗ {endpoint}: message should be str, got {type(response_data['message'])}")
        return False

    print(f"✓ {endpoint}: Standardized format correct")
    return True

def test_patients_documents_api(token: str, patient_id: str):
    """Test the patients documents API that was specifically mentioned"""
    print("\n=== Testing Patients Documents API ===")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/patients/{patient_id}/documents", headers=headers)

    if response.status_code == 200:
        result = response.json()
        if check_standardized_format(result, f"GET /patients/{patient_id}/documents"):
            # Check if data contains documents and total
            if "documents" in result["data"] and "total" in result["data"]:
                print(f"✓ Response data structure correct: documents={len(result['data']['documents'])}, total={result['data']['total']}")
            else:
                print(f"✗ Response data missing expected fields: {list(result['data'].keys())}")
        return True
    else:
        print(f"✗ GET /patients/{patient_id}/documents failed: {response.status_code} - {response.text}")
        return False

def test_chats_api(token: str):
    """Test chats API endpoints"""
    print("\n=== Testing Chats API ===")

    headers = {"Authorization": f"Bearer {token}", "user-entity-id": "admin"}

    # Test GET /chats
    response = requests.get(f"{BASE_URL}/chats", headers=headers)
    if response.status_code == 200:
        result = response.json()
        check_standardized_format(result, "GET /chats")
    else:
        print(f"✗ GET /chats failed: {response.status_code} - {response.text}")

def test_messages_api(token: str, chat_id: str):
    """Test messages API endpoints"""
    print("\n=== Testing Messages API ===")

    headers = {"Authorization": f"Bearer {token}", "user-entity-id": "admin"}

    # Test GET /messages/chat/{chat_id}
    response = requests.get(f"{BASE_URL}/messages/chat/{chat_id}", headers=headers)
    if response.status_code == 200:
        result = response.json()
        check_standardized_format(result, f"GET /messages/chat/{chat_id}")
    else:
        print(f"✗ GET /messages/chat/{chat_id} failed: {response.status_code} - {response.text}")

def test_users_api(token: str):
    """Test users API endpoints"""
    print("\n=== Testing Users API ===")

    headers = {"Authorization": f"Bearer {token}"}

    # Test GET /users/me
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    if response.status_code == 200:
        result = response.json()
        check_standardized_format(result, "GET /users/me")
    else:
        print(f"✗ GET /users/me failed: {response.status_code} - {response.text}")

    # Test GET /users
    response = requests.get(f"{BASE_URL}/users", headers=headers)
    if response.status_code == 200:
        result = response.json()
        check_standardized_format(result, "GET /users")
    else:
        print(f"✗ GET /users failed: {response.status_code} - {response.text}")

def test_documents_api(token: str):
    """Test documents API endpoints"""
    print("\n=== Testing Documents API ===")

    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": ("test_doc.txt", io.BytesIO(b"Test content"), "text/plain")}
    data = {"document_type": "other", "remark": "Test document"}

    # Test POST /documents/upload
    response = requests.post(f"{BASE_URL}/documents/upload", headers=headers, files=files, data=data)
    if response.status_code == 200:
        result = response.json()
        if check_standardized_format(result, "POST /documents/upload"):
            document_id = result["data"]["id"]

            # Test GET /documents/{document_id}
            response = requests.get(f"{BASE_URL}/documents/{document_id}", headers=headers)
            if response.status_code == 200:
                result = response.json()
                check_standardized_format(result, f"GET /documents/{document_id}")
            else:
                print(f"✗ GET /documents/{document_id} failed: {response.status_code} - {response.text}")
    else:
        print(f"✗ POST /documents/upload failed: {response.status_code} - {response.text}")

def test_auth_api():
    """Test auth API endpoints"""
    print("\n=== Testing Auth API ===")

    # Test login
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "admin@example.com", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if response.status_code == 200:
        result = response.json()
        check_standardized_format(result, "POST /auth/login")
    else:
        print(f"✗ POST /auth/login failed: {response.status_code} - {response.text}")

def main():
    print("=== Testing Standardized Response Format for All APIs ===\n")

    # Test auth API first
    test_auth_api()

    # Login as admin
    print("\nLogging in as admin...")
    admin_token = login("admin@example.com", "admin123")
    if not admin_token:
        print("Failed to login as admin")
        return

    # Test various APIs
    test_users_api(admin_token)
    test_documents_api(admin_token)
    test_chats_api(admin_token)

    # Use test data IDs
    patient_id = "2dd7955d-0218-4b08-879a-de40b4e8aea9"  # Alice Smith
    chat_id = "6d31f146-3c76-437e-832f-4bd0f55981c6"    # Chat between Dr. John Smith and Alice Smith

    # Test specific APIs mentioned in the issue
    test_patients_documents_api(admin_token, patient_id)
    test_messages_api(admin_token, chat_id)

    print("\n=== Standardized Response Format Testing Complete ===")

if __name__ == "__main__":
    main()
