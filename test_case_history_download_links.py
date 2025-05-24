#!/usr/bin/env python3
"""
Test script to verify case history download links
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

def create_test_file() -> io.BytesIO:
    """Create a test file in memory"""
    content = b"This is a test case history document for testing download links."
    return io.BytesIO(content)

def create_case_history_with_document(token: str, patient_id: str):
    """Create a case history with a document and verify download links"""
    print("\n=== Testing Case History with Document Download Links ===")

    headers = {"Authorization": f"Bearer {token}"}

    # First, upload a document
    files = {"file": ("case_history_doc.txt", create_test_file(), "text/plain")}
    data = {"document_type": "case_history", "remark": "Case history document"}

    upload_response = requests.post(
        f"{BASE_URL}/documents/upload",
        headers=headers,
        files=files,
        data=data
    )

    if upload_response.status_code != 200:
        print(f"✗ Document upload failed: {upload_response.status_code} - {upload_response.text}")
        return

    document_result = upload_response.json()
    document_id = document_result["data"]["id"]
    print(f"✓ Document uploaded with ID: {document_id}")

    # Create case history with document
    case_history_data = {
        "patient_id": patient_id,
        "summary": "Patient has been experiencing symptoms for the past week.",
        "documents": [document_id]
    }

    response = requests.post(
        f"{BASE_URL}/patients/{patient_id}/case-history",
        headers=headers,
        json=case_history_data
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✓ Case history created successfully")

        # Check if document_files have download_link
        if "data" in result and "document_files" in result["data"]:
            document_files = result["data"]["document_files"]
            if document_files:
                for doc in document_files:
                    if "download_link" in doc:
                        print(f"✓ Download link present in case history document: {doc['download_link']}")
                        print(f"  File name: {doc.get('file_name', 'unknown')}")
                        print(f"  Document ID: {doc.get('id', 'unknown')}")
                    else:
                        print(f"✗ Download link missing in case history document: {doc.get('file_name', 'unknown')}")
                        print(f"  Document data: {json.dumps(doc, indent=2)}")
            else:
                print("ℹ No document files in case history")
        else:
            print("✗ No document_files field in case history response")
            print(f"Response: {json.dumps(result, indent=2)}")
    else:
        print(f"✗ Case history creation failed: {response.status_code} - {response.text}")

def get_case_history_and_verify_links(token: str, patient_id: str):
    """Get case history and verify download links"""
    print("\n=== Testing Get Case History Download Links ===")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/patients/{patient_id}/case-history?create_if_not_exists=true", headers=headers)

    if response.status_code == 200:
        result = response.json()
        print(f"✓ Case history retrieved successfully")

        # Check if document_files have download_link
        if "data" in result and "document_files" in result["data"]:
            document_files = result["data"]["document_files"]
            if document_files:
                for doc in document_files:
                    if "download_link" in doc:
                        print(f"✓ Download link present in retrieved case history document: {doc['download_link']}")
                        print(f"  File name: {doc.get('file_name', 'unknown')}")
                    else:
                        print(f"✗ Download link missing in retrieved case history document: {doc.get('file_name', 'unknown')}")
            else:
                print("ℹ No document files in retrieved case history")
        else:
            print("✗ No document_files field in retrieved case history response")
    else:
        print(f"✗ Case history retrieval failed: {response.status_code} - {response.text}")

def main():
    print("=== Testing Case History Download Links ===\n")

    # Login as admin
    print("Logging in as admin...")
    admin_token = login("admin@example.com", "admin123")
    if not admin_token:
        print("Failed to login as admin")
        return

    # Use Alice Smith's patient ID from test data
    patient_id = "8118bf07-71f2-4c06-8cb0-c003a20c7e91"  # Alice Smith

    # Test 1: Create case history with document
    create_case_history_with_document(admin_token, patient_id)

    # Test 2: Get case history and verify links
    get_case_history_and_verify_links(admin_token, patient_id)

    print("\n=== Case History Download Links Testing Complete ===")

if __name__ == "__main__":
    main()
