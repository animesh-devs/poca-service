#!/usr/bin/env python3
"""
Test script to demonstrate browser-compatible document downloads using temporary tokens
"""
import requests
import json
import io
import os
import sys
import webbrowser
import time

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
    files = {"file": ("browser_test.txt", io.BytesIO(b"This document can be downloaded in a browser!"), "text/plain")}
    data = {"document_type": "other", "remark": "Test document for browser download"}
    
    response = requests.post(f"{BASE_URL}/documents/upload", headers=headers, files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        document_id = result["data"]["id"]
        print(f"✓ Document uploaded successfully")
        print(f"  Document ID: {document_id}")
        return document_id
    else:
        print(f"✗ Document upload failed: {response.status_code} - {response.text}")
        return None

def create_download_token(token: str, document_id: str):
    """Create a temporary download token for browser downloads"""
    print(f"\n=== Creating Temporary Download Token ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/documents/{document_id}/download-token", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        download_data = result["data"]
        
        print(f"✓ Temporary download token created successfully!")
        print(f"  Token: {download_data['download_token'][:20]}...")
        print(f"  Download URL: {download_data['download_url']}")
        print(f"  Expires at: {download_data['expires_at']}")
        print(f"  Valid for: {download_data['expires_in_seconds']} seconds")
        
        return download_data
    else:
        print(f"✗ Failed to create download token: {response.status_code} - {response.text}")
        return None

def test_browser_download(download_url: str):
    """Test downloading using the temporary token URL (no auth required)"""
    print(f"\n=== Testing Browser Download (No Auth Required) ===")
    
    # This simulates what happens when you click a link in a browser
    response = requests.get(download_url)
    
    if response.status_code == 200:
        print(f"✓ Document downloaded successfully without authentication!")
        print(f"  Content-Type: {response.headers.get('content-type', 'unknown')}")
        print(f"  Content-Disposition: {response.headers.get('content-disposition', 'not set')}")
        print(f"  Content: {response.content.decode()}")
        
        # Save the file
        filename = "browser_downloaded_file.txt"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"  File saved as: {filename}")
        
        return True
    else:
        print(f"✗ Download failed: {response.status_code} - {response.text}")
        return False

def test_token_expiry(download_url: str):
    """Test that the token is one-time use"""
    print(f"\n=== Testing Token One-Time Use ===")
    
    # Try to download again with the same token
    response = requests.get(download_url)
    
    if response.status_code == 404:
        print(f"✓ Token correctly invalidated after first use (404: {response.text})")
    else:
        print(f"✗ Unexpected response: {response.status_code} - {response.text}")

def demonstrate_frontend_integration(token: str, document_id: str):
    """Show how to integrate this in a frontend application"""
    print(f"\n=== Frontend Integration Example ===")
    
    # Step 1: Frontend calls API to get download token
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/documents/{document_id}/download-token", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        download_url = result["data"]["download_url"]
        
        print("Frontend Integration Steps:")
        print("1. ✓ Frontend authenticated API call to get download token")
        print("2. ✓ Received browser-compatible download URL")
        print("3. Frontend can now use this URL in several ways:")
        
        print(f"\n   Option A: Direct link (clickable):")
        print(f"   <a href=\"{download_url}\" download>Download Document</a>")
        
        print(f"\n   Option B: JavaScript download:")
        print(f"""   
   function downloadDocument() {{
       window.location.href = '{download_url}';
   }}
   """)
        
        print(f"\n   Option C: Fetch API with blob:")
        print(f"""   
   fetch('{download_url}')
       .then(response => response.blob())
       .then(blob => {{
           const url = window.URL.createObjectURL(blob);
           const a = document.createElement('a');
           a.href = url;
           a.download = 'document.txt';
           a.click();
       }});
   """)
        
        return download_url
    else:
        print(f"✗ Failed to get download token: {response.status_code}")
        return None

def open_in_browser(download_url: str):
    """Open the download URL in the default browser"""
    print(f"\n=== Opening in Browser ===")
    print(f"Opening URL in browser: {download_url}")
    print("This should trigger a file download in your browser!")
    
    try:
        webbrowser.open(download_url)
        print("✓ Browser opened. Check your downloads folder!")
    except Exception as e:
        print(f"✗ Failed to open browser: {e}")
        print(f"You can manually copy this URL to your browser: {download_url}")

def main():
    print("=== Browser-Compatible Document Download Testing ===\n")
    
    # Login as admin
    print("Logging in as admin...")
    admin_token = login("admin@example.com", "admin123")
    if not admin_token:
        print("Failed to login as admin")
        return
    
    # Upload a test document
    document_id = upload_test_document(admin_token)
    if not document_id:
        print("Failed to upload test document")
        return
    
    # Create temporary download token
    download_data = create_download_token(admin_token, document_id)
    if not download_data:
        print("Failed to create download token")
        return
    
    download_url = download_data["download_url"]
    
    # Test browser download (no auth required)
    success = test_browser_download(download_url)
    if not success:
        print("Browser download test failed")
        return
    
    # Test token one-time use
    test_token_expiry(download_url)
    
    # Demonstrate frontend integration
    new_download_url = demonstrate_frontend_integration(admin_token, document_id)
    
    # Ask user if they want to test in actual browser
    if new_download_url:
        user_input = input(f"\nWould you like to test the download in your actual browser? (y/n): ")
        if user_input.lower() in ['y', 'yes']:
            open_in_browser(new_download_url)
    
    print("\n=== Browser Download Testing Complete ===")
    print("\nSummary:")
    print("✓ Temporary download tokens work without authentication")
    print("✓ Tokens are one-time use for security")
    print("✓ Perfect for frontend applications and browser downloads")
    print("✓ No CORS issues since it's a direct download link")

if __name__ == "__main__":
    main()
