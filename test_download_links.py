#!/usr/bin/env python3
"""
Test script to verify that download links are included in all relevant APIs
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
    content = b"This is a test document for testing download links in POCA service."
    return io.BytesIO(content)

def test_document_upload_download_link(token: str) -> str:
    """Test document upload and verify download link"""
    print("\n=== Testing Document Upload Download Link ===")

    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": ("test_doc.txt", create_test_file(), "text/plain")}
    data = {"document_type": "other", "remark": "Test document"}

    response = requests.post(
        f"{BASE_URL}/documents/upload",
        headers=headers,
        files=files,
        data=data
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✓ Document upload successful")

        # Check if download_link is present
        if "data" in result and "download_link" in result["data"]:
            download_link = result["data"]["download_link"]
            print(f"✓ Download link present: {download_link}")
            return result["data"]["id"]
        else:
            print("✗ Download link missing in upload response")
            print(f"Response: {json.dumps(result, indent=2)}")
    else:
        print(f"✗ Document upload failed: {response.status_code} - {response.text}")

    return None

def test_document_get_download_link(token: str, document_id: str):
    """Test document get and verify download link"""
    print("\n=== Testing Document Get Download Link ===")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/documents/{document_id}", headers=headers)

    if response.status_code == 200:
        result = response.json()
        print(f"✓ Document get successful")

        # Check if download_link is present
        if "data" in result and "download_link" in result["data"]:
            download_link = result["data"]["download_link"]
            print(f"✓ Download link present: {download_link}")
        else:
            print("✗ Download link missing in get response")
            print(f"Response: {json.dumps(result, indent=2)}")
    else:
        print(f"✗ Document get failed: {response.status_code} - {response.text}")

def test_case_history_download_links(token: str, patient_id: str):
    """Test case history and verify download links in document_files"""
    print("\n=== Testing Case History Download Links ===")

    headers = {"Authorization": f"Bearer {token}"}

    # Get case history
    response = requests.get(
        f"{BASE_URL}/patients/{patient_id}/case-history",
        headers=headers
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✓ Case history get successful")

        # Check if document_files have download_link
        if "data" in result and "document_files" in result["data"]:
            document_files = result["data"]["document_files"]
            if document_files:
                for doc in document_files:
                    if "download_link" in doc:
                        print(f"✓ Download link present in case history document: {doc['download_link']}")
                    else:
                        print(f"✗ Download link missing in case history document: {doc.get('file_name', 'unknown')}")
            else:
                print("ℹ No document files in case history")
        else:
            print("✗ No document_files field in case history response")
    else:
        print(f"✗ Case history get failed: {response.status_code} - {response.text}")

def test_message_with_attachment_download_link(token: str, chat_id: str, receiver_id: str):
    """Test message with attachment and verify download link in file_details"""
    print("\n=== Testing Message Attachment Download Link ===")

    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": ("message_attachment.txt", create_test_file(), "text/plain")}
    data = {
        "chat_id": chat_id,
        "receiver_id": receiver_id,
        "message": "Here's a test document",
        "message_type": "document"
    }

    response = requests.post(
        f"{BASE_URL}/messages/with-attachment",
        headers=headers,
        files=files,
        data=data
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✓ Message with attachment created successfully")

        # Check if file_details has download_link
        if "file_details" in result and result["file_details"]:
            file_details = result["file_details"]
            if "download_link" in file_details:
                print(f"✓ Download link present in message file_details: {file_details['download_link']}")
            else:
                print(f"✗ Download link missing in message file_details")
                print(f"File details: {json.dumps(file_details, indent=2)}")
        else:
            print("✗ No file_details in message response")
    else:
        print(f"✗ Message with attachment failed: {response.status_code} - {response.text}")

def test_chat_messages_download_links(token: str, chat_id: str):
    """Test chat messages and verify download links in file_details"""
    print("\n=== Testing Chat Messages Download Links ===")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/chats/{chat_id}/messages", headers=headers)

    if response.status_code == 200:
        result = response.json()
        print(f"✓ Chat messages get successful")

        # Check if messages with file_details have download_link
        if "messages" in result:
            messages = result["messages"]
            for message in messages:
                if message.get("file_details"):
                    file_details = message["file_details"]
                    if "download_link" in file_details:
                        print(f"✓ Download link present in chat message file_details: {file_details['download_link']}")
                    else:
                        print(f"✗ Download link missing in chat message file_details")
                        print(f"File details: {json.dumps(file_details, indent=2)}")
        else:
            print("✗ No messages in chat response")
    else:
        print(f"✗ Chat messages get failed: {response.status_code} - {response.text}")

def main():
    print("=== Testing Download Links in All APIs ===\n")

    # Login as admin
    print("Logging in as admin...")
    admin_token = login("admin@example.com", "admin123")
    if not admin_token:
        print("Failed to login as admin")
        return

    # Test 1: Document upload download link
    document_id = test_document_upload_download_link(admin_token)
    if not document_id:
        print("Skipping further tests due to document upload failure")
        return

    # Test 2: Document get download link
    test_document_get_download_link(admin_token, document_id)

    # Test 3: Case history download links
    # Use a patient ID from test data
    patient_id = "8118bf07-71f2-4c06-8cb0-c003a20c7e91"  # Alice Smith
    test_case_history_download_links(admin_token, patient_id)

    # Test 4: Message with attachment download link
    # Use a chat ID from test data
    chat_id = "47d8e6a2-f734-40ff-8b02-3597224432c3"  # Chat between Dr. John Smith and Alice Smith
    receiver_id = "8118bf07-71f2-4c06-8cb0-c003a20c7e91"  # Alice Smith (patient)
    test_message_with_attachment_download_link(admin_token, chat_id, receiver_id)

    # Test 5: Chat messages download links
    test_chat_messages_download_links(admin_token, chat_id)

    print("\n=== Download Links Testing Complete ===")

if __name__ == "__main__":
    main()
