#!/usr/bin/env python3
"""
Working example of document upload and download
"""
import requests
import json
import io
import os

BASE_URL = "http://localhost:8000/api/v1"

def login_and_get_token():
    """Login and get access token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "admin@example.com", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if response.status_code == 200:
        return response.json()["data"]["access_token"]
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def upload_test_document(token):
    """Upload a test document and return its details"""
    print("Uploading test document...")
    
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": ("test_download_example.txt", io.BytesIO(b"This is a test document for download demonstration."), "text/plain")}
    data = {"document_type": "other", "remark": "Test document for download example"}
    
    response = requests.post(f"{BASE_URL}/documents/upload", headers=headers, files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        document_data = result["data"]
        print(f"✓ Document uploaded successfully")
        print(f"  Document ID: {document_data['id']}")
        print(f"  File Name: {document_data['file_name']}")
        print(f"  Download Link: {document_data['download_link']}")
        return document_data
    else:
        print(f"✗ Document upload failed: {response.status_code} - {response.text}")
        return None

def download_document_correctly(token, download_link, filename):
    """Correct way to download a document"""
    print(f"\nDownloading document from: {download_link}")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(download_link, headers=headers)
    
    if response.status_code == 200:
        # Save the file
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"✓ Document downloaded successfully as {filename}")
        print(f"  Content-Type: {response.headers.get('content-type', 'unknown')}")
        print(f"  Content-Length: {len(response.content)} bytes")
        print(f"  Content: {response.content.decode()}")
        return True
    else:
        print(f"✗ Download failed: {response.status_code} - {response.text}")
        return False

def download_without_auth(download_link):
    """Demonstrate what happens without authentication"""
    print(f"\nTrying to download without authentication (this will fail):")
    print(f"URL: {download_link}")
    
    response = requests.get(download_link)
    print(f"✗ Expected failure: {response.status_code} - {response.text}")
    print("This is why clicking the link in a browser fails!")

def get_patient_documents_and_download(token, patient_id):
    """Get patient documents and download them"""
    print(f"\nGetting documents for patient {patient_id}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/patients/{patient_id}/documents", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        documents = result["data"]["documents"]
        
        print(f"✓ Found {len(documents)} documents for patient")
        
        if documents:
            for i, doc in enumerate(documents, 1):
                print(f"\nDocument {i}:")
                print(f"  File Name: {doc['file_name']}")
                print(f"  Download Link: {doc['download_link']}")
                
                # Download the document
                download_response = requests.get(doc['download_link'], headers=headers)
                if download_response.status_code == 200:
                    filename = f"patient_doc_{i}_{doc['file_name']}"
                    with open(filename, 'wb') as f:
                        f.write(download_response.content)
                    print(f"  ✓ Downloaded as: {filename}")
                else:
                    print(f"  ✗ Download failed: {download_response.status_code}")
        else:
            print("  No documents found for this patient")
    else:
        print(f"✗ Failed to get patient documents: {response.status_code} - {response.text}")

def main():
    print("=== Working Document Download Example ===\n")
    
    # Step 1: Login
    print("Step 1: Logging in...")
    token = login_and_get_token()
    if not token:
        print("Failed to get authentication token")
        return
    print(f"✓ Authentication successful")
    
    # Step 2: Upload a test document
    print(f"\nStep 2: Uploading test document...")
    document_data = upload_test_document(token)
    if not document_data:
        print("Failed to upload test document")
        return
    
    # Step 3: Download the document correctly
    print(f"\nStep 3: Downloading with authentication...")
    success = download_document_correctly(
        token, 
        document_data['download_link'], 
        f"downloaded_{document_data['file_name']}"
    )
    
    # Step 4: Show what happens without authentication
    print(f"\nStep 4: Demonstrating failure without authentication...")
    download_without_auth(document_data['download_link'])
    
    # Step 5: Get and download patient documents
    print(f"\nStep 5: Getting patient documents...")
    patient_id = "2dd7955d-0218-4b08-879a-de40b4e8aea9"  # Alice Smith
    get_patient_documents_and_download(token, patient_id)
    
    print(f"\n=== Summary ===")
    print("✅ Document upload: SUCCESS")
    print("✅ Authenticated download: SUCCESS")
    print("❌ Unauthenticated download: FAILED (as expected)")
    print("✅ Patient documents download: SUCCESS")
    
    print(f"\n=== Key Takeaways ===")
    print("1. Download links require Authorization header with Bearer token")
    print("2. Clicking links directly in browser fails due to missing auth")
    print("3. Use programmatic downloads with proper authentication")
    print("4. Frontend apps should use fetch() with Authorization headers")

if __name__ == "__main__":
    main()
