#!/bin/bash

# cURL examples for downloading documents from POCA service

BASE_URL="http://localhost:8000/api/v1"

# Function to login and get token
get_token() {
    curl -s -X POST "$BASE_URL/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=admin@example.com&password=admin123" | \
        jq -r '.data.access_token'
}

# Function to download a document
download_document() {
    local token=$1
    local download_link=$2
    local output_filename=$3
    
    echo "Downloading document..."
    curl -H "Authorization: Bearer $token" \
         -o "$output_filename" \
         "$download_link"
    
    if [ $? -eq 0 ]; then
        echo "✓ Document downloaded successfully as $output_filename"
    else
        echo "✗ Download failed"
    fi
}

# Function to get patient documents and download them
download_patient_documents() {
    local token=$1
    local patient_id=$2
    
    echo "Getting patient documents..."
    
    # Get patient documents
    documents=$(curl -s -H "Authorization: Bearer $token" \
                     "$BASE_URL/patients/$patient_id/documents")
    
    # Parse and download each document
    echo "$documents" | jq -r '.data.documents[] | "\(.download_link) \(.file_name)"' | \
    while read -r download_link filename; do
        echo "Downloading: $filename"
        curl -H "Authorization: Bearer $token" \
             -o "patient_$filename" \
             "$download_link"
        
        if [ $? -eq 0 ]; then
            echo "✓ Downloaded: patient_$filename"
        else
            echo "✗ Failed to download: $filename"
        fi
    done
}

# Main execution
echo "=== cURL Document Download Examples ==="

# Get authentication token
echo "Getting authentication token..."
TOKEN=$(get_token)

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "✗ Failed to get authentication token"
    exit 1
fi

echo "✓ Authentication token obtained"

# Example 1: Download a specific document
echo -e "\n=== Example 1: Download specific document ==="
DOCUMENT_ID="your-document-id-here"
DOWNLOAD_LINK="$BASE_URL/documents/$DOCUMENT_ID/download"
download_document "$TOKEN" "$DOWNLOAD_LINK" "downloaded_document.txt"

# Example 2: Download patient documents
echo -e "\n=== Example 2: Download patient documents ==="
PATIENT_ID="2dd7955d-0218-4b08-879a-de40b4e8aea9"  # Alice Smith
download_patient_documents "$TOKEN" "$PATIENT_ID"

# Example 3: Download with verbose output
echo -e "\n=== Example 3: Download with verbose output ==="
curl -v -H "Authorization: Bearer $TOKEN" \
     -o "verbose_download.txt" \
     "$BASE_URL/documents/some-document-id/download"

# Example 4: Check if download link is accessible
echo -e "\n=== Example 4: Check download link accessibility ==="
curl -I -H "Authorization: Bearer $TOKEN" \
     "$BASE_URL/documents/some-document-id/download"

echo -e "\n=== Download examples complete ==="
