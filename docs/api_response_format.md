# API Response Format

## Standard Response Format

All API responses in the POCA Service follow a standardized format:

```json
{
  "status_code": int,
  "status": bool,
  "message": string,
  "data": any
}
```

### Fields

- `status_code`: HTTP status code (e.g., 200, 201, 400, 401, 403, 404, 500)
- `status`: Boolean indicating success (`true`) or failure (`false`)
- `message`: Human-readable message about the response
- `data`: The actual response data, which can be any valid JSON value (object, array, string, number, boolean, or null)

## Success Response Examples

### Example 1: Login Response

```json
{
  "status_code": 200,
  "status": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user_id": "72530021-8af3-43cc-bc26-38255c6ed17d",
    "role": "admin"
  }
}
```

### Example 2: Get User Profile Response

```json
{
  "status_code": 200,
  "status": true,
  "message": "successful",
  "data": {
    "id": "72530021-8af3-43cc-bc26-38255c6ed17d",
    "name": "Admin User",
    "email": "admin@example.com",
    "role": "admin",
    "contact": "+1234567890",
    "address": "123 Admin St, Adminville, USA",
    "created_at": "2023-05-01T12:00:00Z",
    "updated_at": "2023-05-01T12:00:00Z"
  }
}
```

### Example 3: Document Upload Response

```json
{
  "status_code": 200,
  "status": true,
  "message": "Request successful",
  "data": {
    "id": "f27ea191-7277-4453-8cf3-2d43172c4ae0",
    "file_name": "test_document.pdf",
    "size": 1024,
    "link": "http://localhost:8000/api/v1/documents/f27ea191-7277-4453-8cf3-2d43172c4ae0/download",
    "document_type": "other",
    "uploaded_by": "72530021-8af3-43cc-bc26-38255c6ed17d",
    "uploaded_by_role": "admin",
    "remark": "Test document",
    "entity_id": null,
    "upload_timestamp": "2023-05-01T12:00:00Z",
    "created_at": "2023-05-01T12:00:00Z",
    "download_link": "http://localhost:8000/api/v1/documents/f27ea191-7277-4453-8cf3-2d43172c4ae0/download"
  }
}
```

### Example 4: Patient Documents List Response

```json
{
  "status_code": 200,
  "status": true,
  "message": "Request successful",
  "data": {
    "documents": [
      {
        "id": "3df79e11-eb4d-482c-bd17-ea415a3fb3a7",
        "file_name": "blood_test_results.pdf",
        "size": 1024,
        "link": "http://localhost:8000/api/v1/documents/3df79e11-eb4d-482c-bd17-ea415a3fb3a7/download",
        "uploaded_by": "doctor",
        "remark": "Regular blood test results",
        "case_history_id": "b673ecfa-b26b-4c99-92b2-59a5404483fe",
        "upload_timestamp": "2023-05-01T12:00:00Z",
        "created_at": "2023-05-01T12:00:00Z",
        "download_link": "http://localhost:8000/api/v1/documents/3df79e11-eb4d-482c-bd17-ea415a3fb3a7/download"
      }
    ],
    "total": 1
  }
}
```

### Example 5: Download Token Creation Response

```json
{
  "status_code": 200,
  "status": true,
  "message": "Request successful",
  "data": {
    "download_token": "b2QWPcshLbb6l3lhvQ9Yfd0mJ8bFYUUAVuXi3xix890",
    "download_url": "http://localhost:8000/api/v1/documents/download-with-token?token=b2QWPcshLbb6l3lhvQ9Yfd0mJ8bFYUUAVuXi3xix890",
    "expires_at": "2023-05-01T13:00:00Z",
    "expires_in_seconds": 3600
  }
}
```

### Example 6: Empty Response (204 No Content)

```json
{
  "status_code": 200,
  "status": true,
  "message": "Operation completed successfully",
  "data": null
}
```

## Error Response Examples

### Example 1: Authentication Error

```json
{
  "status_code": 401,
  "status": false,
  "message": "Incorrect email or password",
  "data": {
    "error_code": "AUTH_001",
    "details": {}
  }
}
```

### Example 2: Resource Not Found

```json
{
  "status_code": 404,
  "status": false,
  "message": "User not found",
  "data": {
    "error_code": "RES_001",
    "details": {}
  }
}
```

### Example 3: Validation Error

```json
{
  "status_code": 422,
  "status": false,
  "message": "Validation error",
  "data": {
    "error_code": "VAL_001",
    "details": {
      "errors": [
        {
          "loc": ["body", "email"],
          "msg": "value is not a valid email address",
          "type": "value_error.email"
        }
      ]
    }
  }
}
```

## Client Implementation

When implementing a client for this API, always check the `status` field to determine if the request was successful. If `status` is `true`, the `data` field contains the response data. If `status` is `false`, the `data` field contains error information.

### Example (JavaScript)

```javascript
async function fetchData(url) {
  try {
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    const result = await response.json();

    if (result.status) {
      // Success case
      return result.data;
    } else {
      // Error case
      console.error(`Error: ${result.message}`);
      console.error(`Error code: ${result.data.error_code}`);
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}
```

### Document Download Implementation

For downloading documents, use the `download_link` field from API responses:

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
    } else {
      throw new Error(`Download failed: ${response.status}`);
    }
  } catch (error) {
    console.error('Download error:', error);
    throw error;
  }
}

// Usage example
async function getPatientDocumentsAndDownload(patientId, token) {
  const result = await fetchData(`/api/v1/patients/${patientId}/documents`);

  for (const doc of result.documents) {
    await downloadDocument(doc.download_link, doc.file_name, token);
  }
}
```

### Browser-Compatible Downloads

For browser downloads without authentication headers, create temporary download tokens:

```javascript
async function createDownloadToken(documentId, token) {
  const response = await fetch(`/api/v1/documents/${documentId}/download-token`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  const result = await response.json();

  if (result.status) {
    return result.data.download_url; // Can be used directly in browser
  } else {
    throw new Error(result.message);
  }
}

// Usage: Create clickable download link
async function createDownloadLink(documentId, filename, token) {
  const downloadUrl = await createDownloadToken(documentId, token);

  const link = document.createElement('a');
  link.href = downloadUrl;
  link.download = filename;
  link.textContent = `Download ${filename}`;

  return link; // Can be added to DOM
}
```

> **Note**: For detailed document download examples and troubleshooting, see the [Document Download Guide](../DOCUMENT_DOWNLOAD_GUIDE.md).
