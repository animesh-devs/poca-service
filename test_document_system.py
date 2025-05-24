#!/usr/bin/env python3
"""
Test script for the in-memory document storage system
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
    content = b"This is a test document for the POCA service document storage system.\nIt contains some sample text to test file upload and download functionality."
    return io.BytesIO(content)

def upload_document(token: str, file_content: io.BytesIO, filename: str = "test_document.txt") -> dict:
    """Upload a document"""
    headers = {"Authorization": f"Bearer {token}"}

    files = {
        "file": (filename, file_content, "text/plain")
    }
    data = {
        "document_type": "other",
        "remark": "Test document upload"
    }

    response = requests.post(
        f"{BASE_URL}/documents/upload",
        headers=headers,
        files=files,
        data=data
    )

    print(f"Upload response: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Upload successful: {json.dumps(result, indent=2)}")
        return result
    else:
        print(f"Upload failed: {response.text}")
        return None

def get_document_metadata(token: str, document_id: str) -> dict:
    """Get document metadata"""
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{BASE_URL}/documents/{document_id}",
        headers=headers
    )

    print(f"Get metadata response: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Metadata: {json.dumps(result, indent=2)}")
        return result
    else:
        print(f"Get metadata failed: {response.text}")
        return None

def download_document(token: str, document_id: str) -> bytes:
    """Download a document"""
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{BASE_URL}/documents/{document_id}/download",
        headers=headers
    )

    print(f"Download response: {response.status_code}")
    if response.status_code == 200:
        print(f"Downloaded {len(response.content)} bytes")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Content-Disposition: {response.headers.get('content-disposition')}")
        print(f"Content preview: {response.content[:100]}...")
        return response.content
    else:
        print(f"Download failed: {response.text}")
        return None

def test_access_control(uploader_token: str, other_token: str, document_id: str):
    """Test access control between different users"""
    print("\n=== Testing Access Control ===")

    # Test that uploader can access
    print("Testing uploader access...")
    metadata = get_document_metadata(uploader_token, document_id)
    if metadata:
        print("✓ Uploader can access document metadata")

    content = download_document(uploader_token, document_id)
    if content:
        print("✓ Uploader can download document")

    # Test that other user cannot access (unless they have permission)
    print("\nTesting other user access...")
    metadata = get_document_metadata(other_token, document_id)
    content = download_document(other_token, document_id)

def get_storage_stats(token: str) -> dict:
    """Get storage statistics (admin only)"""
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{BASE_URL}/documents/storage/stats",
        headers=headers
    )

    print(f"Storage stats response: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Storage stats: {json.dumps(result, indent=2)}")
        return result
    else:
        print(f"Storage stats failed: {response.text}")
        return None

def main():
    print("=== Testing Document Storage System ===\n")

    # Login as admin
    print("Logging in as admin...")
    admin_token = login("admin@example.com", "admin123")
    if not admin_token:
        print("Failed to login as admin")
        return

    # Login as a patient
    print("Logging in as patient...")
    patient_token = login("patient1@example.com", "patient1")
    if not patient_token:
        print("Failed to login as patient")
        return

    # Test 1: Upload a document as admin
    print("\n=== Test 1: Upload Document as Admin ===")
    test_file = create_test_file()
    upload_result = upload_document(admin_token, test_file, "admin_test_document.txt")

    if not upload_result:
        print("Upload failed, stopping tests")
        return

    document_id = upload_result["data"]["id"] if "data" in upload_result else upload_result["id"]
    print(f"Document ID: {document_id}")

    # Test 2: Get document metadata
    print("\n=== Test 2: Get Document Metadata ===")
    get_document_metadata(admin_token, document_id)

    # Test 3: Download document
    print("\n=== Test 3: Download Document ===")
    download_document(admin_token, document_id)

    # Test 4: Access control
    test_access_control(admin_token, patient_token, document_id)

    # Test 5: Upload as patient
    print("\n=== Test 5: Upload Document as Patient ===")
    test_file2 = create_test_file()
    patient_upload_result = upload_document(patient_token, test_file2, "patient_test_document.txt")

    if patient_upload_result:
        patient_document_id = patient_upload_result["data"]["id"] if "data" in patient_upload_result else patient_upload_result["id"]
        print(f"Patient Document ID: {patient_document_id}")

        # Test access control for patient document
        test_access_control(patient_token, admin_token, patient_document_id)

    # Test 6: Storage statistics (admin only)
    print("\n=== Test 6: Storage Statistics ===")
    get_storage_stats(admin_token)

    print("\n=== Document Storage System Tests Complete ===")

if __name__ == "__main__":
    main()
