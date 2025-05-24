# Document Download Guide for POCA Service

## Overview

The POCA service provides secure document download functionality with proper access control. All download links require authentication to ensure only authorized users can access documents.

## Why You Get "Unauthorized" When Clicking Links

When you click on a download link like:
```
http://localhost:8000/api/v1/documents/{document_id}/download
```

You get a **401 Unauthorized** error because:

1. **Download links are protected API endpoints** that require authentication
2. **Browser clicks don't include authentication headers** automatically
3. **Access control is enforced** based on user roles and relationships

## ✅ Correct Ways to Download Documents

### 1. **Programmatic Download (Python/Backend)**

```python
import requests

# Step 1: Login and get token
response = requests.post("http://localhost:8000/api/v1/auth/login", 
                        data={"username": "admin@example.com", "password": "admin123"},
                        headers={"Content-Type": "application/x-www-form-urlencoded"})
token = response.json()["data"]["access_token"]

# Step 2: Download with authentication
headers = {"Authorization": f"Bearer {token}"}
download_response = requests.get(download_link, headers=headers)

# Step 3: Save the file
with open("document.pdf", "wb") as f:
    f.write(download_response.content)
```

### 2. **Frontend JavaScript Download**

```javascript
async function downloadDocument(downloadLink, filename, token) {
    try {
        const response = await fetch(downloadLink, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }
    } catch (error) {
        console.error('Download failed:', error);
    }
}

// Usage
const token = localStorage.getItem('access_token');
downloadDocument(downloadLink, 'document.pdf', token);
```

### 3. **cURL Command Line**

```bash
# Get token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin@example.com&password=admin123" | \
    jq -r '.data.access_token')

# Download document
curl -H "Authorization: Bearer $TOKEN" \
     -o "document.pdf" \
     "http://localhost:8000/api/v1/documents/{document_id}/download"
```

### 4. **React Component Example**

```jsx
import React, { useState } from 'react';

function DocumentDownloadButton({ document, token }) {
    const [downloading, setDownloading] = useState(false);
    
    const handleDownload = async () => {
        setDownloading(true);
        try {
            const response = await fetch(document.download_link, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = document.file_name;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            }
        } catch (error) {
            console.error('Download failed:', error);
        } finally {
            setDownloading(false);
        }
    };
    
    return (
        <button onClick={handleDownload} disabled={downloading}>
            {downloading ? 'Downloading...' : 'Download'}
        </button>
    );
}
```

## 📋 API Endpoints That Include Download Links

All these APIs now include `download_link` fields in their responses:

### 1. **Document Upload**
```
POST /api/v1/documents/upload
```
Response includes `download_link` field.

### 2. **Document Get**
```
GET /api/v1/documents/{document_id}
```
Response includes `download_link` field.

### 3. **Patient Documents**
```
GET /api/v1/patients/{patient_id}/documents
```
Each document in the response includes `download_link` field.

### 4. **Case History**
```
GET /api/v1/patients/{patient_id}/case-history
```
Each document in `document_files` includes `download_link` field.

### 5. **Reports**
```
GET /api/v1/patients/{patient_id}/reports
```
Each document in `report_documents` includes `download_link` field.

### 6. **Chat Messages**
```
GET /api/v1/chats/{chat_id}/messages
```
Messages with attachments include `download_link` in `file_details`.

## 🔒 Access Control Rules

Documents can be accessed by:

1. **Admin users**: Can access any document
2. **Document uploaders**: Can access documents they uploaded
3. **Patients**: Can access documents uploaded by their treating doctors
4. **Doctors**: Can access documents uploaded by their patients and colleague doctors treating the same patients
5. **Relationship-based access**: Uses doctor-patient mappings to determine permissions

## 🌐 Frontend Integration Best Practices

### 1. **Store Token Securely**
```javascript
// Store token after login
localStorage.setItem('access_token', token);

// Use token for downloads
const token = localStorage.getItem('access_token');
```

### 2. **Handle Download Errors**
```javascript
async function downloadWithErrorHandling(downloadLink, filename, token) {
    try {
        const response = await fetch(downloadLink, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                // Token expired, redirect to login
                window.location.href = '/login';
                return;
            }
            throw new Error(`Download failed: ${response.status}`);
        }
        
        // Process successful download...
    } catch (error) {
        console.error('Download error:', error);
        alert('Download failed. Please try again.');
    }
}
```

### 3. **Progress Tracking**
```javascript
async function downloadWithProgress(downloadLink, filename, token, onProgress) {
    const response = await fetch(downloadLink, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    
    const contentLength = response.headers.get('content-length');
    const total = parseInt(contentLength, 10);
    let loaded = 0;
    
    const reader = response.body.getReader();
    const chunks = [];
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        chunks.push(value);
        loaded += value.length;
        onProgress(loaded, total);
    }
    
    const blob = new Blob(chunks);
    // Create download link...
}
```

## 🚀 Quick Start Examples

### Get Patient Documents and Download All
```javascript
async function downloadAllPatientDocuments(patientId, token) {
    // Get patient documents
    const response = await fetch(`/api/v1/patients/${patientId}/documents`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    
    const result = await response.json();
    const documents = result.data.documents;
    
    // Download each document
    for (const doc of documents) {
        await downloadDocument(doc.download_link, doc.file_name, token);
    }
}
```

### Download Chat Attachments
```javascript
async function downloadChatAttachments(chatId, token) {
    const response = await fetch(`/api/v1/chats/${chatId}/messages`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    
    const result = await response.json();
    const messages = result.data.messages;
    
    for (const message of messages) {
        if (message.file_details && message.file_details.download_link) {
            await downloadDocument(
                message.file_details.download_link,
                message.file_details.file_name,
                token
            );
        }
    }
}
```

## 🔧 Troubleshooting

### Common Issues and Solutions

1. **401 Unauthorized**
   - **Cause**: Missing or invalid authentication token
   - **Solution**: Ensure you're including the `Authorization: Bearer {token}` header

2. **403 Forbidden**
   - **Cause**: User doesn't have permission to access the document
   - **Solution**: Check user roles and document access permissions

3. **404 Not Found**
   - **Cause**: Document doesn't exist or has been deleted
   - **Solution**: Verify the document ID is correct

4. **CORS Issues**
   - **Cause**: Cross-origin request blocked
   - **Solution**: Ensure your frontend domain is in the allowed origins

## 📝 Summary

- ✅ **Download links require authentication** for security
- ✅ **Use Authorization headers** in all download requests
- ✅ **Frontend apps should use fetch/XMLHttpRequest** with proper headers
- ✅ **All document APIs include download_link fields** for convenience
- ✅ **Access control is enforced** based on user roles and relationships
- ✅ **Multiple integration examples provided** for different frameworks

The download system is designed to be secure while providing flexibility for different types of applications and use cases.
