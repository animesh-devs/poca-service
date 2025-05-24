#!/usr/bin/env python3
"""
Test script to demonstrate how to download documents using the download links
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

def upload_test_document(token: str) -> str:
    """Upload a test document and return its ID"""
    print("Uploading test document...")
    
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": ("test_download.txt", io.BytesIO(b"This is a test document for download testing."), "text/plain")}
    data = {"document_type": "other", "remark": "Test document for download"}
    
    response = requests.post(f"{BASE_URL}/documents/upload", headers=headers, files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        document_id = result["data"]["id"]
        download_link = result["data"]["download_link"]
        print(f"✓ Document uploaded successfully")
        print(f"  Document ID: {document_id}")
        print(f"  Download Link: {download_link}")
        return document_id, download_link
    else:
        print(f"✗ Document upload failed: {response.status_code} - {response.text}")
        return None, None

def download_document_correctly(token: str, download_link: str, document_id: str):
    """Demonstrate the correct way to download a document"""
    print(f"\n=== Downloading Document Correctly ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Method 1: Use the download link directly with authentication
    print(f"Downloading from: {download_link}")
    response = requests.get(download_link, headers=headers)
    
    if response.status_code == 200:
        print(f"✓ Document downloaded successfully!")
        print(f"  Content-Type: {response.headers.get('content-type', 'unknown')}")
        print(f"  Content-Length: {response.headers.get('content-length', 'unknown')} bytes")
        print(f"  Content-Disposition: {response.headers.get('content-disposition', 'not set')}")
        print(f"  Content Preview: {response.content[:50]}...")
        
        # Save the file
        filename = f"downloaded_{document_id}.txt"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"  File saved as: {filename}")
        
    else:
        print(f"✗ Download failed: {response.status_code} - {response.text}")

def download_document_incorrectly(download_link: str):
    """Demonstrate what happens when you don't include authentication"""
    print(f"\n=== Downloading Document Without Authentication (Will Fail) ===")
    
    # This will fail because no Authorization header is provided
    response = requests.get(download_link)
    
    if response.status_code == 401:
        print(f"✗ Expected failure: {response.status_code} - Unauthorized")
        print(f"  This is what happens when you click the link without authentication")
    else:
        print(f"Unexpected response: {response.status_code} - {response.text}")

def get_patient_documents_and_download(token: str, patient_id: str):
    """Get patient documents and download them"""
    print(f"\n=== Getting Patient Documents and Downloading ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/patients/{patient_id}/documents", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        documents = result["data"]["documents"]
        
        print(f"✓ Found {len(documents)} documents for patient")
        
        for i, doc in enumerate(documents, 1):
            print(f"\nDocument {i}:")
            print(f"  File Name: {doc['file_name']}")
            print(f"  Download Link: {doc['download_link']}")
            
            # Download the document
            download_response = requests.get(doc['download_link'], headers=headers)
            if download_response.status_code == 200:
                print(f"  ✓ Downloaded successfully ({len(download_response.content)} bytes)")
                
                # Save with original filename
                safe_filename = f"patient_doc_{i}_{doc['file_name']}"
                with open(safe_filename, 'wb') as f:
                    f.write(download_response.content)
                print(f"  ✓ Saved as: {safe_filename}")
            else:
                print(f"  ✗ Download failed: {download_response.status_code}")
    else:
        print(f"✗ Failed to get patient documents: {response.status_code} - {response.text}")

def demonstrate_browser_download_method(token: str, download_link: str):
    """Show how to create a browser-downloadable URL"""
    print(f"\n=== Browser Download Method ===")
    
    # For browser downloads, you would need to either:
    # 1. Use a frontend that adds the Authorization header
    # 2. Use a temporary download token
    # 3. Use a session-based authentication
    
    print("For browser downloads, you have several options:")
    print("1. Use JavaScript fetch() with Authorization header:")
    print(f"""
    fetch('{download_link}', {{
        headers: {{
            'Authorization': 'Bearer {token[:20]}...'
        }}
    }})
    .then(response => response.blob())
    .then(blob => {{
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'document.txt';
        a.click();
    }});
    """)
    
    print("\n2. Create a download endpoint that accepts tokens in query params (less secure)")
    print("\n3. Use session-based authentication instead of Bearer tokens")

def main():
    print("=== Document Download Testing ===\n")
    
    # Login as admin
    print("Logging in as admin...")
    admin_token = login("admin@example.com", "admin123")
    if not admin_token:
        print("Failed to login as admin")
        return
    
    # Upload a test document
    document_id, download_link = upload_test_document(admin_token)
    if not document_id:
        print("Failed to upload test document")
        return
    
    # Demonstrate correct download method
    download_document_correctly(admin_token, download_link, document_id)
    
    # Demonstrate incorrect download method (what happens when you click the link)
    download_document_incorrectly(download_link)
    
    # Get patient documents and download them
    patient_id = "2dd7955d-0218-4b08-879a-de40b4e8aea9"  # Alice Smith
    get_patient_documents_and_download(admin_token, patient_id)
    
    # Show browser download methods
    demonstrate_browser_download_method(admin_token, download_link)
    
    print("\n=== Document Download Testing Complete ===")

if __name__ == "__main__":
    main()
