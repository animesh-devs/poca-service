#!/usr/bin/env python3
"""
Examples of how to properly download documents from POCA service
"""
import requests
import json
import io

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
    return None

def download_document_correctly(token, download_link):
    """Correct way to download a document"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(download_link, headers=headers)
    
    if response.status_code == 200:
        # Save the file
        filename = "downloaded_document.txt"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"✓ Document downloaded successfully as {filename}")
        return True
    else:
        print(f"✗ Download failed: {response.status_code} - {response.text}")
        return False

def get_patient_documents_and_download(token, patient_id):
    """Get patient documents and download them"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/patients/{patient_id}/documents", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        documents = result["data"]["documents"]
        
        print(f"Found {len(documents)} documents for patient")
        
        for i, doc in enumerate(documents, 1):
            print(f"\nDocument {i}: {doc['file_name']}")
            print(f"Download Link: {doc['download_link']}")
            
            # Download the document
            download_response = requests.get(doc['download_link'], headers=headers)
            if download_response.status_code == 200:
                filename = f"patient_doc_{i}_{doc['file_name']}"
                with open(filename, 'wb') as f:
                    f.write(download_response.content)
                print(f"✓ Downloaded as: {filename}")
            else:
                print(f"✗ Download failed: {download_response.status_code}")

# Example usage
if __name__ == "__main__":
    token = login_and_get_token()
    if token:
        # Example: Download from a specific link
        download_link = "http://localhost:8000/api/v1/documents/some-document-id/download"
        download_document_correctly(token, download_link)
        
        # Example: Get and download patient documents
        patient_id = "2dd7955d-0218-4b08-879a-de40b4e8aea9"
        get_patient_documents_and_download(token, patient_id)
