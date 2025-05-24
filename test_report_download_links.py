#!/usr/bin/env python3
"""
Test script to verify report download links
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
    content = b"This is a test report document for testing download links."
    return io.BytesIO(content)

def create_report_with_document(token: str, patient_id: str):
    """Create a report with a document and verify download links"""
    print("\n=== Testing Report with Document Download Links ===")

    headers = {"Authorization": f"Bearer {token}"}

    # First, upload a document
    files = {"file": ("report_doc.txt", create_test_file(), "text/plain")}
    data = {"document_type": "report", "remark": "Report document"}

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

    # Create report with document
    report_data = {
        "patient_id": patient_id,
        "title": "Test Report",
        "description": "This is a test report for download link testing.",
        "report_type": "lab_test",
        "document_ids": [document_id]
    }

    response = requests.post(
        f"{BASE_URL}/patients/{patient_id}/reports",
        headers=headers,
        json=report_data
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✓ Report created successfully")

        # Check if report_documents have download_link
        if "report_documents" in result:
            report_documents = result["report_documents"]
            if report_documents:
                for doc in report_documents:
                    if "download_link" in doc:
                        print(f"✓ Download link present in report document: {doc['download_link']}")
                        print(f"  File name: {doc.get('file_name', 'unknown')}")
                        print(f"  Document ID: {doc.get('id', 'unknown')}")
                        return result["id"]  # Return report ID
                    else:
                        print(f"✗ Download link missing in report document: {doc.get('file_name', 'unknown')}")
                        print(f"  Document data: {json.dumps(doc, indent=2)}")
            else:
                print("ℹ No report documents in report")
        else:
            print("✗ No report_documents field in report response")
            print(f"Response: {json.dumps(result, indent=2)}")
    else:
        print(f"✗ Report creation failed: {response.status_code} - {response.text}")

    return None

def get_reports_and_verify_links(token: str, patient_id: str):
    """Get reports and verify download links"""
    print("\n=== Testing Get Reports Download Links ===")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/patients/{patient_id}/reports", headers=headers)

    if response.status_code == 200:
        result = response.json()
        print(f"✓ Reports retrieved successfully")

        # Check if reports have download_link in report_documents
        if "data" in result and "reports" in result["data"]:
            reports = result["data"]["reports"]
            if reports:
                for report in reports:
                    if "report_documents" in report and report["report_documents"]:
                        for doc in report["report_documents"]:
                            if "download_link" in doc:
                                print(f"✓ Download link present in retrieved report document: {doc['download_link']}")
                                print(f"  File name: {doc.get('file_name', 'unknown')}")
                            else:
                                print(f"✗ Download link missing in retrieved report document: {doc.get('file_name', 'unknown')}")
                    else:
                        print(f"ℹ No report documents in report: {report.get('title', 'unknown')}")
            else:
                print("ℹ No reports found")
        else:
            print("✗ No reports field in response")
    else:
        print(f"✗ Reports retrieval failed: {response.status_code} - {response.text}")

def main():
    print("=== Testing Report Download Links ===\n")

    # Login as admin
    print("Logging in as admin...")
    admin_token = login("admin@example.com", "admin123")
    if not admin_token:
        print("Failed to login as admin")
        return

    # Use Alice Smith's patient ID from test data
    patient_id = "8118bf07-71f2-4c06-8cb0-c003a20c7e91"  # Alice Smith

    # Test 1: Create report with document
    report_id = create_report_with_document(admin_token, patient_id)

    # Test 2: Get reports and verify links
    get_reports_and_verify_links(admin_token, patient_id)

    print("\n=== Report Download Links Testing Complete ===")

if __name__ == "__main__":
    main()
